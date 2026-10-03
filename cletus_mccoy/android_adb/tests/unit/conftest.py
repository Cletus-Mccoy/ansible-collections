from __future__ import absolute_import, division, print_function
__metaclass__ = type

import sys
import os
# Add the parent directory of ansible_collections to sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

import shutil

import pytest


@pytest.fixture(autouse=True)
def _adb_on_path(monkeypatch):
    """Pretend adb is installed so module tests don't depend on the host (CI has no adb)."""
    real_which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name, *a, **kw: "/usr/bin/adb" if name == "adb" else real_which(name, *a, **kw))
