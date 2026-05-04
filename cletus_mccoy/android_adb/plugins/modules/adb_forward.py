
DOCUMENTATION = r'''
---
module: adb_forward
short_description: Forward ports between host and Android device via ADB
description:
  - Forwards ports between the host and an Android device using ADB.
options:
  local:
    description:
      - Local port (host).
    required: true
    type: str
  remote:
    description:
      - Remote port (device).
    required: true
    type: str
author:
  - Kasper Daems
version_added: '1.2.0'
'''

EXAMPLES = r'''
- name: Forward port
  adb_forward:
    local: tcp:8000
    remote: tcp:8000
'''

RETURN = r'''
changed:
  description: Whether the port was forwarded
  type: bool
  returned: always
msg:
  description: Informational message
  type: str
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import shutil

def main():
    module = AnsibleModule(
        argument_spec=dict(
            local=dict(type='str', required=True),
            remote=dict(type='str', required=True),
        )
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH. Please install Android platform-tools and ensure adb is available.")

    local = module.params['local']
    remote = module.params['remote']
    # TODO: Implement ADB forward logic
    module.exit_json(changed=False, msg='Not implemented')

if __name__ == '__main__':
    main()
    if not local:
      module.fail_json(msg="local is required.")
    if not remote:
      module.fail_json(msg="remote is required.")

    # TODO: Implement ADB port forwarding logic
    module.exit_json(changed=False, msg='Not implemented')

if __name__ == '__main__':
    main()
