# Unit test for adb_shell Ansible module
import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_shell

def test_adb_shell_runs(monkeypatch):
    def fake_run_adb_command(adb_path, args, device=None, timeout=30, server_port=None):
        assert adb_path == 'adb'
        assert args == ['shell', 'echo hello']
        return 'hello'
    monkeypatch.setattr('ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb.run_adb_command', fake_run_adb_command)
    output = adb_shell('adb', 'echo hello')
    assert output == 'hello'
