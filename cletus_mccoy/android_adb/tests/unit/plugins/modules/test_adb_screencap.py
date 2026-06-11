import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_screencap


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


PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def run_module(params, png_bytes):
    module = DummyModule(dict({'adb_path': 'adb', 'device': None}, **params))
    with patch.object(adb_screencap, 'run_adb_binary', return_value=png_bytes):
        adb_screencap.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_screencap.main()
        except SystemExit:
            pass
    return module.result


def test_writes_png(tmp_path):
    dest = tmp_path / "shot.png"
    res = run_module({'dest': str(dest)}, PNG)
    assert res['changed'] is True
    assert res['size'] == len(PNG)
    assert dest.read_bytes() == PNG


def test_non_png_fails(tmp_path):
    dest = tmp_path / "shot.png"
    res = run_module({'dest': str(dest)}, b"not a png")
    assert res.get('failed') is True
    assert not dest.exists()
