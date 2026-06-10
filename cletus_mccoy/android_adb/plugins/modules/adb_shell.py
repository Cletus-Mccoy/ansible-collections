#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Your Name <your.email@example.com>
# Simplified Ansible module to run arbitrary adb shell commands on a device

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
