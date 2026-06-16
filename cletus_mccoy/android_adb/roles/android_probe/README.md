# android_probe role

This role uses the cletus_mccoy.android_adb collection to probe and bootstrap Android devices over ADB.

## Description
- Discovers the wireless-debugging port and connects to the device via ADB
- Gathers real device facts via the `adb_facts` module into `ansible_facts.android`
  (model, Android version, awake/screen state, root status, installed apps)
- Ensures a responsive ADB server first (restarts a hung/stale fork-server)
- **Skips asleep/offline devices cleanly** (`meta: end_host`) so one unreachable
  device never stalls a `serial: 1` run — no `ignore_unreachable`/`any_errors_fatal`
  needed on the consuming play
- Keeps `android_device_info` / `android_installed_apps` facts for backwards compatibility

## Requirements
- ADB must be installed on the controller
- Device should be reachable via ADB (unreachable devices are skipped, not failed)

## Variables
| Variable | Default | Purpose |
|---|---|---|
| `local_ip` | `127.0.0.1` | Device IP for wireless ADB |
| `adb_port` | `5555` | ADB port (auto-discovered if a `37000–45000` port is open) |
| `probe_gather_subset` | `[min, hardware, packages, root]` | Fact groups for `adb_facts` |
| `probe_connect_timeout` | `5` | Seconds for the connectivity probe |
| `probe_skip_unreachable` | `true` | Skip (vs fail) an unreachable device |
| `probe_ensure_server` | `true` | Detect/restart a hung ADB server before probing |

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.android_probe
```

## See Also
- [adb_bootstrap role](../adb_bootstrap/README.md)
- [android_config role](../android_config/README.md)
