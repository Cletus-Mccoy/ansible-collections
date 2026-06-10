import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_settings


class DummyResult:
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class DummyModule:
    def __init__(self, params, check_mode=False):
        self.params = params
        self.check_mode = check_mode

    def exit_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit

    def fail_json(self, **kwargs):
        self.result = kwargs
        raise SystemExit


def run_module(params, current_value, check_mode=False):
    """Run adb_settings.main() with subprocess.run mocked.

    ``current_value`` is what 'settings get' returns first; subsequent puts/deletes
    return empty success.
    """
    module = DummyModule(dict({'device': None, 'value': None, 'adb_path': 'adb'}, **params),
                         check_mode=check_mode)
    call_outputs = iter([DummyResult(stdout=current_value)])

    def fake_run(cmd, *args, **kwargs):
        try:
            return next(call_outputs)
        except StopIteration:
            return DummyResult(stdout='')

    with patch('subprocess.run', side_effect=fake_run):
        adb_settings.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_settings.main()
        except SystemExit:
            pass
    return module.result


def test_doc_blocks():
    assert hasattr(adb_settings, 'DOCUMENTATION')
    assert hasattr(adb_settings, 'EXAMPLES')
    assert hasattr(adb_settings, 'RETURN')


def test_present_no_change_when_equal():
    res = run_module(
        {'namespace': 'system', 'key': 'screen_off_timeout', 'value': '600000', 'state': 'present'},
        current_value='600000\n',
    )
    assert res['changed'] is False
    assert res['previous_value'] == '600000'


def test_present_changes_when_different():
    res = run_module(
        {'namespace': 'system', 'key': 'screen_off_timeout', 'value': '600000', 'state': 'present'},
        current_value='30000\n',
    )
    assert res['changed'] is True
    assert res['previous_value'] == '30000'
    assert res['value'] == '600000'


def test_present_changes_when_unset():
    res = run_module(
        {'namespace': 'system', 'key': 'new_key', 'value': '1', 'state': 'present'},
        current_value='null\n',
    )
    assert res['changed'] is True
    assert res['previous_value'] is None


def test_absent_no_change_when_unset():
    res = run_module(
        {'namespace': 'system', 'key': 'gone', 'state': 'absent'},
        current_value='null\n',
    )
    assert res['changed'] is False


def test_absent_changes_when_set():
    res = run_module(
        {'namespace': 'system', 'key': 'flag', 'state': 'absent'},
        current_value='1\n',
    )
    assert res['changed'] is True
    assert res['previous_value'] == '1'


def test_read_returns_value():
    res = run_module(
        {'namespace': 'secure', 'key': 'location_mode', 'state': 'read'},
        current_value='3\n',
    )
    assert res['changed'] is False
    assert res['value'] == '3'


def test_check_mode_does_not_write():
    res = run_module(
        {'namespace': 'system', 'key': 'screen_off_timeout', 'value': '600000', 'state': 'present'},
        current_value='30000\n',
        check_mode=True,
    )
    assert res['changed'] is True
