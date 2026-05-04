
DOCUMENTATION = r'''
---
module: adb_uninstall
short_description: Uninstall APK from Android device via ADB
description:
  - Uninstalls an app from an Android device using ADB.
options:
  package:
    description:
      - Package name to uninstall.
    required: true
    type: str
author:
  - Kasper Daems
version_added: '1.2.0'
'''

EXAMPLES = r'''
- name: Uninstall APK
  adb_uninstall:
    package: com.example.app
'''

RETURN = r'''
changed:
  description: Whether the APK was uninstalled
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
            package=dict(type='str', required=True),
        )
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH. Please install Android platform-tools and ensure adb is available.")

    package = module.params['package']
    if not package:
        module.fail_json(msg="package is required.")

    # TODO: Implement ADB uninstall logic
    module.exit_json(changed=False, msg='Not implemented')

if __name__ == '__main__':
    main()
