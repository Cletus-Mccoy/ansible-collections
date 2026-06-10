DOCUMENTATION = r'''
module: adb_logcat
short_description: Fetch Android logcat output over ADB
description:
  - Fetches logcat output from an Android device using ADB.
options:
  device:
    description:
      - Device serial or IP:port to target.
    required: false
    type: str
  lines:
    description:
      - Number of log lines to fetch.
    required: false
    type: int
    default: 100
author:
  - Kasper Daems
version_added: '1.0.0'
'''  # noqa

#!/usr/bin/python3
# -*- coding: utf-8 -*-
DOCUMENTATION = r'''
---
module: adb_logcat
short_description: Fetch Android logcat output over ADB
description:
  - Fetches logcat output from an Android device using ADB.
options:
  device:
    description:
      - Device serial or IP:port to target.
    required: false
    type: str
  lines:
    description:
      - Number of log lines to fetch.
    required: false
    type: int
    default: 100
author:
  - Kasper Daems
version_added: '1.0.0'
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

def main():
  module_args = dict(
    device=dict(type='str', required=False, default=None),
    lines=dict(type='int', required=False, default=100),
    adb_path=dict(type='str', required=False, default='adb'),
  )
  module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

  device = module.params['device']
  lines = module.params['lines']
  adb_path = module.params['adb_path']
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
