import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_uninstall

def test_module_doc():
    assert hasattr(adb_uninstall, 'DOCUMENTATION')
    assert hasattr(adb_uninstall, 'EXAMPLES')
    assert hasattr(adb_uninstall, 'RETURN')

def test_main_runs():
    class DummyModule:
        def __init__(self):
            self.params = {'package': 'com.example.app'}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_uninstall.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        adb_uninstall.main()
    except SystemExit:
        pass
    assert module.result['changed'] is False
    assert module.result['msg'] == 'Not implemented'
