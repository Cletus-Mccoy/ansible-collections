import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_uninstall


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


def run_module(params, list_output, uninstall_output='Success', check_mode=False):
    module = DummyModule(dict({'device': None, 'adb_path': 'adb', 'keep_data': False}, **params),
                         check_mode=check_mode)

    def fake_run_adb(adb_path, args, device=None, timeout=30, server_port=None):
        if args[0] == 'shell':
            return list_output
        return uninstall_output

    # patch the lazily-imported helpers at their source module
    import ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb as adbmod
    with patch.object(adbmod, 'run_adb_command', side_effect=fake_run_adb):
        adb_uninstall.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_uninstall.main()
        except SystemExit:
            pass
    return module.result


def test_module_doc():
    assert hasattr(adb_uninstall, 'DOCUMENTATION')
    assert hasattr(adb_uninstall, 'EXAMPLES')
    assert hasattr(adb_uninstall, 'RETURN')


def test_no_change_when_not_installed():
    res = run_module({'package': 'com.example.app'}, list_output='')
    assert res['changed'] is False


def test_uninstalls_when_installed():
    res = run_module({'package': 'com.example.app'},
                     list_output='package:com.example.app\n')
    assert res['changed'] is True


def test_check_mode_no_write():
    res = run_module({'package': 'com.example.app'},
                     list_output='package:com.example.app\n', check_mode=True)
    assert res['changed'] is True
    assert 'would uninstall' in res['msg']
