import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_install

def test_module_doc():
    assert hasattr(adb_install, 'DOCUMENTATION')
    assert hasattr(adb_install, 'EXAMPLES')
    assert hasattr(adb_install, 'RETURN')

def test_main_runs():
    class DummyModule:
        def __init__(self):
            self.params = {'apk_path': '/tmp/app.apk'}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_install.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        adb_install.main()
    except SystemExit:
        pass
    assert module.result['changed'] is False
    assert module.result['msg'] == 'Not implemented'
