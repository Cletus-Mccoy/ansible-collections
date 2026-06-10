DOCUMENTATION = r'''
---
module: adb_device_state
short_description: Manage Android device state over ADB
version_added: '1.1.0'
description:
    - Reboot, shutdown, or change state of Android devices using ADB.
options:
    device:
        description:
            - Device serial or IP:port to target.
        required: false
        type: str
    state:
        description:
            - Desired device state.
        required: true
        type: str
        choices: [reboot, shutdown, recovery, bootloader]
author:
    - Kasper Daems
'''

EXAMPLES = r'''
- name: Reboot the device
  cletus_mccoy.android_adb.adb_device_state:
    state: reboot
    device: "192.168.1.50:5555"
'''

RETURN = r'''
changed:
  description: Always true on success (the requested state change is an action).
  type: bool
  returned: always
msg:
  description: Informational message.
  type: str
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
import shutil

def main():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False),
            state=dict(type="str", required=True, choices=["reboot", "shutdown", "recovery", "bootloader"]),
        ),
        supports_check_mode=True
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH")

    device = module.params.get("device")
    state = module.params["state"]

    try:
        if state == "reboot":
            adb_shell(adb_path, "reboot", device=device)
        elif state == "shutdown":
            adb_shell(adb_path, "reboot -p", device=device)
        elif state == "recovery":
            adb_shell(adb_path, "reboot recovery", device=device)
        elif state == "bootloader":
            adb_shell(adb_path, "reboot bootloader", device=device)
        module.exit_json(changed=True, msg=f"Device state changed: {state}")
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
