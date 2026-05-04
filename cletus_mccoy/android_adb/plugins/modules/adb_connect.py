DOCUMENTATION = r'''
---
module: adb_connect
short_description: Connect to an Android device over ADB (wireless)
description:
  - Connects to an Android device using ADB connect (for wireless debugging).
options:
  ip:
    description:
      - IP address of the device to connect to.
    required: true
    type: str
  port:
    description:
      - Connect port of the device (shown on device screen).
    required: true
    type: int
author:
  - Kasper Daems
version_added: '1.3.0'
'''

EXAMPLES = r'''
- name: Connect to device
  adb_connect:
    ip: 192.168.1.100
    port: 37011
'''

RETURN = r'''
changed:
  description: Whether connection was performed.
  returned: always
  type: bool
msg:
  description: Result message.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import shutil

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type="str", required=True),
            port=dict(type="int", required=True),
        ),
        supports_check_mode=False,
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH")

    ip = module.params["ip"]
    port = module.params["port"]

    cmd = [adb_path, "connect", f"{ip}:{port}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0 and ("connected to" in proc.stdout or "already connected" in proc.stdout):
            module.exit_json(changed=True, msg=proc.stdout.strip())
        else:
            module.fail_json(msg=proc.stdout + proc.stderr)
    except Exception as e:
        module.fail_json(msg=str(e))

def main():
    run_module()

if __name__ == "__main__":
    main()
