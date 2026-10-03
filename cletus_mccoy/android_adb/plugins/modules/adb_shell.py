#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to run arbitrary adb shell commands on a device
from __future__ import absolute_import, division, print_function
__metaclass__ = type

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
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
  - Kasper Daems (@Cletus-Mccoy)
version_added: '0.2.0'
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
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell, AdbError


def main():
    module_args = dict(
        **adb_argument_spec(),
        command=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    command = module.params['command']
    device = module.params['device']
    adb_path = resolve_adb(module)
    server_port = module.params['adb_server_port']

    try:
        output = adb_shell(adb_path, command, device=device, server_port=server_port)
        module.exit_json(changed=True, stdout=output)
    except AdbError as e:
        module.fail_json(msg=str(e))
    except Exception as e:
        module.fail_json(msg='Unexpected error: %s' % str(e))


if __name__ == '__main__':
    main()
