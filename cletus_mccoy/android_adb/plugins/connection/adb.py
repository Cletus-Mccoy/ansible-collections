from ansible.plugins.connection import ConnectionBase
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
import subprocess
import time
import shutil


DOCUMENTATION = r'''
connection: adb
short_description: Execute Ansible tasks over Android Debug Bridge (ADB)
description:
  - Connects to Android devices using adb shell commands.
  - Allows execution of commands and file transfer via push/pull.
author:
  - Kasper Daems
options:
  adb_command_timeout:
    description: Timeout (seconds) for individual adb commands.
    type: int
    default: 60
    vars:
      - name: ansible_adb_command_timeout
  adb_connect_retries:
    description: Number of times to retry a failed adb command before giving up.
    type: int
    default: 2
    vars:
      - name: ansible_adb_connect_retries
'''


class Connection(ConnectionBase):
    """ADB connection plugin for Ansible."""

    transport = "adb"
    has_pipelining = False

    def _connect(self):
        self._adb_path = shutil.which("adb")
        if not self._adb_path:
            raise AnsibleConnectionFailure("adb not found in PATH")

        # inventory_hostname = device serial or IP:port
        self._device = self._play_context.remote_addr
        if not self._device:
            raise AnsibleConnectionFailure(
                "No device specified (inventory_hostname is required)"
            )

        self._connected = True
        return self

    def _base_cmd(self):
        cmd = [self._adb_path]
        if self._device:
            cmd += ["-s", self._device]
        return cmd

    def _timeout(self):
        try:
            return int(self.get_option("adb_command_timeout"))
        except Exception:
            return 60

    def _retries(self):
        try:
            return max(0, int(self.get_option("adb_connect_retries")))
        except Exception:
            return 2

    def _run(self, cmd, in_data=None):
        """Run an adb command with timeout + retry. Returns CompletedProcess."""
        timeout = self._timeout()
        attempts = self._retries() + 1
        last_exc = None
        for attempt in range(attempts):
            try:
                return subprocess.run(
                    cmd,
                    input=in_data,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired as e:
                last_exc = e
            except OSError as e:
                last_exc = e
            if attempt < attempts - 1:
                time.sleep(1)
        raise AnsibleConnectionFailure(
            "adb command failed after %d attempt(s): %s (%s)"
            % (attempts, " ".join(cmd), to_text(last_exc))
        )

    def exec_command(self, cmd, in_data=None, sudoable=True):
        if isinstance(cmd, (list, tuple)):
            cmd = " ".join(cmd)

        full_cmd = self._base_cmd() + ["shell", cmd]
        result = self._run(full_cmd)
        return result.returncode, result.stdout, result.stderr

    def put_file(self, in_path, out_path):
        cmd = self._base_cmd() + ["push", in_path, out_path]
        result = self._run(cmd)
        if result.returncode != 0:
            raise AnsibleConnectionFailure(
                "Failed to push %s to %s: %s"
                % (in_path, out_path, result.stderr.strip() or result.stdout.strip())
            )

    def fetch_file(self, in_path, out_path):
        cmd = self._base_cmd() + ["pull", in_path, out_path]
        result = self._run(cmd)
        if result.returncode != 0:
            raise AnsibleConnectionFailure(
                "Failed to pull %s to %s: %s"
                % (in_path, out_path, result.stderr.strip() or result.stdout.strip())
            )

    def close(self):
        # ADB is stateless from our perspective; nothing to tear down.
        self._connected = False
