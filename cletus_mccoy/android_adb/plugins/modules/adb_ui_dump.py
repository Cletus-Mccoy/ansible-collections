#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to dump the current UI hierarchy from an Android device

DOCUMENTATION = r'''
---
module: adb_ui_dump
short_description: Dump the current UI view hierarchy from an Android device
description:
  - Captures the on-screen view hierarchy with C(uiautomator dump) and returns it
    as XML plus a flattened list of nodes (text, resource-id, content-desc, class,
    bounds and computed center point).
  - Dumps to a file on C(/sdcard) and C(cat)s it back, because dumping straight to
    stdout / C(/dev/tty) is unreliable and often corrupts the XML.
  - Useful for role-driven first-time setup that is unavoidably UI-based (logging
    into Tailscale, toggling "Rooted debugging", etc.). Pair it with
    M(cletus_mccoy.android_adb.adb_ui_tap).
  - Read-only — reports C(changed=false).
options:
  dest:
    description:
      - Optional controller-side path to also save the XML to.
    required: false
    type: path
  dump_path:
    description:
      - On-device path C(uiautomator dump) writes to before it is read back.
    required: false
    type: str
    default: /sdcard/window_dump.xml
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
author:
  - Kasper Daems
version_added: '0.3.0'
'''

EXAMPLES = r'''
- name: Dump the current UI
  cletus_mccoy.android_adb.adb_ui_dump:
    device: 192.168.1.50:5555
  register: ui

- name: Show the clickable nodes
  debug:
    msg: "{{ ui.nodes | selectattr('clickable') | map(attribute='text') | list }}"
'''

RETURN = r'''
changed:
  description: Always false (read-only).
  returned: always
  type: bool
xml:
  description: The raw uiautomator XML.
  returned: success
  type: str
nodes:
  description: Flattened nodes with text, resource_id, content_desc, class,
    package, clickable, bounds (x1,y1,x2,y2) and center (x,y).
  returned: success
  type: list
  elements: dict
'''

import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import AdbError
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.ui import (
    dump_ui,
    parse_nodes,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type="path", required=False, default=None),
            dump_path=dict(type="str", required=False, default="/sdcard/window_dump.xml"),
            device=dict(type="str", required=False, default=None),
            adb_path=dict(type="str", required=False, default=None),
        ),
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    device = module.params["device"]
    dest = module.params["dest"]

    try:
        xml = dump_ui(adb_path, device=device, dump_path=module.params["dump_path"])
        nodes = parse_nodes(xml)
        if dest:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(xml)
        module.exit_json(changed=False, xml=xml, nodes=nodes)
    except AdbError as e:
        module.fail_json(msg="ADB error: %s" % e, changed=False)
    except Exception as e:
        module.fail_json(msg="Unexpected error: %s" % e, changed=False)


if __name__ == "__main__":
    main()
