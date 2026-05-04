# android_probe role

This role uses the cletus_mccoy.android_adb collection to probe and bootstrap Android devices over ADB.

## Description
- Connects to Android devices via ADB
- Discovers device properties (model, version, battery, storage, network)
- Optionally bootstraps device configuration for further automation

## Requirements
- ADB must be installed on the controller
- Device must be reachable via ADB

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.android_probe
```

## See Also
- [adb_bootstrap role](../adb_bootstrap/README.md)
- [android_config role](../android_config/README.md)
