# settings_management role

This role manages fine-grained Android system, secure, and global settings via ADB.

## Features
- Get/set individual settings (system, secure, global)
- Bulk export/import settings
- Compliance checks for settings

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.settings_management
      vars:
        settings_bulk:
          - namespace: system
            key: screen_brightness
            value: 200
          - namespace: secure
            key: location_providers_allowed
            value: gps,network
        settings_get:
          - namespace: global
            key: airplane_mode_on
```
