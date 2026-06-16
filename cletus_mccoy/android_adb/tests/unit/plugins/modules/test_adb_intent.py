import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_intent
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


def run_module(params, shell_output='Starting: Intent', check_mode=False):
    module = DummyModule(
        dict({'device': None, 'command': 'start', 'action': None, 'data': None,
              'component': None, 'mime_type': None, 'category': None,
              'extras': None, 'adb_path': 'adb'}, **params),
        check_mode=check_mode,
    )
    captured = {}

    def fake_run_adb(adb_path, args, device=None, timeout=30, server_port=None):
        captured['args'] = args
        return shell_output

    with patch.object(adbmod, 'run_adb_command', side_effect=fake_run_adb):
        adb_intent.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_intent.main()
        except SystemExit:
            pass
    return module.result, captured


def test_docs():
    assert hasattr(adb_intent, 'DOCUMENTATION')
    assert hasattr(adb_intent, 'EXAMPLES')
    assert hasattr(adb_intent, 'RETURN')


def test_build_am_args_view_url():
    args = adb_intent._build_am_args({
        'command': 'start', 'action': 'android.intent.action.VIEW',
        'data': 'https://example.com', 'component': None, 'mime_type': None,
        'category': None, 'extras': None,
    })
    assert args == ['am', 'start', '-a', 'android.intent.action.VIEW', '-d', 'https://example.com']


def test_extras_rendered():
    args = adb_intent._build_am_args({
        'command': 'broadcast', 'action': 'com.example.ACTION', 'data': None,
        'component': None, 'mime_type': None, 'category': None,
        'extras': {'mode': 'full'},
    })
    assert '--es' in args and 'mode' in args and 'full' in args


def test_start_succeeds():
    res, captured = run_module({'action': 'android.intent.action.VIEW', 'data': 'https://x'})
    assert res['changed'] is True
    assert captured['args'][0] == 'shell'


def test_error_marker_fails():
    res, _ = run_module({'component': 'com.x/.Y'}, shell_output='Error: Activity not started')
    assert 'msg' in res and 'failed' in res['msg'].lower()


def test_check_mode():
    res, _ = run_module({'action': 'a'}, check_mode=True)
    assert res['changed'] is True
    assert 'would run' in res['msg']
