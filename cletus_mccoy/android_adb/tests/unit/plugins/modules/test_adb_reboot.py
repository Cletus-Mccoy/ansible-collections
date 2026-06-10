import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_reboot
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


def run_module(params, run_adb=None, check_mode=False):
    module = DummyModule(
        dict({'mode': 'normal', 'wait': False, 'wait_timeout': 180,
              'device': None, 'adb_path': 'adb'}, **params),
        check_mode=check_mode,
    )
    run_adb = run_adb or (lambda *a, **k: 'rebooting')
    with patch.object(adbmod, 'run_adb_command', side_effect=run_adb), \
            patch('time.sleep', return_value=None):
        adb_reboot.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_reboot.main()
        except SystemExit:
            pass
    return module.result


def test_module_doc():
    assert hasattr(adb_reboot, 'DOCUMENTATION')
    assert hasattr(adb_reboot, 'EXAMPLES')
    assert hasattr(adb_reboot, 'RETURN')


def test_reboot_changed():
    res = run_module({'mode': 'normal'})
    assert res['changed'] is True


def test_check_mode():
    res = run_module({'mode': 'normal'}, check_mode=True)
    assert res['changed'] is True
    assert 'would reboot' in res['msg']


def test_wait_for_boot_success():
    def run_adb(adb_path, args, device=None, timeout=30):
        if args[:1] == ['shell']:
            return '1'
        return 'ok'
    res = run_module({'mode': 'normal', 'wait': True, 'wait_timeout': 30}, run_adb=run_adb)
    assert res['changed'] is True
    assert 'finished booting' in res['msg']
