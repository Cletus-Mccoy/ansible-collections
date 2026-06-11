import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_connect


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


def run_module(params, run_side_effect):
    module = DummyModule(dict({'adb_path': 'adb'}, **params),
                         check_mode=params.pop('_check_mode', False))
    with patch('subprocess.run', side_effect=run_side_effect):
        adb_connect.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_connect.main()
        except SystemExit:
            pass
    return module.result


DEVICES_CONNECTED = "List of devices attached\n192.168.1.100:37011\tdevice\n"
DEVICES_EMPTY = "List of devices attached\n"


def test_present_already_connected_no_change():
    res = run_module(
        {'ip': '192.168.1.100', 'port': 37011, 'state': 'present'},
        run_side_effect=[DummyResult(stdout=DEVICES_CONNECTED)],
    )
    assert res['changed'] is False


def test_present_connects_when_absent():
    res = run_module(
        {'ip': '192.168.1.100', 'port': 37011, 'state': 'present'},
        run_side_effect=[
            DummyResult(stdout=DEVICES_EMPTY),
            DummyResult(stdout='connected to 192.168.1.100:37011'),
        ],
    )
    assert res['changed'] is True


def test_absent_no_change_when_not_connected():
    res = run_module(
        {'ip': '192.168.1.100', 'port': 37011, 'state': 'absent'},
        run_side_effect=[DummyResult(stdout=DEVICES_EMPTY)],
    )
    assert res['changed'] is False


def test_absent_disconnects_when_connected():
    res = run_module(
        {'ip': '192.168.1.100', 'port': 37011, 'state': 'absent'},
        run_side_effect=[
            DummyResult(stdout=DEVICES_CONNECTED),
            DummyResult(stdout='disconnected 192.168.1.100:37011'),
        ],
    )
    assert res['changed'] is True


DEVICES_WITH_STALE = (
    "List of devices attached\n"
    "192.168.1.100:37011\tdevice\n"
    "192.168.1.100:41999\toffline\n"
)


def test_prune_offline_when_already_connected():
    res = run_module(
        {'ip': '192.168.1.100', 'port': 37011, 'state': 'present',
         'prune_offline': True},
        run_side_effect=[
            DummyResult(stdout=DEVICES_WITH_STALE),  # _is_connected
            DummyResult(stdout=DEVICES_WITH_STALE),  # _offline_serials
            DummyResult(stdout='disconnected'),       # disconnect stale
        ],
    )
    assert res['pruned'] == ['192.168.1.100:41999']
    assert res['changed'] is True


def test_prune_offline_none_to_prune():
    res = run_module(
        {'ip': '192.168.1.100', 'port': 37011, 'state': 'present',
         'prune_offline': True},
        run_side_effect=[
            DummyResult(stdout=DEVICES_CONNECTED),  # _is_connected
            DummyResult(stdout=DEVICES_CONNECTED),  # _offline_serials (none)
        ],
    )
    assert res['pruned'] == []
    assert res['changed'] is False
