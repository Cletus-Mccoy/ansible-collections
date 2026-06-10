import os
import tempfile
import pytest
from unittest.mock import patch
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils import config

class DummyResult:
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

def test_get_property_success():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='Pixel 7\n')
        val = config.get_property('/usr/bin/adb', 'ro.product.model', device=None)
        assert val == 'Pixel 7'

def test_set_property_success():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult()
        changed = config.set_property('/usr/bin/adb', 'persist.sys.locale', 'en-US', device=None)
        assert changed is True

def test_backup_properties_success():
    with patch('subprocess.run') as run, tempfile.NamedTemporaryFile(delete=False) as tf:
        run.return_value = DummyResult(stdout='[ro.product.model]: [Pixel 7]\n')
        config.backup_properties('/usr/bin/adb', tf.name, device=None)
        with open(tf.name) as f:
            assert '[ro.product.model]' in f.read()
        os.unlink(tf.name)

def test_validate_property_true():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='Pixel 7\n')
        assert config.validate_property('/usr/bin/adb', 'ro.product.model', 'Pixel 7', device=None)

def test_validate_property_false():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='Pixel 6\n')
        assert not config.validate_property('/usr/bin/adb', 'ro.product.model', 'Pixel 7', device=None)


# --- idempotency helpers --------------------------------------------------
def test_set_property_idempotent_no_change():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='en-US\n')
        changed, prev = config.set_property_idempotent('/usr/bin/adb', 'persist.sys.locale', 'en-US')
        assert changed is False
        assert prev == 'en-US'
        # only the getprop read happened, no setprop write
        assert run.call_count == 1


def test_set_property_idempotent_changes():
    with patch('subprocess.run') as run:
        run.side_effect = [DummyResult(stdout='en-GB\n'), DummyResult()]
        changed, prev = config.set_property_idempotent('/usr/bin/adb', 'persist.sys.locale', 'en-US')
        assert changed is True
        assert prev == 'en-GB'
        assert run.call_count == 2


def test_settings_get_returns_none_when_null():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='null\n')
        assert config.settings_get('/usr/bin/adb', 'system', 'missing') is None


def test_settings_set_idempotent_no_change():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='600000\n')
        changed, prev = config.settings_set_idempotent('/usr/bin/adb', 'system', 'screen_off_timeout', '600000')
        assert changed is False
        assert run.call_count == 1


def test_settings_set_idempotent_changes():
    with patch('subprocess.run') as run:
        run.side_effect = [DummyResult(stdout='30000\n'), DummyResult()]
        changed, prev = config.settings_set_idempotent('/usr/bin/adb', 'system', 'screen_off_timeout', '600000')
        assert changed is True
        assert prev == '30000'


def test_settings_delete_idempotent_no_change_when_unset():
    with patch('subprocess.run') as run:
        run.return_value = DummyResult(stdout='null\n')
        changed, prev = config.settings_delete_idempotent('/usr/bin/adb', 'system', 'flag')
        assert changed is False
        assert run.call_count == 1


def test_settings_delete_idempotent_deletes_when_set():
    with patch('subprocess.run') as run:
        run.side_effect = [DummyResult(stdout='1\n'), DummyResult()]
        changed, prev = config.settings_delete_idempotent('/usr/bin/adb', 'system', 'flag')
        assert changed is True
        assert prev == '1'
