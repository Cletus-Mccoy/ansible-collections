import pytest
from ansible_collections.cletus_mccoy.android_adb.plugins.modules import adb_screenrecord

def test_module_doc():
    assert hasattr(adb_screenrecord, 'DOCUMENTATION')
    assert hasattr(adb_screenrecord, 'EXAMPLES')
    assert hasattr(adb_screenrecord, 'RETURN')

def test_main_runs():
    class DummyModule:
        def __init__(self):
            self.params = {'path': '/sdcard/demo.mp4', 'duration': 10}
        def exit_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
        def fail_json(self, **kwargs):
            self.result = kwargs
            raise SystemExit
    module = DummyModule()
    try:
        adb_screenrecord.main.__globals__['AnsibleModule'] = lambda **kwargs: module
        adb_screenrecord.main()
    except SystemExit:
        pass
    assert module.result['changed'] is False
    assert module.result['msg'] == 'Not implemented'
