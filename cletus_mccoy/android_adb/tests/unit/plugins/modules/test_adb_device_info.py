import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_device_info

class DummyModule:
    def __init__(self):
        self.params = {"device": None}
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

def test_run_module(monkeypatch):
    # Patch adb_shell to return fake outputs
    def fake_adb_shell(adb_path, command, device=None):
        if command == "getprop":
            return "[ro.product.model]: [Pixel 5]"
        if command == "dumpsys battery":
            return "level: 85\nstatus: 2"
        if command == "df /data":
            return "/data 1000000 500000 500000 50% /data"
        if command == "ip addr show":
            return "2: wlan0: ..."
        return ""
    monkeypatch.setattr(adb_device_info, "adb_shell", fake_adb_shell)
    monkeypatch.setattr(adb_device_info.shutil, "which", lambda x: "/usr/bin/adb")
    monkeypatch.setattr(adb_device_info, "parse_getprop", lambda x: {"ro.product.model": "Pixel 5"})
    monkeypatch.setattr(adb_device_info, "extract_device_info", lambda props: {"model": props["ro.product.model"]})
    module = DummyModule()
    # Patch AnsibleModule to DummyModule
    monkeypatch.setattr(adb_device_info, "AnsibleModule", lambda **kwargs: module)
    assert hasattr(adb_device_info, "main")
    try:
        adb_device_info.main()
    except SystemExit:
        pass
    assert module.result is not None
    assert module.result["android_device_info"]["model"] == "Pixel 5"
    assert "battery" in module.result["android_device_info"]
    assert "storage" in module.result["android_device_info"]
    assert "network" in module.result["android_device_info"]
