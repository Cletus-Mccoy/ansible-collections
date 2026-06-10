#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to run arbitrary adb shell commands on a device

DOCUMENTATION = r'''
---
module: adb_shell
short_description: Run an arbitrary command on an Android device via ADB shell
description:
  - Executes a command on an Android device using C(adb shell) and returns its output.
  - This is an action module — it always reports C(changed=true) since the collection
    cannot know whether the command altered device state.
options:
  command:
    description:
      - The shell command to run on the device.
    required: true
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
    default: adb
author:
  - Kasper Daems
version_added: '1.0.0'
'''

EXAMPLES = r'''
- name: Wake the screen
  cletus_mccoy.android_adb.adb_shell:
    command: input keyevent KEYCODE_WAKEUP

- name: Read a property
  cletus_mccoy.android_adb.adb_shell:
    command: getprop ro.product.model
  register: model
'''

RETURN = r'''
changed:
  description: Always true (the module cannot determine idempotency of an arbitrary command).
  type: bool
  returned: always
stdout:
  description: Standard output of the command.
  type: str
  returned: success
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell, AdbError


def main():
    module_args = dict(
        command=dict(type='str', required=True),
        device=dict(type='str', required=False, default=None),
        adb_path=dict(type='str', required=False, default='adb'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    command = module.params['command']
    device = module.params['device']
    adb_path = module.params['adb_path']

    try:
        output = adb_shell(adb_path, command, device=device)
        module.exit_json(changed=True, stdout=output)
    except AdbError as e:
        module.fail_json(msg=str(e))
    except Exception as e:
        module.fail_json(msg='Unexpected error: %s' % str(e))

if __name__ == '__main__':
    main()
