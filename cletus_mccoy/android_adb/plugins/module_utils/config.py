"""Helpers for reading/writing Android configuration.

Two distinct subsystems are covered here:

* **System properties** (``getprop`` / ``setprop``) — kernel/build/runtime
  properties. Writing most ``ro.*`` properties or ``persist.*`` requires root.
* **Settings database** (``settings get|put|delete <namespace> <key>``) — the
  user-facing settings most device configuration lives in. ``system`` and
  ``global`` are writable by the ADB shell user; ``secure`` requires the
  ``WRITE_SECURE_SETTINGS`` permission granted to an app.

All helpers route through :func:`run_adb_command` so error handling, timeouts
and device targeting are consistent across the collection, and they raise
:class:`AdbError` (not ``RuntimeError``) on failure.
"""

from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
    run_adb_command,
)
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.parsing import (
    parse_getprop,  # noqa: F401  (re-exported for backwards compatibility)
)

# ``settings get`` prints this literal string when a key is unset.
SETTINGS_NULL = "null"


# --------------------------------------------------------------------------
# Settings database (settings get/put/delete)
# --------------------------------------------------------------------------
def settings_get(adb_path, namespace, key, device=None):
    """Return the current value of a settings key, or ``None`` if unset."""
    value = run_adb_command(
        adb_path, ["shell", "settings", "get", namespace, key], device=device
    )
    if value == SETTINGS_NULL or value == "":
        return None
    return value


def settings_put(adb_path, namespace, key, value, device=None):
    """Write a settings value. Returns ``True`` (raises on failure)."""
    run_adb_command(
        adb_path,
        ["shell", "settings", "put", namespace, key, str(value)],
        device=device,
    )
    return True


def settings_delete(adb_path, namespace, key, device=None):
    """Delete a settings key. Returns ``True`` (raises on failure)."""
    run_adb_command(
        adb_path, ["shell", "settings", "delete", namespace, key], device=device
    )
    return True


def settings_set_idempotent(adb_path, namespace, key, value, device=None, check_mode=False):
    """Set a settings value only if it differs from the current one.

    Returns ``(changed, previous_value)``. In check mode no write occurs but
    ``changed`` still reflects what *would* happen.
    """
    current = settings_get(adb_path, namespace, key, device=device)
    if current == str(value):
        return False, current
    if not check_mode:
        settings_put(adb_path, namespace, key, value, device=device)
    return True, current


def settings_delete_idempotent(adb_path, namespace, key, device=None, check_mode=False):
    """Delete a settings key only if it is currently set.

    Returns ``(changed, previous_value)``.
    """
    current = settings_get(adb_path, namespace, key, device=device)
    if current is None:
        return False, None
    if not check_mode:
        settings_delete(adb_path, namespace, key, device=device)
    return True, current


# --------------------------------------------------------------------------
# System properties (getprop/setprop)
# --------------------------------------------------------------------------
def get_property(adb_path, key, device=None):
    """Return a single system property value."""
    return run_adb_command(
        adb_path, ["shell", "getprop", key], device=device
    )


def set_property(adb_path, key, value, device=None):
    """Write a system property. Returns ``True`` (raises on failure)."""
    run_adb_command(
        adb_path, ["shell", "setprop", key, str(value)], device=device
    )
    return True


def set_property_idempotent(adb_path, key, value, device=None, check_mode=False):
    """Set a property only if it differs. Returns ``(changed, previous_value)``."""
    current = get_property(adb_path, key, device=device)
    if current == str(value):
        return False, current
    if not check_mode:
        set_property(adb_path, key, value, device=device)
    return True, current


def backup_properties(adb_path, backup_path, device=None):
    """Dump all system properties to a local file."""
    output = run_adb_command(adb_path, ["shell", "getprop"], device=device)
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(output)
    return True


def validate_property(adb_path, key, expected_value, device=None):
    """Return True if a property currently equals ``expected_value``."""
    return get_property(adb_path, key, device=device) == expected_value
