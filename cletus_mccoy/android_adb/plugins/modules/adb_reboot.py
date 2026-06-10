DOCUMENTATION = r'''
---
module: adb_reboot
short_description: Reboot an Android device via ADB
description:
  - Reboots an Android device using ADB.
  - Supports normal, bootloader, and recovery reboot modes.
  - Optionally waits for the device to finish booting (C(sys.boot_completed=1))
    before returning. Wait only applies to C(normal) reboots — bootloader and
    recovery do not boot Android.
options:
  mode:
    description:
      - Reboot mode.
    required: false
    type: str
    default: normal
    choices: [normal, bootloader, recovery]
  wait:
    description:
      - Wait for the device to reconnect and finish booting before returning.
        Only meaningful for O(mode=normal).
    required: false
    type: bool
    default: false
  wait_timeout:
    description:
      - Maximum seconds to wait for the device to finish booting.
    required: false
    type: int
    default: 180
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
- name: Reboot device and wait for it to come back
  cletus_mccoy.android_adb.adb_reboot:
    mode: normal
    wait: true
    wait_timeout: 240

- name: Reboot to bootloader
  cletus_mccoy.android_adb.adb_reboot:
    mode: bootloader
'''

RETURN = r'''
changed:
  description: Whether the device was rebooted.
  type: bool
  returned: always
msg:
  description: Informational message.
  type: str
  returned: always
'''

import time

from ansible.module_utils.basic import AnsibleModule
import shutil


def _wait_for_boot(adb_path, device, timeout):
    """Wait until the device reconnects and sys.boot_completed == 1.

    Returns True on success, False on timeout.
    """
    from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
        run_adb_command, AdbError,
    )
    deadline = time.time() + timeout
    # Give the device a moment to actually go down before polling.
    time.sleep(2)
    while time.time() < deadline:
        try:
            run_adb_command(adb_path, ["wait-for-device"], device=device, timeout=10)
            booted = run_adb_command(
                adb_path, ["shell", "getprop", "sys.boot_completed"],
                device=device, timeout=10,
            )
            if booted.strip() == "1":
                return True
        except (AdbError, Exception):
            pass
        time.sleep(3)
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            mode=dict(type='str', required=False, default='normal',
                      choices=['normal', 'bootloader', 'recovery']),
            wait=dict(type='bool', required=False, default=False),
            wait_timeout=dict(type='int', required=False, default=180),
            device=dict(type='str', required=False, default=None),
            adb_path=dict(type='str', required=False, default=None),
        ),
        supports_check_mode=True,
    )

    mode = module.params['mode']
    wait = module.params['wait']
    wait_timeout = module.params['wait_timeout']
    device = module.params['device']
    adb_path = module.params['adb_path'] or shutil.which('adb')
    check_mode = getattr(module, 'check_mode', False)

    if not adb_path:
        module.fail_json(msg="adb not found in PATH. Please install Android platform-tools and ensure adb is available.", changed=False)

    if check_mode:
        module.exit_json(changed=True, msg=f"would reboot ({mode})")

    try:
        from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import run_adb_command, AdbError
        args = ["reboot"] if mode == 'normal' else ["reboot", mode]
        output = run_adb_command(adb_path, args, device=device)

        if wait and mode == 'normal':
            if not _wait_for_boot(adb_path, device, wait_timeout):
                module.fail_json(
                    msg=f"Device did not finish booting within {wait_timeout}s after reboot",
                    changed=True,
                )
            module.exit_json(changed=True, msg=f"Device rebooted ({mode}) and finished booting", stdout=output)

        module.exit_json(changed=True, msg=f"Device rebooted ({mode})", stdout=output)
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", changed=False)


if __name__ == '__main__':
    main()
