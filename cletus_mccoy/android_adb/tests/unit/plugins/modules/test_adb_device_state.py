import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_device_state

class DummyModule:
    def __init__(self, state):
        self.params = {"device": None, "state": state}
        self.failed = False
        self.msg = None
        self.result = None
    def fail_json(self, msg):
        self.failed = True
        self.msg = msg
        raise Exception(msg)
    def exit_json(self, **kwargs):
        self.result = kwargs
        return kwargs

def test_run_module_reboot(monkeypatch):
    monkeypatch.setattr(adb_device_state, "adb_shell", lambda adb_path, cmd, device=None: None)
    monkeypatch.setattr(adb_device_state.shutil, "which", lambda x: "/usr/bin/adb")
    monkeypatch.setattr(adb_device_state, "AnsibleModule", lambda **kwargs: DummyModule("reboot"))
    module = DummyModule("reboot")
    monkeypatch.setattr(adb_device_state, "AnsibleModule", lambda **kwargs: module)
    adb_device_state.run_module()
    assert module.result["changed"] is True
    assert "reboot" in module.result["msg"]

def test_run_module_shutdown(monkeypatch):
    monkeypatch.setattr(adb_device_state, "adb_shell", lambda adb_path, cmd, device=None: None)
    monkeypatch.setattr(adb_device_state.shutil, "which", lambda x: "/usr/bin/adb")
    monkeypatch.setattr(adb_device_state, "AnsibleModule", lambda **kwargs: DummyModule("shutdown"))
    module = DummyModule("shutdown")
    monkeypatch.setattr(adb_device_state, "AnsibleModule", lambda **kwargs: module)
    adb_device_state.run_module()
    assert module.result["changed"] is True
    assert "shutdown" in module.result["msg"]
