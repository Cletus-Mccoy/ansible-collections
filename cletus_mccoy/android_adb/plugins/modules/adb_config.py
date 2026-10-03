from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adb_config
short_description: Manage Android device configuration over ADB
description:
  - Read, backup, change, and validate configuration values on Android devices using ADB.
options:
  action:
    description:
      - Action to perform.
      - V(get), V(set), V(backup) and V(validate) work on system properties
        (C(getprop)/C(setprop)).
      - V(settings_get), V(settings_put) and V(settings_delete) work on the
        Settings database and need O(namespace). Prefer the dedicated
        M(cletus_mccoy.android_adb.adb_settings) module for these.
      - V(shell) runs O(command) and always reports C(changed=true); prefer
        M(cletus_mccoy.android_adb.adb_shell).
    required: true
    type: str
    choices: [get, set, backup, validate, settings_get, settings_put, settings_delete, shell]
  namespace:
    description:
      - Settings namespace for the C(settings_*) actions (C(system),
        C(secure) or C(global)).
    type: str
  command:
    description:
      - Shell command to run for O(action=shell).
    type: str
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
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
  - Kasper Daems (@Cletus-Mccoy)
version_added: '0.1.0'
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
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.config import (
    get_property, backup_properties, validate_property, settings_get,
    set_property_idempotent, settings_set_idempotent, settings_delete_idempotent,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **adb_argument_spec(),
            action=dict(
                type="str",
                required=True,
                choices=["get", "set", "backup", "validate", "settings_get", "settings_put", "settings_delete", "shell"]
            ),
            key=dict(type="str", required=False, no_log=False),
            value=dict(type="str", required=False),
            backup_path=dict(type="str", required=False),
            namespace=dict(type="str", required=False),
            command=dict(type="str", required=False),
        ),
        supports_check_mode=True,
    )

    adb_path = resolve_adb(module)

    device = module.params.get("device")
    action = module.params["action"]
    key = module.params.get("key")
    value = module.params.get("value")

    namespace = module.params.get("namespace")
    command = module.params.get("command")
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
            changed, previous = set_property_idempotent(
                adb_path, key, value, device=device, check_mode=module.check_mode
            )
            module.exit_json(changed=changed, value=value, previous_value=previous)
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
        elif action == "settings_get":
            if not namespace or not key:
                module.fail_json(msg="namespace and key are required for settings_get action")
            result = settings_get(adb_path, namespace, key, device=device)
            module.exit_json(changed=False, value=result)
        elif action == "settings_put":
            if not namespace or not key or value is None:
                module.fail_json(msg="namespace, key, and value are required for settings_put action")
            changed, previous = settings_set_idempotent(
                adb_path, namespace, key, value, device=device, check_mode=module.check_mode
            )
            module.exit_json(changed=changed, value=value, previous_value=previous)
        elif action == "settings_delete":
            if not namespace or not key:
                module.fail_json(msg="namespace and key are required for settings_delete action")
            changed, previous = settings_delete_idempotent(
                adb_path, namespace, key, device=device, check_mode=module.check_mode
            )
            module.exit_json(changed=changed, previous_value=previous)
        elif action == "shell":
            if not command:
                module.fail_json(msg="command is required for shell action")
            from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
            result = adb_shell(adb_path, command, device=device)
            module.exit_json(changed=True, stdout=result)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
