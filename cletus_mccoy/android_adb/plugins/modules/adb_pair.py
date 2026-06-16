DOCUMENTATION = r'''
---
module: adb_pair
short_description: Pair with an Android device over ADB wirelessly
description:
  - Initiates wireless ADB pairing with an Android device (Android 11+).
  - The pairing dialog (Wireless debugging → Pair device with pairing code) shows
    a code and port that B(time out) after a short window and must be held open on
    the device. This module retries within a bounded window and returns a clear,
    actionable message when the window has expired, so a run can be resumed by
    reopening the dialog rather than failing opaquely.
options:
  ip:
    description:
      - IP address of the device to pair with.
    required: true
    type: str
  port:
    description:
      - Pairing port of the device (shown in the pairing dialog).
    required: true
    type: int
  pairing_code:
    description:
      - Pairing code shown on the device.
    required: false
    type: str
  retries:
    description:
      - Number of additional attempts if pairing fails transiently (e.g. the
        device is still bringing the dialog up). Each attempt is bounded by
        O(timeout).
    required: false
    type: int
    default: 2
  retry_delay:
    description:
      - Seconds to wait between attempts.
    required: false
    type: int
    default: 2
  timeout:
    description:
      - Per-attempt timeout (seconds) for the C(adb pair) call.
    required: false
    type: int
    default: 15
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
  adb_server_port:
    description:
      - Pair using a dedicated ADB server on this port (C(adb -P <port>)) instead
        of the shared C(tcp:5037) server, for per-device isolation.
    required: false
    type: int
author:
  - Kasper Daems
version_added: '1.1.0'
'''  # noqa

EXAMPLES = r'''
- name: Pair with device (retries within the pairing window)
  cletus_mccoy.android_adb.adb_pair:
    ip: 192.168.1.100
    port: 37123
    pairing_code: "123456"
    retries: 3
'''

RETURN = r'''
changed:
  description: Whether pairing was performed.
  returned: always
  type: bool
msg:
  description: Result message.
  returned: always
  type: str
attempts:
  description: How many attempts were made.
  returned: always
  type: int
expired:
  description: True when the failure looks like an expired/closed pairing dialog (reopen it and retry).
  returned: on failure
  type: bool
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import shutil
import time


# Substrings in adb's output that indicate the pairing window is gone (rather
# than a wrong code), so the operator should reopen the dialog and resume.
_EXPIRED_MARKERS = (
    "failed to connect",
    "connection refused",
    "timed out",
    "no route to host",
    "cannot connect",
)


def _looks_expired(text):
    low = (text or "").lower()
    return any(m in low for m in _EXPIRED_MARKERS)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type="str", required=True),
            port=dict(type="int", required=True),
            pairing_code=dict(type="str", required=False),
            retries=dict(type="int", required=False, default=2),
            retry_delay=dict(type="int", required=False, default=2),
            timeout=dict(type="int", required=False, default=15),
            adb_path=dict(type="str", required=False, default=None),
            adb_server_port=dict(type="int", required=False, default=None),
        ),
        supports_check_mode=False,
    )

    adb_path = module.params.get("adb_path") or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    ip = module.params["ip"]
    port = module.params["port"]
    pairing_code = module.params.get("pairing_code")
    retries = max(0, module.params.get("retries") or 0)
    retry_delay = module.params.get("retry_delay") or 0
    timeout = module.params.get("timeout") or 15
    server_port = module.params.get("adb_server_port")

    base = [adb_path]
    if server_port:
        base += ["-P", str(server_port)]
    cmd = base + ["pair", f"{ip}:{port}"]

    attempts = 0
    last_out = ""
    last_expired = False
    for attempt in range(retries + 1):
        attempts = attempt + 1
        try:
            if pairing_code:
                proc = subprocess.run(cmd, input=pairing_code + "\n",
                                      capture_output=True, text=True, timeout=timeout)
            else:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last_out = "adb pair timed out after %ss" % timeout
            last_expired = True
            if attempt < retries:
                time.sleep(retry_delay)
            continue

        out = (proc.stdout or "") + (proc.stderr or "")
        last_out = out.strip()

        if proc.returncode == 0 and "Successfully paired" in proc.stdout:
            module.exit_json(changed=True, msg=proc.stdout.strip(), attempts=attempts)

        if "Enter pairing code" in proc.stdout and not pairing_code:
            module.fail_json(
                msg="Pairing code required. Provide the pairing_code parameter.",
                changed=False, attempts=attempts, expired=False,
            )

        last_expired = _looks_expired(out)
        # Retry only when it looks like a transient/expired-window condition.
        if last_expired and attempt < retries:
            time.sleep(retry_delay)
            continue
        # A non-expired failure (e.g. wrong code) won't improve with retries.
        if not last_expired:
            break

    if last_expired:
        module.fail_json(
            msg="Pairing failed: the pairing dialog appears to have expired or "
                "closed (after %d attempt(s)). On the device, reopen Wireless "
                "debugging → Pair device with pairing code to get a fresh code "
                "and port, then re-run. Last output: %s" % (attempts, last_out),
            changed=False, attempts=attempts, expired=True,
        )
    module.fail_json(msg=last_out or "adb pair failed", changed=False,
                     attempts=attempts, expired=False)


if __name__ == "__main__":
    main()
