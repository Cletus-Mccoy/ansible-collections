DOCUMENTATION = r'''
---
module: adb_device_info
short_description: Gather Android device info over ADB
description:
    - Gathers device information from an Android device using ADB.
    - Also collects battery, storage, and network information.
options:
    device:
        description:
            - Device serial or IP:port to target.
        required: false
        type: str
author:
    - Kasper Daems
version_added: '1.0.0'
'''  # noqa

EXAMPLES = r'''
- name: Gather Android device info
  cletus_mccoy.android_adb.adb_device_info:
    device: "192.168.1.50:5555"
  register: info
'''

RETURN = r'''
android_device_info:
  description: Parsed device properties plus battery, storage and network output.
  type: dict
  returned: success
changed:
  description: Always false (read-only).
  type: bool
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.parsing import parse_getprop, extract_device_info
import shutil


def main():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False),
        ),
        supports_check_mode=True
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH")

    device = module.params.get("device")

    try:
        # Basic device info
        output = adb_shell(adb_path, "getprop", device=device)
        props = parse_getprop(output)
        info = extract_device_info(props)

        # Battery info
        battery_output = adb_shell(adb_path, "dumpsys battery", device=device)
        info["battery"] = battery_output

        # Storage info
        storage_output = adb_shell(adb_path, "df /data", device=device)
        info["storage"] = storage_output

        # Network info
        network_output = adb_shell(adb_path, "ip addr show", device=device)
        info["network"] = network_output

        module.exit_json(
            changed=False,
            android_device_info=info
        )

    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()