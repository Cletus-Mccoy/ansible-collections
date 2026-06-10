DOCUMENTATION = r'''
---
module: adb_install
short_description: Install an APK on an Android device via ADB
description:
  - Installs an APK on an Android device using ADB.
  - The APK may be a path on the Ansible controller (installed with
    C(adb install)) or a path already present on the device under C(/sdcard) or
    C(/data) (installed with C(adb shell pm install)).
  - Optionally idempotent. If O(package) (and optionally O(version)) is given, the
    module checks the installed version first and reports C(changed=false) when the
    desired version is already present.
options:
  apk_path:
    description:
      - Path to the APK file (on the controller, or on the device for C(/sdcard)/C(/data) paths).
    required: true
    type: str
  package:
    description:
      - Package name of the app. When supplied, enables an idempotency check
        against the currently installed version.
    required: false
    type: str
  version:
    description:
      - Desired C(versionName). When supplied together with O(package), the module
        skips installation if the installed C(versionName) already matches.
        Without O(version), installation is skipped if the package is installed at all.
    required: false
    type: str
  device:
    description:
      - Device serial or C(IP:port) to target.
    required: false
    type: str
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
author:
  - Kasper Daems
version_added: '1.2.0'
'''

EXAMPLES = r'''
- name: Install an APK from the controller
  cletus_mccoy.android_adb.adb_install:
    apk_path: /path/to/app.apk

- name: Install idempotently, skipping if version already present
  cletus_mccoy.android_adb.adb_install:
    apk_path: /path/to/app-2.3.0.apk
    package: com.example.app
    version: "2.3.0"
'''

RETURN = r'''
changed:
  description: Whether the APK was installed.
  type: bool
  returned: always
msg:
  description: Informational message.
  type: str
  returned: always
installed_version:
  description: The versionName that was present before this run (when package is supplied).
  type: str
  returned: when package is supplied
'''

from ansible.module_utils.basic import AnsibleModule
import shutil


def _installed_version(adb_path, package, device):
    """Return the installed versionName, '' if installed without a readable version,
    or None if the package is not installed."""
    from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
    output = adb_shell(adb_path, f"dumpsys package {package}", device=device)
    if "Unable to find package" in output or not output.strip():
        return None
    found = False
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("versionName="):
            return line.split("=", 1)[1].strip()
        if line.startswith("Package ["):
            found = True
    return "" if found else None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            apk_path=dict(type='str', required=True),
            package=dict(type='str', required=False, default=None),
            version=dict(type='str', required=False, default=None),
            device=dict(type='str', required=False, default=None),
            adb_path=dict(type='str', required=False, default=None),
        ),
        supports_check_mode=True,
    )

    apk_path = module.params['apk_path']
    package = module.params['package']
    version = module.params['version']
    device = module.params['device']
    adb_path = module.params['adb_path'] or shutil.which('adb')
    check_mode = getattr(module, 'check_mode', False)

    if not adb_path:
        module.fail_json(msg="adb not found in PATH.", changed=False)
    if not apk_path:
        module.fail_json(msg="apk_path is required.", changed=False)

    from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
        run_adb_command, adb_shell, AdbError,
    )

    try:
        # Idempotency check (only possible when the package name is known).
        current_version = None
        if package:
            current_version = _installed_version(adb_path, package, device)
            already_satisfied = (
                current_version is not None
                and (version is None or current_version == version)
            )
            if already_satisfied:
                module.exit_json(
                    changed=False,
                    msg=f"{package} already installed"
                        + (f" at version {current_version}" if current_version else ""),
                    installed_version=current_version,
                )

        if check_mode:
            module.exit_json(changed=True, msg=f"would install {apk_path}",
                             installed_version=current_version)

        # If apk_path is a device path, use 'adb shell pm install'.
        if apk_path.startswith("/data/") or apk_path.startswith("/sdcard/"):
            output = adb_shell(adb_path, f"pm install -r {apk_path}", device=device)
        else:
            output = run_adb_command(adb_path, ["install", "-r", apk_path], device=device)

        if "Success" in output:
            result = dict(changed=True, msg=output)
            if package:
                result["installed_version"] = current_version
            module.exit_json(**result)
        if "INSTALL_FAILED_USER_RESTRICTED" in output:
            reason = "Install failed due to user restrictions (e.g. Play Protect, device policy, or unknown sources not allowed)."
        else:
            reason = output
        module.fail_json(msg=f"Install failed: {reason}", changed=False)
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", changed=False)


if __name__ == '__main__':
    main()
