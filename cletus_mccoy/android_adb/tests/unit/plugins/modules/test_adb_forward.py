import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_forward
import ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb as adbmod


class DummyModule:
    def __init__(self, params, check_mode=False):
        self.params = params
        self.check_mode = check_mode
        self.result = None

    def exit_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit

    def fail_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit


def run_module(params, list_output, check_mode=False):
    module = DummyModule(
        dict({'remote': None, 'state': 'present', 'device': None, 'adb_path': 'adb'}, **params),
        check_mode=check_mode,
    )

    def fake_run_adb(adb_path, args, device=None, timeout=30):
        if args[:2] == ['forward', '--list']:
            return list_output
        return ''

    with patch.object(adbmod, 'run_adb_command', side_effect=fake_run_adb):
        adb_forward.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_forward.main()
        except SystemExit:
            pass
    return module.result


def test_module_doc():
    assert hasattr(adb_forward, 'DOCUMENTATION')
    assert hasattr(adb_forward, 'EXAMPLES')
    assert hasattr(adb_forward, 'RETURN')


def test_present_creates_when_absent():
    res = run_module({'local': 'tcp:8000', 'remote': 'tcp:8000'}, list_output='')
    assert res['changed'] is True


def test_present_idempotent_when_exists():
    res = run_module({'local': 'tcp:8000', 'remote': 'tcp:8000'},
                     list_output='emulator-5554 tcp:8000 tcp:8000\n')
    assert res['changed'] is False


def test_absent_removes_when_present():
    res = run_module({'local': 'tcp:8000', 'state': 'absent'},
                     list_output='emulator-5554 tcp:8000 tcp:8000\n')
    assert res['changed'] is True


def test_absent_idempotent_when_missing():
    res = run_module({'local': 'tcp:8000', 'state': 'absent'}, list_output='')
    assert res['changed'] is False
