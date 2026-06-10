# adb_bootstrap role

One-time setup to bring an Android device under ADB management. Pairs/connects
the device and configures its ADB strategy, branching on whether the device is
rooted.

## Description
- Optional one-time wireless pairing (non-rooted devices)
- Connects to the device over ADB
- Configures the chosen ADB strategy:
  - **rooted + persistent** → sets `persist.adb.tcp.port` natively (survives reboot)
  - **non-rooted + persistent** → guidance to install the
    [adb-auto-enable](https://github.com/mouldybread/adb-auto-enable) helper app
  - **on_demand** → no persistent exposure; wireless debugging enabled manually

## Requirements
- ADB installed on the controller
- For pairing: device in pairing mode (Settings → Developer options → Wireless debugging)

## Variables
| Variable | Default | Description |
|---|---|---|
| `device_rooted` | `false` | Whether the device is rooted |
| `adb_strategy` | `on_demand` | `persistent` or `on_demand` |
| `adb_delegate_host` | `localhost` | Host that runs the `adb` binary |
| `adb_do_pairing` | `false` | Run one-time wireless pairing |
| `adb_pair_ip` | `""` | Device IP |
| `adb_pair_port` | `0` | Pairing port (one-time) |
| `adb_pair_code` | `""` | Pairing code |
| `adb_connect_port` | `5555` | Port to connect on |
| `adb_persistent_port` | `5555` | Fixed port for persistent ADB (rooted) |

## Example
```yaml
- hosts: android
  gather_facts: no
  serial: 1
  roles:
    - role: cletus_mccoy.android_adb.adb_bootstrap
      vars:
        device_rooted: true
        adb_strategy: persistent
        adb_pair_ip: 192.168.1.50
        adb_connect_port: 5555
```

## See Also
- [android_probe role](../android_probe/README.md)
- [android_config role](../android_config/README.md)
