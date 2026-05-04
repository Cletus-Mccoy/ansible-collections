import pytest
from unittest.mock import patch
import subprocess

MODULE_PATH = "ansible_collections.cletus_mccoy.android_adb.plugins.modules.adb_pair"

class DummyResult:
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

def test_pair_success(monkeypatch):
    # Simulate successful pairing
    def dummy_run(cmd, input=None, capture_output=True, text=True, timeout=10):
        return DummyResult(stdout="Successfully paired to 192.168.1.100:12345\n", returncode=0)
    monkeypatch.setattr(subprocess, "run", dummy_run)
    from importlib import import_module
    adb_pair = import_module(MODULE_PATH)
    # Patch AnsibleModule to simulate parameters and capture exit_json
    class DummyModule:
        def __init__(self):
            self.params = {"ip": "192.168.1.100", "port": 12345, "pairing_code": "123456"}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            raise Exception(kwargs["msg"])
    module = DummyModule()
    try:
        adb_pair.run_module.__globals__["AnsibleModule"] = lambda **_: module
        adb_pair.run_module()
    except SystemExit:
        pass
    assert module.result["changed"] is True
    assert "Successfully paired" in module.result["msg"]

def test_pair_code_required(monkeypatch):
    # Simulate prompt for pairing code
    def dummy_run(cmd, input=None, capture_output=True, text=True, timeout=10):
        return DummyResult(stdout="Enter pairing code: ", returncode=1)
    monkeypatch.setattr(subprocess, "run", dummy_run)
    from importlib import import_module
    adb_pair = import_module(MODULE_PATH)
    class DummyModule:
        def __init__(self):
            self.params = {"ip": "192.168.1.100", "port": 12345}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_pair.run_module.__globals__["AnsibleModule"] = lambda **_: module
        adb_pair.run_module()
    except SystemExit:
        pass
    assert "Pairing code required" in module.result["msg"]

def test_pair_failure(monkeypatch):
    # Simulate failure
    def dummy_run(cmd, input=None, capture_output=True, text=True, timeout=10):
        return DummyResult(stdout="Failed to pair\n", returncode=1)
    monkeypatch.setattr(subprocess, "run", dummy_run)
    from importlib import import_module
    adb_pair = import_module(MODULE_PATH)
    class DummyModule:
        def __init__(self):
            self.params = {"ip": "192.168.1.100", "port": 12345, "pairing_code": "badcode"}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_pair.run_module.__globals__["AnsibleModule"] = lambda **_: module
        adb_pair.run_module()
    except SystemExit:
        pass
    assert "Failed to pair" in module.result["msg"]
