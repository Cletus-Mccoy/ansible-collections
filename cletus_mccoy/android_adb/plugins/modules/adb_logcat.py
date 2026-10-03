#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adb_logcat
short_description: Fetch Android logcat output over ADB
description:
  - Fetches logcat output from an Android device using ADB.
options:
  lines:
    description:
      - Number of log lines to fetch.
    required: false
    type: int
    default: 100
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
  - Kasper Daems (@Cletus-Mccoy)
version_added: '0.1.0'
'''

EXAMPLES = r'''
- name: Fetch last 10 logcat lines
  cletus_mccoy.android_adb.adb_logcat:
    lines: 10
'''

RETURN = r'''
output:
  description: Logcat output
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb


def main():
    module_args = dict(
        **adb_argument_spec(),
        lines=dict(type='int', required=False, default=100),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    device = module.params['device']
    lines = module.params['lines']
    adb_path = resolve_adb(module)
    try:
        from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import run_adb_command, AdbError
        args = ["logcat", "-t", str(lines)]
        output = run_adb_command(adb_path, args, device=device)
        module.exit_json(changed=False, output=output)
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}")
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}")


if __name__ == '__main__':
    main()
