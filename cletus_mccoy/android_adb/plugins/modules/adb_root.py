#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to toggle adb root / unroot and re-establish the connection

DOCUMENTATION = r'''
---
module: adb_root
short_description: Restart adbd as root (or non-root) and re-establish the connection
description:
  - Runs C(adb root) or C(adb unroot) to restart C(adbd) on the device with or
    without root privileges.
  - On userdebug / eng builds (including most phh-Treble GSIs) this is the
    reliable root path for ADB — more so than C(su), which on those builds often
    competes with the platform C(su) and is denied without prompting. Prefer this
    module over running C(su -c) inside C(adb_shell).
  - "C(adb root)/C(adb unroot) drop the current ADB transport, so a wireless
    (C(IP:port)) connection goes away and the stale entry lingers as C(offline)
    in C(adb devices). When O(reconnect=true) (the default) and O(device) is an
    C(IP:port), this module reconnects afterwards and (with O(prune_stale=true))
    disconnects any leftover C(offline) entries."
  - Idempotent on the basis of adbd's own report — when adbd is already in the
    requested mode the device says so and the module returns C(changed=false).
options:
  state:
    description:
      - C(root) restarts adbd as root; C(unroot) restarts it as the regular shell user.
    required: false
    type: str
    choices: [root, unroot]
    default: root
  device:
    description:
      - Device serial or C(IP:port) to target. If an C(IP:port) is given it is
        also used as the reconnect target.
    required: false
    type: str
  reconnect:
    description:
      - After toggling, reconnect to O(device) when it looks like an C(IP:port).
        Has no effect for USB serials.
    required: false
    type: bool
    default: true
  prune_stale:
    description:
      - When reconnecting, C(adb disconnect) any entries left in the C(offline)
        state (typically the stale transport the toggle just dropped).
    required: false
    type: bool
    default: true
  reconnect_timeout:
    description:
      - Seconds to keep retrying C(adb connect) while adbd restarts.
    required: false
    type: int
    default: 10
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
- name: Restart adbd as root on a wireless device and reconnect
  cletus_mccoy.android_adb.adb_root:
    device: 192.168.1.50:5555

- name: Drop back to non-root
  cletus_mccoy.android_adb.adb_root:
    device: 192.168.1.50:5555
    state: unroot
'''

RETURN = r'''
changed:
  description: Whether adbd's root state was changed.
  returned: always
  type: bool
root_state:
  description: The resulting state as reported by the device (C(root) or C(unroot)).
  returned: success
  type: str
reconnected:
  description: Whether the module reconnected to the device afterwards.
  returned: success
  type: bool
pruned:
  description: Stale C(offline) entries that were disconnected.
  returned: success
  type: list
  elements: str
msg:
  description: The raw adb output that the result was derived from.
  returned: always
  type: str
'''

import re
import shutil
import subprocess
import time

from ansible.module_utils.basic import AnsibleModule

# device looks like an IP:port (or host:port) wireless target rather than a serial
_HOSTPORT_RE = re.compile(r"^[^\s]+:\d+$")


def _run(adb_path, args, device=None, timeout=15):
    cmd = [adb_path]
    if device:
        cmd += ["-s", device]
    cmd += args
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def _classify(state, out):
    """Map adb root/unroot output to (changed, root_state, fatal_msg)."""
    low = out.lower()
    if "disabled by system setting" in low:
        return None, None, (
            "ADB root is disabled by a system setting. On userdebug builds enable "
            "Developer options -> 'Rooted debugging' (or set the appropriate "
            "ro.adb.* / persist.adb.* gate); on production builds adbd cannot run "
            "as root at all. Raw: %s" % out
        )
    if "cannot run as root in production builds" in low or "production builds" in low:
        return None, None, (
            "adbd cannot run as root on this (production) build. Raw: %s" % out
        )
    if state == "root":
        if "already running as root" in low:
            return False, "root", None
        if "restarting adbd as root" in low:
            return True, "root", None
    else:  # unroot
        if "not running as root" in low:
            return False, "unroot", None
        if "restarting adbd as non root" in low or "restarting adbd as nonroot" in low:
            return True, "unroot", None
    # Unrecognised but non-fatal output — assume the toggle took effect.
    return True, state, None


def _offline_serials(adb_path):
    proc = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=10)
    offline = []
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if "\t" not in line:
            continue
        serial, dev_state = (p.strip() for p in line.split("\t", 1))
        if dev_state == "offline":
            offline.append(serial)
    return offline


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", default="root", choices=["root", "unroot"]),
            device=dict(type="str", required=False, default=None),
            reconnect=dict(type="bool", required=False, default=True),
            prune_stale=dict(type="bool", required=False, default=True),
            reconnect_timeout=dict(type="int", required=False, default=10),
            adb_path=dict(type="str", required=False, default=None),
        ),
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    state = module.params["state"]
    device = module.params["device"]
    is_wireless = bool(device) and _HOSTPORT_RE.match(device) is not None

    if module.check_mode:
        module.exit_json(changed=True, msg="would run 'adb %s'" % state,
                         root_state=state, reconnected=False, pruned=[])

    try:
        _, out = _run(adb_path, [state], device=device)
        changed, root_state, fatal = _classify(state, out)
        if fatal:
            module.fail_json(msg=fatal, changed=False)

        reconnected = False
        pruned = []
        if changed and module.params["reconnect"] and is_wireless:
            # adbd is restarting; retry connect until the transport is back.
            deadline = time.time() + max(1, module.params["reconnect_timeout"])
            last = ""
            while time.time() < deadline:
                rc, last = _run(adb_path, ["connect", device], timeout=10)
                if rc == 0 and ("connected to" in last or "already connected" in last):
                    reconnected = True
                    break
                time.sleep(0.5)

            if module.params["prune_stale"]:
                for serial in _offline_serials(adb_path):
                    subprocess.run([adb_path, "disconnect", serial],
                                   capture_output=True, text=True, timeout=10)
                    pruned.append(serial)

            if not reconnected:
                module.fail_json(
                    msg="toggled adb %s but could not reconnect to %s: %s"
                        % (state, device, last),
                    changed=changed, root_state=root_state, pruned=pruned,
                )

        module.exit_json(changed=changed, root_state=root_state,
                         reconnected=reconnected, pruned=pruned, msg=out)
    except subprocess.TimeoutExpired as e:
        module.fail_json(msg="adb timed out: %s" % e, changed=False)
    except Exception as e:
        module.fail_json(msg="Unexpected error: %s" % e, changed=False)


if __name__ == "__main__":
    main()
