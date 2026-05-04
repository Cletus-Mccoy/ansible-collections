# android_config role

This role manages Android device configuration using the kadans.android_adb collection.

## Description
- Applies configuration to Android devices via ADB

## Requirements
- ADB must be installed on the controller
- Device must be reachable via ADB

## Example
```yaml
- hosts: android
  roles:
    - role: kadans.android_adb.android_config
```
