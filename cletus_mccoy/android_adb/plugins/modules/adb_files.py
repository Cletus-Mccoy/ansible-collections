#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Your Name <your.email@example.com>
# Ansible module to push/pull files to/from Android device using adb

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
