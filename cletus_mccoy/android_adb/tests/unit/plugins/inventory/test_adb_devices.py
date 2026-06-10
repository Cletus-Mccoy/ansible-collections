import pytest
from unittest.mock import patch

pytest.importorskip("ansible.plugins.inventory")

from ansible_collections.cletus_mccoy.android_adb.plugins.inventory import adb_devices


DEVICES_OUTPUT = (
    "List of devices attached\n"
    "emulator-5554          device product:sdk model:Android_SDK\n"
    "192.168.1.50:5555      device product:clock model:MiClock\n"
    "1234567890             unauthorized\n"
)


def make_module():
    # Bypass __init__ machinery; we only test helper methods.
    return adb_devices.InventoryModule.__new__(adb_devices.InventoryModule)


def test_list_devices_parses_serials_and_state():
    mod = make_module()
    with patch.object(adb_devices.subprocess, 'run') as run:
        run.return_value = type('R', (), {'returncode': 0, 'stdout': DEVICES_OUTPUT, 'stderr': ''})()
        devices = mod._list_devices('adb')
    assert ('emulator-5554', 'device') in devices
    assert ('192.168.1.50:5555', 'device') in devices
    assert ('1234567890', 'unauthorized') in devices


def test_sanitize_group_name():
    assert adb_devices.InventoryModule._sanitize_group_name('Google Pixel 7') == 'google_pixel_7'
    assert adb_devices.InventoryModule._sanitize_group_name('Xiaomi/Redmi') == 'xiaomi_redmi'


def test_verify_file_suffix():
    mod = make_module()
    with patch('ansible.plugins.inventory.BaseInventoryPlugin.verify_file', return_value=True):
        assert mod.verify_file('/some/path/adb_devices.yml')
        assert not mod.verify_file('/some/path/hosts.ini')
