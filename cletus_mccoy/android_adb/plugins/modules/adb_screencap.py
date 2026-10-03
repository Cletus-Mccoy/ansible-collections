#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to capture a screenshot from an Android device
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adb_screencap
short_description: Capture a screenshot from an Android device to the controller
description:
  - Captures the current screen with C(adb exec-out screencap -p) and writes the
    PNG to a path on the Ansible controller.
  - Uses C(exec-out) (not C(shell)) so the binary stream is not mangled by
    line-ending translation.
  - This is an action module — it always reports C(changed=true) because it writes
    a fresh capture every run.
options:
  dest:
    description:
      - Controller-side path to write the PNG to.
    required: true
    type: path
extends_documentation_fragment:
  - cletus_mccoy.android_adb.adb
author:
  - Kasper Daems (@Cletus-Mccoy)
version_added: '0.3.0'
'''

EXAMPLES = r'''
- name: Screenshot the current screen
  cletus_mccoy.android_adb.adb_screencap:
    dest: /tmp/device.png
    device: 192.168.1.50:5555
'''

RETURN = r'''
changed:
  description: Always true.
  returned: always
  type: bool
dest:
  description: The controller path the screenshot was written to.
  returned: success
  type: str
size:
  description: Size of the written PNG in bytes.
  returned: success
  type: int
'''


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_argument_spec, resolve_adb
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
    AdbError,
    run_adb_binary,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **adb_argument_spec(),
            dest=dict(type="path", required=True),
        ),
        supports_check_mode=True,
    )

    adb_path = resolve_adb(module)

    dest = module.params["dest"]
    device = module.params["device"]

    if module.check_mode:
        module.exit_json(changed=True, dest=dest)

    try:
        png = run_adb_binary(adb_path, ["exec-out", "screencap", "-p"], device=device)
        if not png.startswith(b"\x89PNG"):
            module.fail_json(
                msg="screencap did not return PNG data (got %d bytes); the device "
                    "may not support 'screencap -p'" % len(png),
                changed=False,
            )
        with open(dest, "wb") as fh:
            fh.write(png)
        module.exit_json(changed=True, dest=dest, size=len(png))
    except AdbError as e:
        module.fail_json(msg="ADB error: %s" % e, changed=False)
    except Exception as e:
        module.fail_json(msg="Unexpected error: %s" % e, changed=False)


if __name__ == "__main__":
    main()
