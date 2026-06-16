import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_facts


class DummyModule:
    def __init__(self, params):
        self.params = params
        self.result = None
        self.failed = False

    def exit_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit

    def fail_json(self, **kwargs):
        self.failed = True
        self.result = kwargs
        raise SystemExit


def run_module(monkeypatch, params, probe_state, shell_map=None):
    full = dict(
        device="192.168.1.5:5555",
        connect=False,
        connect_timeout=5,
        command_timeout=30,
        gather_subset=["min"],
        fail_on_unreachable=False,
        ensure_server=True,
        adb_path="adb",
    )
    full.update(params)
    module = DummyModule(full)

    monkeypatch.setattr(adb_facts, "AnsibleModule", lambda **kw: module)
    monkeypatch.setattr(adb_facts.shutil, "which", lambda x: "/usr/bin/adb")
    monkeypatch.setattr(adb_facts, "adb_ensure_server",
                        lambda *a, **k: {"restarted": False, "responsive": True})
    monkeypatch.setattr(adb_facts, "probe_device", lambda *a, **k: probe_state)

    shell_map = shell_map or {}

    def fake_shell(adb_path, cmd, device=None, timeout=30, server_port=None):
        return shell_map.get(cmd, "")

    monkeypatch.setattr(adb_facts, "adb_shell", fake_shell)

    try:
        adb_facts.main()
    except SystemExit:
        pass
    return module


def test_unreachable_skips_cleanly(monkeypatch):
    m = run_module(monkeypatch, {}, probe_state="unreachable")
    assert m.failed is False
    facts = m.result["ansible_facts"]["android"]
    assert facts["reachable"] is False
    assert facts["state"] == "unreachable"
    assert m.result["changed"] is False


def test_unreachable_can_fail(monkeypatch):
    m = run_module(monkeypatch, {"fail_on_unreachable": True}, probe_state="offline")
    assert m.failed is True
    assert m.result["ansible_facts"]["android"]["reachable"] is False


def test_reachable_gathers_min_facts(monkeypatch):
    getprop = (
        "[ro.product.model]: [Pixel 5]\n"
        "[ro.product.manufacturer]: [Google]\n"
        "[ro.build.version.release]: [14]\n"
        "[ro.build.version.sdk]: [34]\n"
    )
    m = run_module(
        monkeypatch, {}, probe_state="device",
        shell_map={"getprop": getprop, "dumpsys power": "mWakefulness=Asleep"},
    )
    assert m.failed is False
    facts = m.result["ansible_facts"]["android"]
    assert facts["reachable"] is True
    assert facts["model"] == "Pixel 5"
    assert facts["manufacturer"] == "Google"
    assert facts["android_version"] == "14"
    assert facts["sdk"] == "34"
    assert facts["awake"] is False


def test_root_subset_detects_root(monkeypatch):
    m = run_module(
        monkeypatch, {"gather_subset": ["min", "root"]}, probe_state="device",
        shell_map={"getprop": "[ro.product.model]: [X]",
                   "id": "uid=0(root) gid=0(root)"},
    )
    facts = m.result["ansible_facts"]["android"]
    assert facts["adbd_root"] is True
    assert facts["rooted"] is True


def test_packages_subset(monkeypatch):
    m = run_module(
        monkeypatch, {"gather_subset": ["packages"]}, probe_state="device",
        shell_map={"getprop": "", "dumpsys power": "",
                   "pm list packages -3": "package:com.example.one\npackage:com.example.two"},
    )
    facts = m.result["ansible_facts"]["android"]
    assert facts["installed_apps"] == ["com.example.one", "com.example.two"]
