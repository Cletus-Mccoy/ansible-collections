DOCUMENTATION = r'''
---
module: adb_forward
short_description: Manage ADB port forwards for an Android device
version_added: '1.0.0'
description:
  - Creates or removes an ADB port forward (C(adb forward) / C(adb forward --remove)).
  - Idempotent. Existing forwards are read from C(adb forward --list); a forward
    is only created if absent and only removed if present.
options:
  local:
    description:
      - Local socket spec to forward from, e.g. C(tcp:8000).
    required: true
    type: str
  remote:
    description:
      - Remote socket spec to forward to, e.g. C(tcp:8000). Required when O(state=present).
    required: false
    type: str
  state:
    description:
      - C(present) ensures the forward exists; C(absent) removes it.
    required: false
    type: str
    choices: [present, absent]
    default: present
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
'''

EXAMPLES = r'''
- name: Forward local tcp:8000 to remote tcp:8000
  cletus_mccoy.android_adb.adb_forward:
    local: tcp:8000
    remote: tcp:8000

- name: Remove a forward
  cletus_mccoy.android_adb.adb_forward:
    local: tcp:8000
    state: absent
'''

RETURN = r'''
changed:
  description: Whether the forward set changed.
  type: bool
  returned: always
msg:
  description: Informational message.
  type: str
  returned: always
'''

from ansible.module_utils.basic import AnsibleModule
import shutil


def _existing_forward(adb_path, device, local):
    """Return the remote spec currently forwarded for ``local``, or None."""
    from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import run_adb_command
    output = run_adb_command(adb_path, ["forward", "--list"], device=device)
    target = device
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        serial, l, r = parts[0], parts[1], parts[2]
        if l == local and (device is None or serial == target):
            return r
    return None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            local=dict(type='str', required=True),
            remote=dict(type='str', required=False, default=None),
            state=dict(type='str', required=False, default='present',
                       choices=['present', 'absent']),
            device=dict(type='str', required=False, default=None),
            adb_path=dict(type='str', required=False, default=None),
        ),
        required_if=[("state", "present", ["remote"])],
        supports_check_mode=True,
    )

    local = module.params['local']
    remote = module.params['remote']
    state = module.params['state']
    device = module.params['device']
    adb_path = module.params['adb_path'] or shutil.which('adb')
    check_mode = getattr(module, 'check_mode', False)

    if not adb_path:
        module.fail_json(msg="adb not found in PATH. Please install Android platform-tools and ensure adb is available.", changed=False)

    try:
        from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import run_adb_command, AdbError
        current = _existing_forward(adb_path, device, local)

        if state == 'present':
            if current == remote:
                module.exit_json(changed=False, msg=f"forward already set: {local} -> {remote}")
            if check_mode:
                module.exit_json(changed=True, msg=f"would forward {local} -> {remote}")
            run_adb_command(adb_path, ["forward", local, remote], device=device)
            module.exit_json(changed=True, msg=f"Port forwarded: {local} -> {remote}")
        else:  # absent
            if current is None:
                module.exit_json(changed=False, msg=f"no forward for {local}")
            if check_mode:
                module.exit_json(changed=True, msg=f"would remove forward {local}")
            run_adb_command(adb_path, ["forward", "--remove", local], device=device)
            module.exit_json(changed=True, msg=f"Forward removed: {local}")
    except AdbError as e:
        module.fail_json(msg=f"ADB error: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {e}", changed=False)


if __name__ == '__main__':
    main()
