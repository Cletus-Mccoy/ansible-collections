#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to push/pull files to/from Android device using adb

DOCUMENTATION = r'''
---
module: adb_files
short_description: Push or pull files to/from an Android device via ADB
description:
  - Transfers files between the Ansible controller and an Android device using
    C(adb push) / C(adb pull).
options:
  action:
    description:
      - C(push) copies a local file to the device; C(pull) copies a device file
        to the controller.
    required: true
    type: str
    choices: [push, pull]
  src:
    description:
      - Source path. For C(push), a path on the controller; for C(pull), a path on the device.
    required: true
    type: str
  dest:
    description:
      - Destination path. For C(push), a path on the device; for C(pull), a path on the controller.
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
- name: Push a config file to the device
  cletus_mccoy.android_adb.adb_files:
    action: push
    src: /tmp/app.conf
    dest: /sdcard/app.conf

- name: Pull a log file from the device
  cletus_mccoy.android_adb.adb_files:
    action: pull
    src: /sdcard/app.log
    dest: /tmp/app.log
'''

RETURN = r'''
changed:
  description: Whether the transfer was performed.
  type: bool
  returned: always
msg:
  description: Informational message.
  type: str
  returned: always
stdout:
  description: Raw output from adb push/pull.
  type: str
  returned: success
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_push, adb_pull, AdbError
import os

def main():
    module_args = dict(
        action=dict(type='str', required=True, choices=['push', 'pull']),
        src=dict(type='str', required=True),
        dest=dict(type='str', required=True),
        device=dict(type='str', required=False, default=None),
        adb_path=dict(type='str', required=False, default='adb'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    action = module.params['action']
    src = module.params['src']
    dest = module.params['dest']
    device = module.params['device']
    adb_path = module.params['adb_path']

    try:
        if action == 'push':
            if not os.path.exists(src):
                module.fail_json(msg='Source file does not exist: %s' % src)
            output = adb_push(adb_path, src, dest, device=device)
            module.exit_json(changed=True, msg='Pushed %s to %s' % (src, dest), stdout=output)
        elif action == 'pull':
            output = adb_pull(adb_path, src, dest, device=device)
            module.exit_json(changed=True, msg='Pulled %s to %s' % (src, dest), stdout=output)
        else:
            module.fail_json(msg='Invalid action: %s' % action)
    except AdbError as e:
        module.fail_json(msg=str(e))
    except Exception as e:
        module.fail_json(msg='Unexpected error: %s' % str(e))

if __name__ == '__main__':
    main()
