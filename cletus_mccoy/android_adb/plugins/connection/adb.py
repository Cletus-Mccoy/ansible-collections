from ansible.plugins.connection import ConnectionBase
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
import subprocess
import shutil


DOCUMENTATION = r'''
connection: adb
short_description: Execute Ansible tasks over Android Debug Bridge (ADB)
description:
  - Connects to Android devices using adb shell commands.
  - Allows execution of commands, file transfer via push/pull.
author:
  - Kasper Daems
'''


class Connection(ConnectionBase):
    """
    ADB connection plugin for Ansible
    """
    transport = "adb"
    has_pipelining = False

    def _connect(self):
        """
        Establish "connection" via adb
        """
        self._adb_path = shutil.which("adb")

        if not self._adb_path:
            raise AnsibleConnectionFailure("adb not found in PATH")

        # inventory_hostname = device serial or IP
        self._device = self._play_context.remote_addr

        if not self._device:
            raise AnsibleConnectionFailure(
                "No device specified (inventory_hostname is required)"
            )

        # Mark connection as active (IMPORTANT for Ansible)
        self._connected = True

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """
        Execute a shell command on Android device
        """
        if isinstance(cmd, (list, tuple)):
            cmd = " ".join(cmd)

        full_cmd = [self._adb_path]

        if self._device:
            full_cmd += ["-s", self._device]

        full_cmd += ["shell", cmd]

        result = subprocess.run(full_cmd, capture_output=True, text=True)

        return result.returncode, result.stdout, result.stderr

    def put_file(self, in_path, out_path):
        """
        Copy file to device
        """
        cmd = [self._adb_path]

        if self._device:
            cmd += ["-s", self._device]

        cmd += ["push", in_path, out_path]

        subprocess.check_call(cmd)

    def fetch_file(self, in_path, out_path):
        """
        Copy file from device
        """
        cmd = [self._adb_path]

        if self._device:
            cmd += ["-s", self._device]

        cmd += ["pull", in_path, out_path]

        subprocess.check_call(cmd)

    def close(self):
        """
        Cleanup connection (ADB is stateless, so nothing needed)
        """
        self._connected = False