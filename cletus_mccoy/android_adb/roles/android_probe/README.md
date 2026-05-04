# android_probe role

This role uses the kadans.android_adb collection to probe and bootstrap Android devices over ADB.

## Description
- Connects to Android devices via ADB
- Discovers device properties
- Optionally bootstraps device configuration

## Requirements
- ADB must be installed on the controller
- Device must be reachable via ADB

## Example
```yaml
- hosts: android
  roles:
    - role: kadans.android_adb.android_probe
```
