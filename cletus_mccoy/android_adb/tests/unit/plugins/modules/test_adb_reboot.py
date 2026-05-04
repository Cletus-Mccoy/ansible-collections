import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_reboot

def test_module_doc():
    assert hasattr(adb_reboot, 'DOCUMENTATION')
    assert hasattr(adb_reboot, 'EXAMPLES')
    assert hasattr(adb_reboot, 'RETURN')

def test_main_runs():
    # Should exit with changed=False and msg='Not implemented'
    # Simulate AnsibleModule with default args
    class DummyModule:
        def __init__(self):
            self.params = {'mode': 'normal'}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_reboot.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        adb_reboot.main()
    except SystemExit:
        pass
    assert module.result['changed'] is False
    assert module.result['msg'] == 'Not implemented'
