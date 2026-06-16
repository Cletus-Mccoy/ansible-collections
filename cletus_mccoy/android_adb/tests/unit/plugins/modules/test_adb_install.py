import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_install
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


def run_module(params, dumpsys_output='', install_output='Success', check_mode=False):
    module = DummyModule(dict({'package': None, 'version': None, 'device': None, 'adb_path': 'adb'}, **params),
                         check_mode=check_mode)

    def fake_run_adb(adb_path, args, device=None, timeout=30, server_port=None):
        if args[0] == 'shell' and args[1].startswith('dumpsys'):
            return dumpsys_output
        return install_output

    with patch.object(adbmod, 'run_adb_command', side_effect=fake_run_adb):
        adb_install.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        try:
            adb_install.main()
        except SystemExit:
            pass
    return module.result


def test_module_doc():
    assert hasattr(adb_install, 'DOCUMENTATION')
    assert hasattr(adb_install, 'EXAMPLES')
    assert hasattr(adb_install, 'RETURN')


def test_install_without_package_always_installs():
    res = run_module({'apk_path': '/tmp/app.apk'})
    assert res['changed'] is True


def test_skip_when_version_matches():
    res = run_module(
        {'apk_path': '/tmp/app.apk', 'package': 'com.example.app', 'version': '2.3.0'},
        dumpsys_output='Package [com.example.app]\n    versionName=2.3.0\n',
    )
    assert res['changed'] is False
    assert res['installed_version'] == '2.3.0'


def test_install_when_version_differs():
    res = run_module(
        {'apk_path': '/tmp/app.apk', 'package': 'com.example.app', 'version': '2.3.0'},
        dumpsys_output='Package [com.example.app]\n    versionName=2.2.0\n',
    )
    assert res['changed'] is True


def test_skip_when_present_and_no_version_requested():
    res = run_module(
        {'apk_path': '/tmp/app.apk', 'package': 'com.example.app'},
        dumpsys_output='Package [com.example.app]\n    versionName=1.0\n',
    )
    assert res['changed'] is False


def test_install_when_not_present():
    res = run_module(
        {'apk_path': '/tmp/app.apk', 'package': 'com.example.app'},
        dumpsys_output='Unable to find package: com.example.app',
    )
    assert res['changed'] is True
