DOCUMENTATION = r'''
---
module: adb_connect
short_description: Connect to (or disconnect from) an Android device over ADB (wireless)
description:
  - Manages a wireless ADB connection to an Android device using C(adb connect)
    and C(adb disconnect).
  - Idempotent. When O(state=present) and the device is already connected, the
    module reports C(changed=false). When O(state=absent) and the device is not
    connected, it also reports C(changed=false).
options:
  ip:
    description:
      - IP address of the device to connect to.
    required: true
    type: str
  port:
    description:
      - Connect port of the device (shown on device screen for wireless debugging).
    required: true
    type: int
  state:
    description:
      - C(present) ensures the device is connected; C(absent) disconnects it.
    required: false
    type: str
    choices: [present, absent]
    default: present
  prune_offline:
    description:
      - Before connecting, C(adb disconnect) any entries currently in the
        C(offline) state. These stale transports are commonly left behind after
        an C(adb root)/C(unroot)/C(tcpip) toggle and show up alongside the live
        device. Only applies when O(state=present).
    required: false
    type: bool
    default: false
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
author:
  - Kasper Daems
version_added: '1.3.0'
'''

EXAMPLES = r'''
- name: Connect to device
  cletus_mccoy.android_adb.adb_connect:
    ip: 192.168.1.100
    port: 37011

- name: Disconnect from device
  cletus_mccoy.android_adb.adb_connect:
    ip: 192.168.1.100
    port: 37011
    state: absent
'''

RETURN = r'''
changed:
  description: Whether the connection state was changed.
  returned: always
  type: bool
msg:
  description: Result message from adb.
  returned: always
  type: str
pruned:
  description: Stale C(offline) entries that were disconnected (when O(prune_offline=true)).
  returned: when prune_offline is true
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import shutil


def _is_connected(adb_path, target):
    """Return True if ``target`` (ip:port) shows as a device in ``adb devices``."""
    proc = subprocess.run(
        [adb_path, "devices"], capture_output=True, text=True, timeout=10
    )
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        serial = line.split()[0]
        state = line.split()[-1]
        if serial == target and state == "device":
            return True
    return False


def _offline_serials(adb_path):
    """Return serials currently shown as ``offline`` in ``adb devices``."""
    proc = subprocess.run(
        [adb_path, "devices"], capture_output=True, text=True, timeout=10
    )
    offline = []
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if "\t" not in line:
            continue
        serial, state = (p.strip() for p in line.split("\t", 1))
        if state == "offline":
            offline.append(serial)
    return offline


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type="str", required=True),
            port=dict(type="int", required=True),
            state=dict(type="str", required=False, default="present",
                       choices=["present", "absent"]),
            prune_offline=dict(type="bool", required=False, default=False),
            adb_path=dict(type="str", required=False, default=None),
        ),
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    ip = module.params["ip"]
    port = module.params["port"]
    state = module.params["state"]
    target = f"{ip}:{port}"

    try:
        already_connected = _is_connected(adb_path, target)

        if state == "present":
            pruned = []
            if module.params.get("prune_offline"):
                for serial in _offline_serials(adb_path):
                    if not module.check_mode:
                        subprocess.run([adb_path, "disconnect", serial],
                                       capture_output=True, text=True, timeout=10)
                    pruned.append(serial)

            if already_connected:
                module.exit_json(changed=bool(pruned),
                                 msg=f"already connected to {target}", pruned=pruned)
            if module.check_mode:
                module.exit_json(changed=True, msg=f"would connect to {target}",
                                 pruned=pruned)
            proc = subprocess.run(
                [adb_path, "connect", target],
                capture_output=True, text=True, timeout=10,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode == 0 and ("connected to" in proc.stdout or "already connected" in proc.stdout):
                module.exit_json(changed=True, msg=proc.stdout.strip(), pruned=pruned)
            module.fail_json(msg=out.strip() or "adb connect failed", changed=False,
                             pruned=pruned)
        else:  # absent
            if not already_connected:
                module.exit_json(changed=False, msg=f"{target} not connected")
            if module.check_mode:
                module.exit_json(changed=True, msg=f"would disconnect {target}")
            proc = subprocess.run(
                [adb_path, "disconnect", target],
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0:
                module.exit_json(changed=True, msg=proc.stdout.strip() or f"disconnected {target}")
            module.fail_json(msg=(proc.stdout + proc.stderr).strip(), changed=False)
    except Exception as e:
        module.fail_json(msg=str(e), changed=False)


if __name__ == "__main__":
    main()
