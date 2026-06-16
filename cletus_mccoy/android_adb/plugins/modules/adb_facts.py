DOCUMENTATION = r'''
---
module: adb_facts
short_description: Gather Ansible facts from an Android device over ADB
version_added: '1.4.0'
description:
  - The ADB equivalent of M(ansible.builtin.setup) for Android devices.
  - Runs on the controller (delegated to localhost) and talks to the device
    over ADB, so it works for hosts that gather no facts and have no SSH/Python
    on-device. Populates C(ansible_facts.android) with real device state instead
    of inventory-faked facts.
  - Performs a fast, bounded connectivity probe first. An asleep/offline device
    is reported as C(ansible_facts.android.reachable=false) and the task
    succeeds (C(changed=false)) rather than hanging or failing — so one offline
    device never stalls a serialized run and consumers no longer need play-level
    C(ignore_unreachable)/C(any_errors_fatal) workarounds.
  - Ensures a responsive ADB server before probing, restarting a hung/stale
    fork-server if needed (see O(ensure_server)).
  - Read-only. Never changes device state.
options:
  device:
    description:
      - Device serial or C(ip:port) to target. When omitted, the single
        attached device is used.
    required: false
    type: str
  connect:
    description:
      - When the device looks like C(ip:port), run a bounded C(adb connect)
        before probing. Leave false if a separate connect step already ran.
    required: false
    type: bool
    default: false
  connect_timeout:
    description:
      - Seconds to allow for the connectivity probe (and optional connect). Kept
        short so unreachable devices are skipped quickly.
    required: false
    type: int
    default: 5
  command_timeout:
    description:
      - Per-command timeout (seconds) for the ADB shell calls used to gather facts.
    required: false
    type: int
    default: 30
  gather_subset:
    description:
      - Which fact groups to collect. C(min) is always included.
      - Choose from C(min), C(hardware), C(network), C(storage), C(battery),
        C(packages), C(root), C(all).
    required: false
    type: list
    elements: str
    default: [min]
  fail_on_unreachable:
    description:
      - When true, fail the task if the device cannot be reached. The default
        (false) returns facts with C(reachable=false) so playbooks can branch on
        device state instead of erroring.
    required: false
    type: bool
    default: false
  ensure_server:
    description:
      - Detect a hung/stale ADB server and C(kill-server)/C(start-server) before
        probing. Recommended once per play; harmless to leave on.
    required: false
    type: bool
    default: true
  adb_path:
    description:
      - Path to the C(adb) binary. Defaults to C(adb) resolved from PATH.
    required: false
    type: str
author:
  - Kasper Daems
'''

EXAMPLES = r'''
# Drop-in gather-facts step for Android hosts (which run gather_facts: false).
- name: Gather Android facts
  cletus_mccoy.android_adb.adb_facts:
    device: "{{ local_ip }}:{{ adb_port }}"
    connect: true
    gather_subset: [min, hardware, root]
  delegate_to: localhost

- name: Skip the rest of the play when the device is asleep/offline
  ansible.builtin.meta: end_host
  when: not ansible_facts.android.reachable

- name: Use real device facts
  ansible.builtin.debug:
    msg: "{{ ansible_facts.android.model }} on Android {{ ansible_facts.android.android_version }}"
'''

RETURN = r'''
ansible_facts:
  description: Facts to add to C(ansible_facts), under the C(android) key.
  returned: always
  type: dict
  contains:
    android:
      description: Device facts (a subset depending on reachability and O(gather_subset)).
      type: dict
      sample:
        reachable: true
        state: device
        device: "192.168.1.50:5555"
        awake: false
        rooted: false
        model: "Pixel 5"
        manufacturer: "Google"
        android_version: "14"
        sdk: "34"
changed:
  description: Always false (read-only).
  returned: always
  type: bool
'''

import shutil

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.adb import (
    adb_shell,
    ensure_server as adb_ensure_server,
    probe_device,
    AdbError,
    AdbTimeout,
)
from ansible_collections.cletus_mccoy.android_adb.plugins.module_utils.parsing import (
    parse_getprop,
    extract_device_info,
    parse_packages,
    parse_awake_state,
    parse_adbd_root,
)


def _subsets(requested):
    """Expand the gather_subset list into a concrete set (always includes min)."""
    requested = set(requested or [])
    if "all" in requested:
        return {"min", "hardware", "network", "storage", "battery", "packages", "root"}
    requested.add("min")
    return requested


