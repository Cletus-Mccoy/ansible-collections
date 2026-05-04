DOCUMENTATION = r'''
---
module: adb_pair
short_description: Pair with an Android device over ADB wirelessly
description:
  - Initiates wireless ADB pairing with an Android device.
options:
  ip:
    description:
      - IP address of the device to pair with.
    required: true
    type: str
  port:
    description:
      - Pairing port of the device.
    required: true
    type: int
  pairing_code:
    description:
      - Pairing code shown on the device (if required).
    required: false
    type: str
author:
  - Kasper Daems
version_added: '1.1.0'
'''  # noqa

EXAMPLES = r'''
- name: Pair with device
  adb_pair:
    ip: 192.168.1.100
    port: 12345
    pairing_code: "123456"
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
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import shutil

def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type="str", required=True),
            port=dict(type="int", required=True),
            pairing_code=dict(type="str", required=False),
        ),
        supports_check_mode=False,
    )

    adb_path = shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH")

    ip = module.params["ip"]
    port = module.params["port"]
    pairing_code = module.params.get("pairing_code")

    cmd = [adb_path, "pair", f"{ip}:{port}"]
    try:
        if pairing_code:
            # Send pairing code via stdin
            proc = subprocess.run(cmd, input=pairing_code + "\n", capture_output=True, text=True, timeout=10)
        else:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0 and "Successfully paired" in proc.stdout:
            module.exit_json(changed=True, msg=proc.stdout.strip())
        elif "Enter pairing code" in proc.stdout and not pairing_code:
            module.fail_json(msg="Pairing code required. Please provide pairing_code parameter.")
        else:
            module.fail_json(msg=proc.stdout + proc.stderr)
    except Exception as e:
        module.fail_json(msg=str(e))

def main():
    run_module()

if __name__ == "__main__":
    main()
