# cletus_mccoy.android_adb

Ansible collection to manage Android devices over ADB.

## Features
- ADB connection plugin
- Device info gathering
- Package listing
- File push/pull via Ansible modules
- Device configuration (getprop/setprop/backup/validate)
- Device state management (reboot, shutdown, bootloader, recovery)
- APK install/uninstall
- Screen recording
- Port forwarding
- Device pairing
- Logcat and intent automation

## Modules
- adb_config
- adb_device_info
- adb_device_state
- adb_forward
- adb_install
- adb_intent
- adb_logcat
- adb_packages
- adb_pair
- adb_reboot
- adb_screenrecord
- adb_uninstall

## Roles
- [adb_bootstrap](roles/adb_bootstrap/README.md): Bootstrap Android devices for configuration
- [android_probe](roles/android_probe/README.md): Probe and gather device info
- [android_config](roles/android_config/README.md): Manage device configuration

## Requirements
- adb installed on controller
- Android device with ADB enabled

## Example

```yaml
- hosts: android
  connection: adb
  gather_facts: no

  tasks:
    - name: Get device info
      cletus_mccoy.android_adb.adb_device_info:
```