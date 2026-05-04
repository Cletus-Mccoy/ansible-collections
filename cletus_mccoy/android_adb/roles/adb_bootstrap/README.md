# adb_bootstrap role

This role bootstraps Android devices using the kadans.android_adb collection.

## Description
- Prepares Android devices for configuration via ADB

## Requirements
- ADB must be installed on the controller
- Device must be reachable via ADB

## Example
```yaml
- hosts: android
  roles:
    - role: kadans.android_adb.adb_bootstrap
```
