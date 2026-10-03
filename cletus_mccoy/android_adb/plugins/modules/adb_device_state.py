from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adb_device_state
short_description: Manage Android device state over ADB
version_added: '0.1.0'
description:
    - Reboot, shutdown, or change state of Android devices using ADB.
options:
    state:
        description:
            - Desired device state.
        required: true
        type: str
        choices: [reboot, shutdown, recovery, bootloader]
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
    - Kasper Daems (@Cletus-Mccoy)
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
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **adb_argument_spec(),
            state=dict(type="str", required=True, choices=["reboot", "shutdown", "recovery", "bootloader"]),
        ),
        supports_check_mode=True
    )

    adb_path = resolve_adb(module)

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
