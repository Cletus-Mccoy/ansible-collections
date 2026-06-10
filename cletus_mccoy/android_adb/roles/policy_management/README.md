# policy_management role

This role enforces device policies on Android devices via ADB.

## Features
- Enforce screen lock, password, encryption
- Remote wipe, lock, or reset
- Manage certificates and VPN profiles

## Example
```yaml
- hosts: android
  roles:
    - role: cletus_mccoy.android_adb.policy_management
      vars:
        enforce_screen_lock: true
        min_password_length: 8
```
