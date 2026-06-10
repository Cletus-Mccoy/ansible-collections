DOCUMENTATION = r'''
---
module: adb_settings
short_description: Manage Android Settings database values over ADB
description:
  - Reads and writes values in the Android Settings provider via
    C(settings get|put|delete <namespace> <key>).
  - This is a different subsystem from system properties (C(getprop)/C(setprop),
    managed by M(cletus_mccoy.android_adb.adb_config)). Most user-facing device
    configuration (screen timeout, brightness, locale-related toggles, accessibility,
    developer options) lives in the Settings database, not in system properties.
  - The module is idempotent. It reads the current value and only writes when it
    differs from the desired value, returning C(changed=false) otherwise.
options:
  device:
    description:
      - Device serial or C(IP:port) to target. If omitted, the single attached
        device is used.
    required: false
    type: str
  namespace:
    description:
      - Settings namespace.
      - C(system) and C(global) are writable by the ADB shell user without root.
      - C(secure) requires the C(WRITE_SECURE_SETTINGS) permission, which can only
        be granted to an installed app via
        C(pm grant <pkg> android.permission.WRITE_SECURE_SETTINGS). The ADB shell
        itself (UID 2000) can already write C(secure) on most builds, but writes
        may be rejected on hardened/managed devices.
    required: true
    type: str
    choices: [system, secure, global]
  key:
    description:
      - The settings key to read, write, or delete.
    required: true
    type: str
  value:
    description:
      - Desired value. Required when O(state=present).
    required: false
    type: str
  state:
    description:
      - C(present) ensures the key equals O(value).
      - C(absent) deletes the key (no-op if already unset).
      - C(read) returns the current value without changing anything.
    required: false
    type: str
    choices: [present, absent, read]
    default: present
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
author:
  - Kasper Daems
version_added: '0.2.0'
'''

EXAMPLES = r'''
- name: Set screen-off timeout to 10 minutes (Settings DB, system namespace)
  cletus_mccoy.android_adb.adb_settings:
    namespace: system
    key: screen_off_timeout
    value: "600000"

- name: Keep screen on while charging (global)
  cletus_mccoy.android_adb.adb_settings:
    namespace: global
    key: stay_on_while_plugged_in
    value: "3"

- name: Read the current location mode
  cletus_mccoy.android_adb.adb_settings:
    namespace: secure
    key: location_mode
    state: read
  register: loc

- name: Remove a custom setting
  cletus_mccoy.android_adb.adb_settings:
    namespace: system
    key: my_custom_flag
    state: absent
'''

RETURN = r'''
value:
  description: The desired value (state=present) or the current value (state=read).
  returned: when state is present or read
  type: str
previous_value:
  description: The value before the change (None if it was unset).
  returned: when state is present or absent
  type: str
changed:
  description: Whether a change was made.
  returned: always
  type: bool
'''

import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import AdbError
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.config import (
    settings_get,
    settings_set_idempotent,
    settings_delete_idempotent,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False, default=None),
            namespace=dict(type="str", required=True, choices=["system", "secure", "global"]),
            key=dict(type="str", required=True),
            value=dict(type="str", required=False, default=None),
            state=dict(type="str", required=False, default="present",
                       choices=["present", "absent", "read"]),
            adb_path=dict(type="str", required=False, default=None),
        ),
        required_if=[("state", "present", ["value"])],
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    device = module.params["device"]
    namespace = module.params["namespace"]
    key = module.params["key"]
    value = module.params["value"]
    state = module.params["state"]

    try:
        if state == "read":
            current = settings_get(adb_path, namespace, key, device=device)
            module.exit_json(changed=False, value=current)
        elif state == "present":
            changed, previous = settings_set_idempotent(
                adb_path, namespace, key, value, device=device,
                check_mode=module.check_mode,
            )
            module.exit_json(changed=changed, value=value, previous_value=previous)
        else:  # absent
            changed, previous = settings_delete_idempotent(
                adb_path, namespace, key, device=device,
                check_mode=module.check_mode,
            )
            module.exit_json(changed=changed, previous_value=previous)
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", changed=False)


if __name__ == "__main__":
    main()
