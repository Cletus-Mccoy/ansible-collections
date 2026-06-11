"""Helpers for UI automation over ADB (uiautomator + input).

Shared by the :mod:`adb_ui_dump` and :mod:`adb_ui_tap` modules.

The reliable way to capture the view hierarchy is to have ``uiautomator dump``
write to a file on the device and then ``cat`` it back — dumping straight to
stdout/``/dev/tty`` is flaky and often interleaves the "UI hierchary dumped to:"
status line with the XML. So :func:`dump_ui` always dumps to ``/sdcard`` and
reads the file.
"""

import re
import xml.etree.ElementTree as ET

from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
    AdbError,
    run_adb_command,
)

# Default on-device path the hierarchy is dumped to before being read back.
DEFAULT_DUMP_PATH = "/sdcard/window_dump.xml"

_BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def dump_ui(adb_path, device=None, dump_path=DEFAULT_DUMP_PATH):
    """Dump the current view hierarchy and return it as an XML string.

    Dumps to ``dump_path`` on the device, then ``cat``s it back (dumping to a
    tty/stdout is unreliable).
    """
    run_adb_command(
        adb_path, ["shell", "uiautomator", "dump", dump_path], device=device, timeout=30
    )
    xml = run_adb_command(adb_path, ["shell", "cat", dump_path], device=device)
    if not xml.lstrip().startswith("<"):
        raise AdbError("uiautomator dump did not produce XML: %s" % xml[:200])
    return xml


def parse_bounds(bounds):
    """Parse a ``[x1,y1][x2,y2]`` bounds string into ``(x1, y1, x2, y2)``.

    Returns ``None`` if the string does not match.
    """
    m = _BOUNDS_RE.search(bounds or "")
    if not m:
        return None
    return tuple(int(g) for g in m.groups())


def center_of(bounds):
    """Return the ``(x, y)`` center of a bounds string, or ``None``."""
    parsed = parse_bounds(bounds)
    if not parsed:
        return None
    x1, y1, x2, y2 = parsed
    return (x1 + x2) // 2, (y1 + y2) // 2


def parse_nodes(xml):
    """Flatten a uiautomator dump into a list of node dicts.

    Each node carries its useful identifying attributes plus the parsed
    ``bounds`` tuple and computed ``center`` ``(x, y)``.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise AdbError("could not parse UI dump XML: %s" % exc)

    nodes = []
    for el in root.iter("node"):
        attrib = el.attrib
        bounds = attrib.get("bounds", "")
        nodes.append({
            "text": attrib.get("text", ""),
            "resource_id": attrib.get("resource-id", ""),
            "content_desc": attrib.get("content-desc", ""),
            "class": attrib.get("class", ""),
            "package": attrib.get("package", ""),
            "clickable": attrib.get("clickable") == "true",
            "bounds": parse_bounds(bounds),
            "center": center_of(bounds),
        })
    return nodes


def find_nodes(nodes, text=None, resource_id=None, content_desc=None):
    """Return the subset of ``nodes`` matching the given criteria (exact match).

    Criteria that are ``None`` are ignored. With no criteria, returns ``[]``.
    """
    if text is None and resource_id is None and content_desc is None:
        return []
    matches = []
    for node in nodes:
        if text is not None and node["text"] != text:
            continue
        if resource_id is not None and node["resource_id"] != resource_id:
            continue
        if content_desc is not None and node["content_desc"] != content_desc:
            continue
        matches.append(node)
    return matches
