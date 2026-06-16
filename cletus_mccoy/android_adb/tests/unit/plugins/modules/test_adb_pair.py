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
            self.result = None
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise Exception(kwargs["msg"])
    module = DummyModule()
    try:
        adb_pair.main.__globals__["AnsibleModule"] = lambda **kwargs: module
        assert hasattr(adb_pair, "main")
        adb_pair.main()
    except SystemExit:
        pass
    assert hasattr(module, "result")
    assert module.result is not None
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
            self.result = None
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_pair.main.__globals__["AnsibleModule"] = lambda **kwargs: module
        assert hasattr(adb_pair, "main")
        adb_pair.main()
    except SystemExit:
        pass
    assert hasattr(module, "result")
    assert module.result is not None
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
            self.result = None
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_pair.main.__globals__["AnsibleModule"] = lambda **kwargs: module
        assert hasattr(adb_pair, "main")
        adb_pair.main()
    except SystemExit:
        pass
    assert hasattr(module, "result")
    assert module.result is not None
    assert "Failed to pair" in module.result["msg"]


class _Mod:
    def __init__(self, params):
        self.params = params
        self.result = None

    def exit_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit

    def fail_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit


def _run(monkeypatch, params, run_side_effect):
    from importlib import import_module
    adb_pair = import_module(MODULE_PATH)
    monkeypatch.setattr(subprocess, "run", run_side_effect)
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    module = _Mod(params)
    adb_pair.main.__globals__["AnsibleModule"] = lambda **kwargs: module
    try:
        adb_pair.main()
    except SystemExit:
        pass
    return module.result


def test_expired_window_retries_and_reports(monkeypatch):
    calls = {"n": 0}

    def run(cmd, input=None, capture_output=True, text=True, timeout=15):
        calls["n"] += 1
        return DummyResult(stdout="", stderr="failed to connect to 1.2.3.4:5", returncode=1)

    res = _run(
        monkeypatch,
        {"ip": "1.2.3.4", "port": 5, "pairing_code": "111111",
         "retries": 2, "retry_delay": 0, "timeout": 15, "adb_path": "adb"},
        run,
    )
    assert res["expired"] is True
    assert res["attempts"] == 3          # initial + 2 retries
    assert calls["n"] == 3
    assert "reopen Wireless debugging" in res["msg"]


def test_wrong_code_does_not_retry(monkeypatch):
    calls = {"n": 0}

    def run(cmd, input=None, capture_output=True, text=True, timeout=15):
        calls["n"] += 1
        return DummyResult(stdout="Failed: wrong pairing code\n", returncode=1)

    res = _run(
        monkeypatch,
        {"ip": "1.2.3.4", "port": 5, "pairing_code": "000000",
         "retries": 5, "retry_delay": 0, "timeout": 15, "adb_path": "adb"},
        run,
    )
    assert res["expired"] is False
    assert res["attempts"] == 1          # no retries on a non-transient failure
    assert calls["n"] == 1


def test_timeout_is_treated_as_expired(monkeypatch):
    def run(cmd, input=None, capture_output=True, text=True, timeout=15):
        raise subprocess.TimeoutExpired(cmd="adb", timeout=timeout)

    res = _run(
        monkeypatch,
        {"ip": "1.2.3.4", "port": 5, "pairing_code": "111111",
         "retries": 1, "retry_delay": 0, "timeout": 15, "adb_path": "adb"},
        run,
    )
    assert res["expired"] is True
    assert res["attempts"] == 2
