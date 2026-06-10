# app_management role

This role manages application lifecycle on Android devices via ADB.

## Features
- Install, uninstall, and update apps
- Inventory/report installed apps
- Configure app permissions and settings

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.app_management
      vars:
        app_action: install
        apk_path: /path/to/app.apk
```
