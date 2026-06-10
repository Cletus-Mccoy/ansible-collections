DOCUMENTATION = r'''
---
module: adb_intent
short_description: Send an Android intent over ADB
description:
  - Sends an intent to an Android device via C(adb shell am).
  - Supports starting an activity (C(am start)), starting a service
    (C(am startservice)), and broadcasting (C(am broadcast)).
  - This is an action module — sending an intent is not idempotent, so it always
    reports C(changed=true) on success.
options:
  device:
    description:
      - Device serial or C(IP:port) to target.
    required: false
    type: str
  command:
    description:
      - Which C(am) sub-command to use.
    required: false
    type: str
    default: start
    choices: [start, startservice, broadcast]
  action:
    description:
      - Intent action, e.g. C(android.intent.action.VIEW).
    required: false
    type: str
  data:
    description:
      - Data URI for the intent (C(-d)).
    required: false
    type: str
  component:
    description:
      - Explicit component, e.g. C(com.example/.MainActivity) (C(-n)).
    required: false
    type: str
  mime_type:
    description:
      - MIME type for the intent (C(-t)).
    required: false
    type: str
  category:
    description:
      - Intent category, e.g. C(android.intent.category.LAUNCHER) (C(-c)).
    required: false
    type: str
  extras:
    description:
      - String extras to pass, as a dict of key/value pairs (each rendered as C(--es key value)).
    required: false
    type: dict
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
author:
  - Kasper Daems
version_added: '0.2.0'
'''

EXAMPLES = r'''
- name: Open a URL on the device
  cletus_mccoy.android_adb.adb_intent:
    action: android.intent.action.VIEW
    data: https://example.com

- name: Launch a specific activity
  cletus_mccoy.android_adb.adb_intent:
    component: com.example.app/.MainActivity

- name: Broadcast a custom intent with extras
  cletus_mccoy.android_adb.adb_intent:
    command: broadcast
    action: com.example.ACTION_REFRESH
    extras:
      mode: full
'''

RETURN = r'''
changed:
  description: Always true on success (sending an intent is an action).
  type: bool
  returned: always
stdout:
  description: Output from the am command.
  type: str
  returned: success
'''

import shutil

from ansible.module_utils.basic import AnsibleModule


def _build_am_args(params):
    args = ["am", params["command"]]
    if params.get("action"):
        args += ["-a", params["action"]]
    if params.get("data"):
        args += ["-d", params["data"]]
    if params.get("mime_type"):
        args += ["-t", params["mime_type"]]
    if params.get("category"):
        args += ["-c", params["category"]]
    if params.get("component"):
        args += ["-n", params["component"]]
    for key, value in (params.get("extras") or {}).items():
        args += ["--es", str(key), str(value)]
    return args


def main():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False, default=None),
            command=dict(type="str", required=False, default="start",
                         choices=["start", "startservice", "broadcast"]),
            action=dict(type="str", required=False, default=None),
            data=dict(type="str", required=False, default=None),
            component=dict(type="str", required=False, default=None),
            mime_type=dict(type="str", required=False, default=None),
            category=dict(type="str", required=False, default=None),
            extras=dict(type="dict", required=False, default=None),
            adb_path=dict(type="str", required=False, default=None),
        ),
        required_one_of=[["action", "component"]],
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    device = module.params["device"]
    am_args = _build_am_args(module.params)
    shell_cmd = " ".join(am_args)

    if getattr(module, "check_mode", False):
        module.exit_json(changed=True, msg=f"would run: {shell_cmd}")

    from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
        adb_shell, AdbError,
    )
    try:
        output = adb_shell(adb_path, shell_cmd, device=device)
        # `am` returns 0 even for some failures; surface common error markers.
        if "Error:" in output or "Exception" in output:
            module.fail_json(msg=f"Intent failed: {output}", changed=False)
        module.exit_json(changed=True, stdout=output)
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", changed=False)


if __name__ == "__main__":
    main()
