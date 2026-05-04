DOCUMENTATION = r'''
---
module: adb_config
short_description: Manage Android device configuration over ADB
description:
  - Read, backup, change, and validate configuration values on Android devices using ADB.
options:
  device:
    description:
      - Device serial or IP:port to target.
    required: false
    type: str
  action:
    description:
      - Action to perform (get, set, backup, validate).
    required: true
    type: str
    choices: [get, set, backup, validate]
  key:
    description:
      - Configuration key/property to manage (for get/set/validate).
    required: false
    type: str
  value:
    description:
      - Value to set (for set action).
    required: false
    type: str
  backup_path:
    description:
      - Path to store backup (for backup action).
    required: false
    type: str
author:
  - Kasper Daems
version_added: '1.1.0'
'''  # noqa

EXAMPLES = r'''
- name: Get a property
  adb_config:
    action: get
    key: ro.product.model

- name: Set a property
  adb_config:
    action: set
    key: persist.sys.locale
    value: en-US

- name: Backup properties
  adb_config:
    action: backup
    backup_path: /tmp/device_props.bak

- name: Validate a property
  adb_config:
    action: validate
    key: ro.product.model
    value: Pixel 7
'''

RETURN = r'''
value:
  description: Value of the property (for get/validate).
  returned: when supported
  type: str
  sample: Pixel 7
changed:
  description: Whether any change was made.
  returned: always
  type: bool
backup_path:
  description: Path where backup was stored.
  returned: when action=backup
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.config import (
    get_property, set_property, backup_properties, validate_property
)
import shutil

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False),
            action=dict(type="str", required=True, choices=["get", "set", "backup", "validate"]),
            key=dict(type="str", required=False),
            value=dict(type="str", required=False),
            backup_path=dict(type="str", required=False),
        ),
        supports_check_mode=True,
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH")

    device = module.params.get("device")
    action = module.params["action"]
    key = module.params.get("key")
    value = module.params.get("value")
    backup_path = module.params.get("backup_path")

    try:
        if action == "get":
            if not key:
                module.fail_json(msg="key is required for get action")
            result = get_property(adb_path, key, device=device)
            module.exit_json(changed=False, value=result)
        elif action == "set":
            if not key or value is None:
                module.fail_json(msg="key and value are required for set action")
            changed = set_property(adb_path, key, value, device=device)
            module.exit_json(changed=changed)
        elif action == "backup":
            if not backup_path:
                module.fail_json(msg="backup_path is required for backup action")
            backup_properties(adb_path, backup_path, device=device)
            module.exit_json(changed=True, backup_path=backup_path)
        elif action == "validate":
            if not key or value is None:
                module.fail_json(msg="key and value are required for validate action")
            valid = validate_property(adb_path, key, value, device=device)
            module.exit_json(changed=False, valid=valid, value=value)
    except Exception as e:
        module.fail_json(msg=str(e))

def main():
    run_module()

if __name__ == "__main__":
    main()
