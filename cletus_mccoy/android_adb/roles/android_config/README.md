# android_config role

This role manages Android device configuration using the cletus_mccoy.android_adb collection.

## Description
- Applies configuration to Android devices via ADB
- Uses modules like adb_config to set, get, backup, and validate device properties

## Requirements
- ADB must be installed on the controller
- Device must be reachable via ADB

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.android_config
```

## See Also
- [adb_bootstrap role](../adb_bootstrap/README.md)
- [android_probe role](../android_probe/README.md)
