import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_ui_tap


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
          '<node text="OK" resource-id="id/ok" content-desc="" class="b" '
          'package="p" clickable="true" bounds="[100,200][300,260]" />'
          '<node text="Dup" resource-id="id/d" content-desc="" class="b" '
          'package="p" clickable="true" bounds="[0,0][10,10]" />'
          '<node text="Dup" resource-id="id/d" content-desc="" class="b" '
          'package="p" clickable="true" bounds="[20,20][40,40]" />'
          '</hierarchy>')


def run_module(params):
    module = DummyModule(dict(
        {'adb_path': 'adb', 'device': None, 'text': None, 'resource_id': None,
         'content_desc': None, 'x': None, 'y': None, 'index': 0}, **params))
    calls = []

    def fake_run(adb_path, args, device=None, timeout=30):
        calls.append(args)
        return ''

    with patch.object(adb_ui_tap, 'dump_ui', return_value=SAMPLE), \
         patch.object(adb_ui_tap, 'run_adb_command', side_effect=fake_run):
        adb_ui_tap.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_ui_tap.main()
        except SystemExit:
            pass
    module.result['_calls'] = calls
    return module.result


def test_tap_by_text():
    res = run_module({'text': 'OK'})
    assert res['changed'] is True
    assert (res['x'], res['y']) == (200, 230)
    assert res['_calls'][-1] == ['shell', 'input', 'tap', '200', '230']


def test_tap_by_coords_skips_dump():
    res = run_module({'x': 540, 'y': 1200})
    assert (res['x'], res['y']) == (540, 1200)
    assert res['matched'] == 0
    assert res['_calls'][-1] == ['shell', 'input', 'tap', '540', '1200']


def test_no_match_fails():
    res = run_module({'text': 'Nope'})
    assert res.get('failed') is True


def test_index_selects_match():
    res = run_module({'text': 'Dup', 'index': 1})
    assert (res['x'], res['y']) == (30, 30)


def test_index_out_of_range_fails():
    res = run_module({'text': 'Dup', 'index': 5})
    assert res.get('failed') is True
    assert 'out of range' in res['msg']
