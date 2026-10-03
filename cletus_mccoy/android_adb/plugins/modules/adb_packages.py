from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adb_packages
short_description: List installed Android packages over ADB
description:
    - Lists installed packages on an Android device using ADB.
options:
    include_system:
        description:
            - Whether to include system packages.
        required: false
        type: bool
        default: false
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
    - Kasper Daems (@Cletus-Mccoy)
version_added: '0.1.0'
'''  # noqa

EXAMPLES = r'''
- name: List user-installed packages
  cletus_mccoy.android_adb.adb_packages:
    device: "192.168.1.50:5555"
  register: pkgs

- name: List all packages including system
  cletus_mccoy.android_adb.adb_packages:
    include_system: true
'''

RETURN = r'''
packages:
  description: List of installed package names.
  type: list
  elements: str
  returned: success
changed:
  description: Always false (read-only).
  type: bool
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.parsing import parse_packages


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **adb_argument_spec(),
            include_system=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    adb_path = resolve_adb(module)

    device = module.params.get("device")
    include_system = module.params["include_system"]
    cmd = "pm list packages" if include_system else "pm list packages -3"

    try:
        output = adb_shell(adb_path, cmd, device=device)
        packages = parse_packages(output)
        module.exit_json(changed=False, packages=packages)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
