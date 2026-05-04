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