def _shell(adb_path, cmd, device, timeout):
    """adb shell that returns '' on error instead of aborting the whole gather."""
    try:
        return adb_shell(adb_path, cmd, device=device, timeout=timeout)
    except (AdbError, AdbTimeout):
        return ""


def gather(adb_path, device, subsets, timeout):
    facts = {}

    props = parse_getprop(_shell(adb_path, "getprop", device, timeout))
    base = extract_device_info(props)
    # Friendlier, setup-style key names alongside the device_info names.
    facts.update({
        "manufacturer": base["manufacturer"],
        "model": base["model"],
        "brand": base["brand"],
        "android_version": base["android_ver"],
        "sdk": base["sdk_version"],
        "build_id": base["build_id"],
        "serial": base["serial"],
        "timezone": base["timezone"],
        "locale": base["locale"],
        "security_patch": props.get("ro.build.version.security_patch", "unknown"),
    })

    # Awake/screen state — cheap and always useful for on-demand devices.
    facts["awake"] = parse_awake_state(_shell(adb_path, "dumpsys power", device, timeout))

    if "root" in subsets:
        facts["adbd_root"] = parse_adbd_root(_shell(adb_path, "id", device, timeout))
        # A `su` binary means the device itself is rooted, independent of adbd.
        su_path = _shell(adb_path, "which su || command -v su || true", device, timeout)
        facts["rooted"] = bool(su_path.strip()) or facts["adbd_root"]

    if "hardware" in subsets:
        facts["cpu_abi"] = props.get("ro.product.cpu.abi", "unknown")
        facts["hardware"] = props.get("ro.hardware", "unknown")
        facts["device_codename"] = props.get("ro.product.device", "unknown")
        facts["kernel"] = _shell(adb_path, "uname -r", device, timeout) or "unknown"

    if "network" in subsets:
        facts["network"] = _shell(adb_path, "ip addr show", device, timeout)

    if "storage" in subsets:
        facts["storage"] = _shell(adb_path, "df /data", device, timeout)

    if "battery" in subsets:
        facts["battery"] = _shell(adb_path, "dumpsys battery", device, timeout)

    if "packages" in subsets:
        facts["installed_apps"] = parse_packages(
            _shell(adb_path, "pm list packages -3", device, timeout)
        )

    return facts


def main():
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type="str", required=False),
            connect=dict(type="bool", required=False, default=False),
            connect_timeout=dict(type="int", required=False, default=5),
            command_timeout=dict(type="int", required=False, default=30),
            gather_subset=dict(type="list", elements="str", required=False, default=["min"]),
            fail_on_unreachable=dict(type="bool", required=False, default=False),
            ensure_server=dict(type="bool", required=False, default=True),
            adb_path=dict(type="str", required=False, default=None),
        ),
        supports_check_mode=True,
    )

    adb_path = module.params["adb_path"] or shutil.which("adb")
    if not adb_path:
        module.fail_json(msg="adb not found in PATH", changed=False)

    device = module.params.get("device")
    connect_timeout = module.params["connect_timeout"]
    command_timeout = module.params["command_timeout"]
    subsets = _subsets(module.params["gather_subset"])

    server = {"restarted": False}
    try:
        if module.params["ensure_server"]:
            server = adb_ensure_server(adb_path, timeout=connect_timeout)
            if not server.get("responsive", True):
                module.fail_json(
                    msg="ADB server is not responsive even after restart",
                    changed=False,
                )
    except AdbTimeout as e:
        module.fail_json(msg=str(e), changed=False)

    state = probe_device(
        adb_path, device,
        connect=module.params["connect"],
        connect_timeout=connect_timeout,
    )

    if state != "device":
        # Asleep / offline / unauthorized — skip cleanly with usable facts.
        android = {
            "reachable": False,
            "state": state,
            "device": device,
            "server_restarted": server.get("restarted", False),
        }
        if module.params["fail_on_unreachable"]:
            module.fail_json(
                msg="device %s not reachable (state=%s)" % (device, state),
                changed=False,
                ansible_facts={"android": android},
            )
        module.exit_json(changed=False, ansible_facts={"android": android})

    try:
        android = gather(adb_path, device, subsets, command_timeout)
    except (AdbError, AdbTimeout) as e:
        module.fail_json(msg=str(e), changed=False)

    android.update({
        "reachable": True,
        "state": state,
        "device": device,
        "server_restarted": server.get("restarted", False),
    })

    module.exit_json(changed=False, ansible_facts={"android": android})


if __name__ == "__main__":
    main()
