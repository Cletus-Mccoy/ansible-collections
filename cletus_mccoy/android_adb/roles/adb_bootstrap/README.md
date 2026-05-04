# adb_bootstrap role

This role bootstraps Android devices using the cletus_mccoy.android_adb collection.

## Description
- Prepares Android devices for configuration via ADB
- Installs required packages, sets up environment, and ensures device is ready for further automation.

## Requirements
- ADB must be installed on the controller
- Device must be reachable via ADB

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.adb_bootstrap
```

## See Also
- [android_probe role](../android_probe/README.md)
- [android_config role](../android_config/README.md)
