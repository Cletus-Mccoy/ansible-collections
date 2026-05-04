import subprocess
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.parsing import parse_getprop

def get_property(adb_path, key, device=None):
    cmd = [adb_path]
    if device:
        cmd += ["-s", device]
    cmd += ["shell", f"getprop {key}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()

def set_property(adb_path, key, value, device=None):
    cmd = [adb_path]
    if device:
        cmd += ["-s", device]
    cmd += ["shell", f"setprop {key} '{value}'"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return True

def backup_properties(adb_path, backup_path, device=None):
    cmd = [adb_path]
    if device:
        cmd += ["-s", device]
    cmd += ["shell", "getprop"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(result.stdout)
    return True

def validate_property(adb_path, key, expected_value, device=None):
    actual = get_property(adb_path, key, device=device)
    return actual == expected_value
