
DOCUMENTATION = r'''
---
module: adb_screenrecord
short_description: Record Android device screen via ADB
short_description: Record the screen of an Android device using ADB.
description:
  - Records the screen of an Android device using ADB and saves it to a specified path on the host.
options:
  path:
    description:
      - Path on the host to save the recorded screen.
    required: true
    type: str
  duration:
    description:
      - Duration of the screen recording in seconds.
    required: false
    type: int
    default: 10
author:
  - Kasper Daems
version_added: '1.2.0'
'''

EXAMPLES = r'''
- name: Record screen for 10 seconds
  adb_screenrecord:
    path: /tmp/screenrecord.mp4
    duration: 10
'''

RETURN = r'''
changed:
  description: Whether the screen was recorded
  type: bool
  returned: always
msg:
  description: Informational message
  type: str
  returned: always
'''


from ansible.module_utils.basic import AnsibleModule
import shutil
import os
import tempfile

def main():
  module = AnsibleModule(
      argument_spec=dict(
          path=dict(type='str', required=True),
          duration=dict(type='int', default=10),
          device=dict(type='str', required=False, default=None),
          adb_path=dict(type='str', required=False, default='adb'),
      )
  )

  path = module.params['path']
  duration = module.params['duration']
  device = module.params['device']
  adb_path = module.params['adb_path'] or shutil.which('adb')
  if not adb_path:
      module.fail_json(msg="adb not found in PATH. Please install Android platform-tools and ensure adb is available.")
  if not path:
      module.fail_json(msg="path is required.")
  if duration is not None and (not isinstance(duration, int) or duration <= 0):
      module.fail_json(msg="duration must be a positive integer.")

  # Use a temp file on the device
  remote_tmp = f"/data/local/tmp/screenrecord_{os.getpid()}.mp4"
  try:
      from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell, adb_pull, run_adb_command, AdbError

      # Record the screen
      shell_cmd = f"screenrecord --time-limit={duration} {remote_tmp}"
      adb_shell(adb_path, shell_cmd, device=device)

      # Pull the file to the host
      adb_pull(adb_path, remote_tmp, path, device=device)

      # Clean up the remote file
      try:
          adb_shell(adb_path, f"rm {remote_tmp}", device=device)
      except Exception:
          pass

      module.exit_json(changed=True, msg=f"Screen recorded to {path}")
  except AdbError as e:
      module.fail_json(msg=f"ADB error: {e}")
  except Exception as e:
      module.fail_json(msg=f"Unexpected error: {e}")

if __name__ == '__main__':
  main()


