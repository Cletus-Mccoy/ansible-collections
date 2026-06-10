# Unit test for adb_files Ansible module
import pytest
import os
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import adb_push, adb_pull


def test_adb_push_runs(monkeypatch, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    def fake_run_adb_command(adb_path, args, device=None, timeout=30):
        assert adb_path == 'adb'
        assert args == ['push', str(test_file), '/data/local/tmp/test.txt']
        return 'pushed'
    monkeypatch.setattr('ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb.run_adb_command', fake_run_adb_command)
    output = adb_push('adb', str(test_file), "/data/local/tmp/test.txt")
    assert output == "pushed"


def test_adb_pull_runs(monkeypatch):
    def fake_run_adb_command(adb_path, args, device=None, timeout=30):
        assert adb_path == 'adb'
        assert args == ['pull', '/data/local/tmp/test.txt', './localcopy.txt']
        return 'pulled'
    monkeypatch.setattr('ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb.run_adb_command', fake_run_adb_command)
    output = adb_pull('adb', "/data/local/tmp/test.txt", "./localcopy.txt")
    assert output == "pulled"
