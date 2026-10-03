from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adb_uninstall
short_description: Uninstall an app from an Android device via ADB
description:
  - Uninstalls an app (by package name) from an Android device using ADB.
  - Idempotent. If the package is not installed, the module reports
    C(changed=false) and does nothing.
options:
  package:
    description:
      - Package name to uninstall (e.g. C(com.example.app)).
    required: true
    type: str
  keep_data:
    description:
      - Keep the app's data and cache directories (C(adb uninstall -k)).
    required: false
    type: bool
    default: false
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
  - Kasper Daems (@Cletus-Mccoy)
version_added: '0.1.0'
'''

EXAMPLES = r'''
- name: Uninstall an app
  cletus_mccoy.android_adb.adb_uninstall:
    package: com.example.app
'''

RETURN = r'''
changed:
  description: Whether the app was uninstalled.
  type: bool
  returned: always
msg:
  description: Informational message.
  type: str
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb


def _is_installed(adb_path, package, device):
    from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
    output = adb_shell(adb_path, f"pm list packages {package}", device=device)
    # `pm list packages <pkg>` does prefix matching; match the exact line.
    for line in output.splitlines():
        if line.strip() == f"package:{package}":
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **adb_argument_spec(),
            package=dict(type='str', required=True),
            keep_data=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True,
    )

    package = module.params['package']
    keep_data = module.params['keep_data']
    device = module.params['device']
    adb_path = resolve_adb(module)
    check_mode = getattr(module, 'check_mode', False)
    if not adb_path:
        module.fail_json(msg="adb not found in PATH. Please install Android platform-tools and ensure adb is available.", changed=False)

    try:
        from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import run_adb_command, AdbError

        if not _is_installed(adb_path, package, device):
            module.exit_json(changed=False, msg=f"{package} is not installed")

        if check_mode:
            module.exit_json(changed=True, msg=f"would uninstall {package}")

        args = ["uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package)
        output = run_adb_command(adb_path, args, device=device)
        if "Success" in output:
            module.exit_json(changed=True, msg=output)
        module.fail_json(msg=f"Uninstall failed: {output}", changed=False)
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", changed=False)


if __name__ == '__main__':
    main()
