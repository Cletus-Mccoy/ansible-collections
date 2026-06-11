#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to tap a UI element (by text/resource-id) or coordinates

DOCUMENTATION = r'''
---
module: adb_ui_tap
short_description: Tap a UI element by text/resource-id, or at raw coordinates
description:
  - Sends a tap with C(input tap). The tap location is either given directly as
    O(x)/O(y), or resolved from the current view hierarchy by matching a node's
    O(text), O(resource_id) or O(content_desc) and tapping its center.
  - When matching by selector it dumps the UI (see
    M(cletus_mccoy.android_adb.adb_ui_dump)) and computes the center of the matched
    node's bounds.
  - This is an action module — it always reports C(changed=true).
  - "Note: foreground-stealing overlay apps (e.g. a rotation-lock app) will fight
    UI automation by grabbing focus; C(force-stop) them first."
options:
  text:
    description: [Match the node whose C(text) equals this.]
    required: false
    type: str
  resource_id:
    description: [Match the node whose C(resource-id) equals this.]
    required: false
    type: str
  content_desc:
    description: [Match the node whose C(content-desc) equals this.]
    required: false
    type: str
  x:
    description: [Tap at this X coordinate (requires O(y)). Bypasses node matching.]
    required: false
    type: int
  y:
    description: [Tap at this Y coordinate (requires O(x)).]
    required: false
    type: int
  index:
    description: [Which match to tap when a selector matches multiple nodes (0-based).]
    required: false
    type: int
    default: 0
  device:
    description: [Device serial or C(IP:port) to target.]
    required: false
    type: str
  adb_path:
    description: [Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.]
    required: false
    type: str
author:
  - Kasper Daems
version_added: '0.3.0'
'''

EXAMPLES = r'''
- name: Tap the OK button by text
  cletus_mccoy.android_adb.adb_ui_tap:
    text: OK

- name: Tap a specific widget by resource id
  cletus_mccoy.android_adb.adb_ui_tap:
    resource_id: com.android.settings:id/switch_widget

- name: Tap raw coordinates
  cletus_mccoy.android_adb.adb_ui_tap:
    x: 540
    y: 1200
'''

RETURN = r'''
changed:
  description: Always true.
  returned: always
  type: bool
x:
  description: X coordinate tapped.
  returned: success
  type: int
y:
  description: Y coordinate tapped.
  returned: success
  type: int
matched:
  description: Number of nodes that matched the selector (0 for coordinate taps).
  returned: success
  type: int
'''

import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
    AdbError,
    run_adb_command,
)
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.ui import (
    dump_ui,
    parse_nodes,
    find_nodes,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            text=dict(type="str", required=False, default=None),
            resource_id=dict(type="str", required=False, default=None),
            content_desc=dict(type="str", required=False, default=None),
            x=dict(type="int", required=False, default=None),
            y=dict(type="int", required=False, default=None),
            index=dict(type="int", required=False, default=0),
            device=dict(type="str", required=False, default=None),
            adb_path=dict(type="str", required=False, default=None),
        ),
        required_one_of=[["text", "resource_id", "content_desc", "x"]],
        required_together=[["x", "y"]],
        mutually_exclusive=[
            ["x", "text"], ["x", "resource_id"], ["x", "content_desc"],
        ],
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    device = module.params["device"]
    x = module.params["x"]
    y = module.params["y"]
    index = module.params["index"]

    try:
        matched = 0
        if x is None:
            nodes = parse_nodes(dump_ui(adb_path, device=device))
            hits = find_nodes(
                nodes,
                text=module.params["text"],
                resource_id=module.params["resource_id"],
                content_desc=module.params["content_desc"],
            )
            matched = len(hits)
            if matched == 0:
                module.fail_json(msg="no UI node matched the given selector", changed=False)
            if index < 0 or index >= matched:
                module.fail_json(
                    msg="index %d out of range (%d node(s) matched)" % (index, matched),
                    changed=False,
                )
            center = hits[index]["center"]
            if center is None:
                module.fail_json(msg="matched node has no usable bounds", changed=False)
            x, y = center

        if module.check_mode:
            module.exit_json(changed=True, x=x, y=y, matched=matched)

        run_adb_command(adb_path, ["shell", "input", "tap", str(x), str(y)], device=device)
        module.exit_json(changed=True, x=x, y=y, matched=matched)
    except AdbError as e:
        module.fail_json(msg="ADB error: %s" % e, changed=False)
    except Exception as e:
        module.fail_json(msg="Unexpected error: %s" % e, changed=False)


if __name__ == "__main__":
    main()
