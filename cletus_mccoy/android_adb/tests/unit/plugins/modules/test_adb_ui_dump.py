import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_ui_dump


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


SAMPLE = ('<hierarchy rotation="0">'
          '<node text="OK" resource-id="id/ok" content-desc="" class="android.widget.Button" '
          'package="p" clickable="true" bounds="[10,20][30,40]" />'
          '</hierarchy>')


def run_module(params):
    module = DummyModule(dict({'adb_path': 'adb', 'device': None, 'dest': None,
                               'dump_path': '/sdcard/window_dump.xml'}, **params))
    with patch.object(adb_ui_dump, 'dump_ui', return_value=SAMPLE):
        adb_ui_dump.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_ui_dump.main()
        except SystemExit:
            pass
    return module.result


def test_returns_nodes():
    res = run_module({})
    assert res['changed'] is False
    assert res['xml'] == SAMPLE
    assert len(res['nodes']) == 1
    assert res['nodes'][0]['center'] == (20, 30)


def test_saves_to_dest(tmp_path):
    dest = tmp_path / "ui.xml"
    res = run_module({'dest': str(dest)})
    assert dest.read_text() == SAMPLE
