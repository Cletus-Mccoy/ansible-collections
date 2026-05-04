import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_forward

def test_module_doc():
    assert hasattr(adb_forward, 'DOCUMENTATION')
    assert hasattr(adb_forward, 'EXAMPLES')
    assert hasattr(adb_forward, 'RETURN')

def test_main_runs():
    class DummyModule:
        def __init__(self):
            self.params = {'local': 'tcp:8000', 'remote': 'tcp:8000'}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_forward.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        adb_forward.main()
    except SystemExit:
        pass
    assert module.result['changed'] is False
    assert module.result['msg'] == 'Not implemented'
