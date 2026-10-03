# Android automation with Ansible

[![CI](https://github.com/Cletus-Mccoy/ansible-collections/actions/workflows/android_adb.yml/badge.svg)](https://github.com/Cletus-Mccoy/ansible-collections/actions/workflows/android_adb.yml)
[![Ansible Galaxy](https://img.shields.io/badge/galaxy-cletus__mccoy.android__adb-blue?logo=ansible)](https://galaxy.ansible.com/ui/repo/published/cletus_mccoy/android_adb/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](cletus_mccoy/android_adb/LICENSE)

Manage Android phones, tablets and kiosks the same way you manage servers:
declaratively, idempotently and from inventory, over plain ADB. No agent and no
Python on the device.

```yaml
- hosts: tablets
  gather_facts: false
  tasks:
    - cletus_mccoy.android_adb.adb_facts:        # gather_facts for Android
        device: "{{ ansible_host }}:5555"
      delegate_to: localhost

    - cletus_mccoy.android_adb.adb_install:      # idempotent APK install
        device: "{{ ansible_host }}:5555"
        apk_path: files/kiosk-app.apk
        package: com.example.kiosk
        version: "2.3.1"
      delegate_to: localhost

    - cletus_mccoy.android_adb.adb_settings:     # Settings DB, idempotent
        device: "{{ ansible_host }}:5555"
        namespace: system
        key: screen_off_timeout
        value: "600000"
      delegate_to: localhost
```

## What's in it

**[cletus_mccoy.android_adb](cletus_mccoy/android_adb/README.md)** has 22 modules,
6 roles, an ADB connection plugin and an inventory plugin:

- **Apps:** install, uninstall and update APKs idempotently; edit an app's SharedPreferences
- **Configuration:** Settings database and system properties, with accurate `changed`
- **Facts and inventory:** `adb_facts` as a `gather_facts` replacement; discover devices from `adb devices`
- **Connectivity:** wireless pairing (Android 11+), connect/disconnect, root toggling, per-device ADB servers for parallel fleets
- **UI automation:** screenshots, view-hierarchy dumps, tap by text or resource-id
- **Ops:** reboot and wait for boot, logcat, screen recording, port forwards, file push/pull, intents

Typical uses: kiosk and signage tablets, QA and test-device farms, debloating or
provisioning phones, home-lab wall panels.

## Install

```bash
ansible-galaxy collection install cletus_mccoy.android_adb
```

Requires ansible-core 2.16+ and `adb` (Android platform-tools) on the controller.

## Feedback

Using it? Tell me what you automate in
[Discussions](https://github.com/Cletus-Mccoy/ansible-collections/discussions/1).
That is what decides what gets built next. Bugs and feature requests go in
[Issues](https://github.com/Cletus-Mccoy/ansible-collections/issues/new/choose).
