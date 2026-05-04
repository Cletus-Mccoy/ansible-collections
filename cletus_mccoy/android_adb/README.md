# cletus_mccoy.android_adb

Ansible collection to manage Android devices over ADB.

## Features (initial)
- ADB connection plugin
- Device info gathering
- Package listing
- File push/pull via Ansible modules

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
      adb_device_info: