#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# Ansible module to set a key in an app's shared_prefs XML, context-preserving

DOCUMENTATION = r'''
---
module: adb_app_pref
short_description: Set or remove a key in an Android app's shared_prefs XML (root)
description:
  - Reads and writes a single key in an app's SharedPreferences file under
    C(/data/data/<package>/shared_prefs/), which is the only way to pre-seed
    remote-admin settings for apps like Fully Kiosk Browser over ADB.
  - "Requires root on the device (see M(cletus_mccoy.android_adb.adb_root)) — the
    shared_prefs directory is not readable by the regular ADB shell user."
  - "B(SELinux-safe by design.) A naive C(sed -i) rewrites the prefs file as a new
    inode, which loses the app's per-app MLS SELinux category and owner; the app
    then silently cannot read it and resets/crashes. This module preserves the
    original inode, owner and SELinux context by writing the new content back in
    place (C(cat tmp > prefs)) rather than replacing the file."
  - "B(No shell/YAML quoting traps.) Hand-rolling the edit as a folded C(sed)
    script in a task (e.g. a C(>-) block) is fragile: indented continuation lines
    keep real newlines, so C(adb shell) receives a broken multi-line script
    (C(-e: not found), then it tries to exec the XML path). This module never
    passes the value through the device shell — the new file is built on the
    controller and C(adb push)ed — so folding/escaping cannot corrupt it."
  - Idempotent — the file is only rewritten when the key's type or value actually
    changes.
options:
  package:
    description:
      - The app's package name (e.g. C(de.ozerov.fully)).
    required: true
    type: str
  key:
    description:
      - The SharedPreferences key name.
    required: true
    type: str
  value:
    description:
      - Desired value. Required when O(state=present). For O(type=boolean) accepts
        C(true)/C(false)/C(1)/C(0)/C(yes)/C(no).
    required: false
    type: str
  type:
    description:
      - The SharedPreferences value type to write.
    required: false
    type: str
    choices: [string, boolean, int, long, float]
    default: string
  file:
    description:
      - The shared_prefs XML filename (with or without C(.xml)). If omitted and
        the app has exactly one C(.xml) under C(shared_prefs/), that file is used;
        otherwise this is required.
    required: false
    type: str
  state:
    description:
      - C(present) ensures the key equals O(value); C(absent) removes the key.
    required: false
    type: str
    choices: [present, absent]
    default: present
  device:
    description:
      - Device serial or C(IP:port) to target.
    required: false
    type: str
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
author:
  - Kasper Daems
version_added: '0.3.0'
'''

EXAMPLES = r'''
- name: Enable Fully Kiosk remote admin
  cletus_mccoy.android_adb.adb_app_pref:
    package: de.ozerov.fully
    key: remoteAdmin
    type: boolean
    value: "true"

- name: Set the remote-admin password
  cletus_mccoy.android_adb.adb_app_pref:
    package: de.ozerov.fully
    key: remoteAdminPassword
    type: string
    value: "hunter2"

- name: Remove a key
  cletus_mccoy.android_adb.adb_app_pref:
    package: de.ozerov.fully
    key: oldFlag
    state: absent
'''

RETURN = r'''
changed:
  description: Whether the prefs file was rewritten.
  returned: always
  type: bool
file:
  description: The shared_prefs file that was operated on.
  returned: success
  type: str
previous_value:
  description: The value before the change (None if the key was unset).
  returned: success
  type: str
'''

import os
import shutil
import tempfile
import xml.etree.ElementTree as ET

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
    AdbError,
    run_adb_command,
    adb_push,
)

XML_DECL = "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}


def _shell(adb_path, cmd, device=None):
    return run_adb_command(adb_path, ["shell", cmd], device=device)


def _resolve_file(adb_path, package, fname, device=None):
    prefs_dir = "/data/data/%s/shared_prefs" % package
    if fname:
        if not fname.endswith(".xml"):
            fname += ".xml"
        return "%s/%s" % (prefs_dir, fname)
    # Auto-detect: exactly one .xml under shared_prefs/
    listing = _shell(adb_path, "ls %s 2>/dev/null" % prefs_dir, device=device)
    xmls = [n for n in listing.split() if n.endswith(".xml")]
    if len(xmls) == 1:
        return "%s/%s" % (prefs_dir, xmls[0])
    if not xmls:
        raise AdbError("no .xml found under %s (is the app installed and has it "
                       "been launched once?)" % prefs_dir)
    raise AdbError("multiple shared_prefs files under %s (%s); specify 'file'"
                   % (prefs_dir, ", ".join(xmls)))


def _read_prefs(adb_path, prefs, device=None):
    exists = _shell(adb_path, '[ -f "%s" ] && echo Y || echo N' % prefs, device=device)
    if exists.strip() != "Y":
        return None
    return run_adb_command(adb_path, ["shell", "cat", prefs], device=device)


def _normalize_bool(value):
    low = (value or "").strip().lower()
    if low in _TRUE:
        return "true"
    if low in _FALSE:
        return "false"
    raise AdbError("invalid boolean value %r (use true/false)" % value)


def _element_value(el):
    if el.tag == "string":
        return el.text or ""
    return el.get("value")


def _find(root, key):
    for el in list(root):
        if el.get("name") == key:
            return el
    return None


def _build_element(key, pref_type, value):
    el = ET.Element(pref_type)
    el.set("name", key)
    if pref_type == "string":
        el.text = value
    elif pref_type == "boolean":
        el.set("value", _normalize_bool(value))
    else:
        el.set("value", value)
    return el


def _desired_value(pref_type, value):
    if pref_type == "boolean":
        return _normalize_bool(value)
    return value


def _serialize(root):
    return XML_DECL + ET.tostring(root, encoding="unicode")


def _write_back(module, adb_path, prefs, content, device=None):
    """Write ``content`` to ``prefs`` preserving its inode/owner/SELinux context."""
    tmp_local = None
    remote_tmp = "/data/local/tmp/.adb_app_pref_%d.xml" % os.getpid()
    try:
        fd, tmp_local = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        adb_push(adb_path, tmp_local, remote_tmp, device=device)
        # In-place rewrite: redirect onto the existing file so the inode (and its
        # owner + per-app SELinux MLS category) is preserved.
        _shell(adb_path, 'cat "%s" > "%s"' % (remote_tmp, prefs), device=device)
    finally:
        _shell(adb_path, 'rm -f "%s"' % remote_tmp, device=device)
        if tmp_local and os.path.exists(tmp_local):
            os.remove(tmp_local)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            package=dict(type="str", required=True),
            key=dict(type="str", required=True),
            value=dict(type="str", required=False, default=None),
            type=dict(type="str", required=False, default="string",
                      choices=["string", "boolean", "int", "long", "float"]),
            file=dict(type="str", required=False, default=None),
            state=dict(type="str", required=False, default="present",
                       choices=["present", "absent"]),
            device=dict(type="str", required=False, default=None),
            adb_path=dict(type="str", required=False, default=None),
        ),
        required_if=[("state", "present", ["value"])],
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    package = module.params["package"]
    key = module.params["key"]
    value = module.params["value"]
    pref_type = module.params["type"]
    state = module.params["state"]
    device = module.params["device"]

    try:
        prefs = _resolve_file(adb_path, package, module.params["file"], device=device)
        raw = _read_prefs(adb_path, prefs, device=device)

        if raw is None:
            if state == "absent":
                module.exit_json(changed=False, file=prefs, previous_value=None)
            module.fail_json(
                msg="prefs file %s does not exist; launch the app once so it "
                    "creates the file, then re-run" % prefs,
                changed=False,
            )

        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            module.fail_json(msg="could not parse %s: %s" % (prefs, e), changed=False)
        if root.tag != "map":
            module.fail_json(msg="%s is not a shared_prefs file (root tag %r)"
                                 % (prefs, root.tag), changed=False)

        existing = _find(root, key)
        previous = _element_value(existing) if existing is not None else None

        if state == "absent":
            if existing is None:
                module.exit_json(changed=False, file=prefs, previous_value=None)
            if not module.check_mode:
                root.remove(existing)
                _write_back(module, adb_path, prefs, _serialize(root), device=device)
            module.exit_json(changed=True, file=prefs, previous_value=previous)

        # state == present
        desired = _desired_value(pref_type, value)
        if existing is not None and existing.tag == pref_type and _element_value(existing) == desired:
            module.exit_json(changed=False, file=prefs, previous_value=previous)

        if not module.check_mode:
            if existing is not None:
                root.remove(existing)
            root.append(_build_element(key, pref_type, value))
            _write_back(module, adb_path, prefs, _serialize(root), device=device)
        module.exit_json(changed=True, file=prefs, previous_value=previous)

    except AdbError as e:
        module.fail_json(msg="ADB error: %s" % e, changed=False)
    except Exception as e:
        module.fail_json(msg="Unexpected error: %s" % e, changed=False)


if __name__ == "__main__":
    main()
