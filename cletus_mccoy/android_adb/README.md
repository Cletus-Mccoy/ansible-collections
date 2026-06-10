# cletus_mccoy.android_adb

Ansible collection to manage Android devices over ADB.

## Features
- ADB connection plugin (timeouts + retries)
- Inventory plugin that discovers devices from `adb devices -l`
- Device info gathering
- Package listing
- File push/pull via Ansible modules
- System-property configuration (getprop/setprop/backup/validate)
- **Settings-database configuration** (`settings get/put/delete`) — idempotent
- Idempotent APK install/uninstall (with version tracking)
- Idempotent wireless connect/disconnect
- Device reboot with wait-for-boot
- Port forwarding, screen recording, intents, device pairing, logcat

## Modules
- adb_config — system properties + settings (get/set/backup/validate)
- adb_connect — wireless connect/disconnect (idempotent)
- adb_device_info
- adb_device_state
- adb_files
- adb_forward — port forwards (idempotent, supports `state: absent`)
- adb_install — APK install (idempotent via `package`/`version`)
- adb_intent — send `am start`/`broadcast` intents
- adb_logcat
- adb_packages
- adb_pair
- adb_reboot — reboot with optional `wait`/`wait_timeout`
- adb_screenrecord
- **adb_settings** — Settings database get/put/delete (idempotent)
- adb_shell
- adb_uninstall — APK uninstall (idempotent)

## Roles
- [adb_bootstrap](roles/adb_bootstrap/README.md): One-time device setup; branches on rooted vs non-rooted and persistent vs on-demand ADB strategy
- [android_probe](roles/android_probe/README.md): Probe and gather device info
- [android_config](roles/android_config/README.md): Declarative device configuration (screen timeout, locale, timezone, stay-on, free-form settings/properties)
- [settings_management](roles/settings_management/README.md): Bulk-manage Settings DB values
- [app_management](roles/app_management/README.md): Bulk/targeted APK install/remove/update
- [policy_management](roles/policy_management/README.md): Apply device policies

## Requirements
- adb installed on controller
- Android device with ADB enabled

## Two configuration subsystems

Android device configuration lives in **two different places**:

| Subsystem | Command | Module | Notes |
|---|---|---|---|
| System properties | `getprop`/`setprop` | `adb_config` (action `get`/`set`) | Most `ro.*` and `persist.*` writes need root |
| Settings database | `settings get/put/delete` | `adb_settings` | Write permission is version-dependent — see below |

Use `adb_settings` for user-facing settings (screen timeout, locale toggles, etc.)
and `adb_config` for system properties.

> **Android 16+ permission note.** On older Android the ADB shell could write
> `system`/`global` settings without root. On newer releases (confirmed on
> Android 16) `com.android.shell` is **not** granted `WRITE_SETTINGS`, so
> `settings put system` fails with `SecurityException: ... WRITE_SETTINGS`. The
> module reports this faithfully (`failed`, `changed=false`). To write settings on
> such devices you must either be **rooted**, or `pm grant <app>` the relevant
> permission (`WRITE_SETTINGS` / `WRITE_SECURE_SETTINGS`) to a helper app. Plan
> declarative `adb_settings`/`android_config` accordingly: rooted displays can take
> any setting; non-rooted daily-drivers are effectively read-only for system settings.

## Notes for downstream / integration use (v0.2.0)

- Modules shell out to `adb` on the controller, so target them with
  `delegate_to: localhost` (or set `adb_delegate_host`) while the play host is the
  Android device. Use `gather_facts: no` and `serial: 1` for Wi-Fi ADB hosts.
- **Available and idempotent in v0.2.0:** `adb_connect`, `adb_install`,
  `adb_uninstall`, `adb_settings`, `adb_config` (set), `adb_forward`,
  `adb_reboot` (with wait). Roles `adb_bootstrap` and `android_config` are filled in.
- **Action modules (not idempotent by design):** `adb_intent`, `adb_shell`,
  `adb_screenrecord`, `adb_device_state`, `adb_logcat`, `adb_pair`.

## Example

```yaml
- hosts: android
  connection: cletus_mccoy.android_adb.adb
  gather_facts: no

  tasks:
    - name: Get device info
      cletus_mccoy.android_adb.adb_device_info:
```
