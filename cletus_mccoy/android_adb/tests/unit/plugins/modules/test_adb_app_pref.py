import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_app_pref


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


PREFS = "/data/data/de.ozerov.fully/shared_prefs/de.ozerov.fully_preferences.xml"


def make_xml(body):
    return ("<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
            "<map>\n%s\n</map>" % body)


def make_reader(xml, listing="de.ozerov.fully_preferences.xml", exists="Y"):
    def fake(adb_path, args, device=None, timeout=30):
        if args[0] == 'shell' and len(args) >= 2 and args[1] == 'cat':
            return xml
        joined = ' '.join(args[1:])
        if joined.startswith('ls '):
            return listing
        if '[ -f' in joined:
            return exists
        return ''
    return fake


def run_module(params, reader, recorder):
    module = DummyModule(
        dict({'adb_path': 'adb', 'type': 'string', 'file': None,
              'state': 'present', 'device': None, 'value': None}, **params),
    )
    with patch.object(adb_app_pref, 'run_adb_command', side_effect=reader), \
         patch.object(adb_app_pref, '_write_back', side_effect=recorder):
        adb_app_pref.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_app_pref.main()
        except SystemExit:
            pass
    return module.result


def test_present_idempotent_no_write():
    xml = make_xml('<boolean name="remoteAdmin" value="true" />')
    written = []
    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdmin', 'type': 'boolean',
         'value': 'true', 'file': 'de.ozerov.fully_preferences.xml'},
        make_reader(xml), lambda *a, **k: written.append(a[-2]),
    )
    assert res['changed'] is False
    assert written == []


def test_present_changes_value():
    xml = make_xml('<boolean name="remoteAdmin" value="false" />')
    written = []

    def recorder(module, adb_path, prefs, content, device=None):
        written.append(content)

    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdmin', 'type': 'boolean',
         'value': 'true', 'file': 'de.ozerov.fully_preferences.xml'},
        make_reader(xml), recorder,
    )
    assert res['changed'] is True
    assert res['previous_value'] == 'false'
    assert 'value="true"' in written[0]


def test_present_adds_new_string_key():
    xml = make_xml('<int name="other" value="1" />')
    written = []

    def recorder(module, adb_path, prefs, content, device=None):
        written.append(content)

    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdminPassword',
         'type': 'string', 'value': 'hunter2',
         'file': 'de.ozerov.fully_preferences.xml'},
        make_reader(xml), recorder,
    )
    assert res['changed'] is True
    assert res['previous_value'] is None
    assert '<string name="remoteAdminPassword">hunter2</string>' in written[0]


def test_absent_removes_key():
    xml = make_xml('<boolean name="remoteAdmin" value="true" />')
    written = []

    def recorder(module, adb_path, prefs, content, device=None):
        written.append(content)

    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdmin', 'state': 'absent',
         'file': 'de.ozerov.fully_preferences.xml'},
        make_reader(xml), recorder,
    )
    assert res['changed'] is True
    assert 'remoteAdmin' not in written[0]


def test_absent_missing_key_no_change():
    xml = make_xml('<int name="other" value="1" />')
    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdmin', 'state': 'absent',
         'file': 'de.ozerov.fully_preferences.xml'},
        make_reader(xml), lambda *a, **k: None,
    )
    assert res['changed'] is False


def test_autodetect_single_file():
    xml = make_xml('<boolean name="remoteAdmin" value="true" />')
    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdmin', 'type': 'boolean',
         'value': 'true'},
        make_reader(xml, listing='de.ozerov.fully_preferences.xml'),
        lambda *a, **k: None,
    )
    assert res['changed'] is False
    assert res['file'].endswith('de.ozerov.fully_preferences.xml')


def test_multiple_files_requires_file():
    xml = make_xml('<boolean name="remoteAdmin" value="true" />')
    res = run_module(
        {'package': 'de.ozerov.fully', 'key': 'remoteAdmin', 'type': 'boolean',
         'value': 'true'},
        make_reader(xml, listing='a.xml b.xml'),
        lambda *a, **k: None,
    )
    assert res.get('failed') is True
    assert 'specify' in res['msg']
