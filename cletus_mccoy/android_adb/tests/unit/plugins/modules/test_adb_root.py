import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_root


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
        self.result['failed'] = True
        raise SystemExit


def run_module(params, run_side_effect):
    module = DummyModule(
        dict({'adb_path': 'adb', 'state': 'root', 'device': None,
              'reconnect': True, 'prune_stale': True, 'reconnect_timeout': 10},
             **params),
        check_mode=params.pop('_check_mode', False),
    )
    with patch('subprocess.run', side_effect=run_side_effect):
        adb_root.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_root.main()
        except SystemExit:
            pass
    return module.result


def test_already_root_no_change():
    res = run_module(
        {'state': 'root'},
        [DummyResult(stdout='adbd is already running as root')],
    )
    assert res['changed'] is False
    assert res['root_state'] == 'root'


def test_restart_as_root_no_device():
    res = run_module(
        {'state': 'root'},
        [DummyResult(stdout='restarting adbd as root')],
    )
    assert res['changed'] is True
    assert res['reconnected'] is False


def test_disabled_by_system_setting_fails():
    res = run_module(
        {'state': 'root'},
        [DummyResult(stdout='ADB Root access is disabled by system setting')],
    )
    assert res.get('failed') is True
    assert 'disabled' in res['msg'].lower()


def test_unroot_already_non_root():
    res = run_module(
        {'state': 'unroot'},
        [DummyResult(stdout='adbd not running as root')],
    )
    assert res['changed'] is False
    assert res['root_state'] == 'unroot'


def test_wireless_reconnect_and_prune():
    devices = ("List of devices attached\n"
               "192.168.1.50:5555\tdevice\n"
               "192.168.1.50:41000\toffline\n")
    res = run_module(
        {'state': 'root', 'device': '192.168.1.50:5555'},
        [
            DummyResult(stdout='restarting adbd as root'),       # adb root
            DummyResult(stdout='connected to 192.168.1.50:5555'),  # adb connect
            DummyResult(stdout=devices),                           # adb devices (prune scan)
            DummyResult(stdout='disconnected'),                    # adb disconnect stale
        ],
    )
    assert res['changed'] is True
    assert res['reconnected'] is True
    assert res['pruned'] == ['192.168.1.50:41000']
