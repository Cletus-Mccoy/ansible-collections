# ansible-collections

Ansible collections by Kasper Daems.

## Collections

| Collection | Description |
|---|---|
| [cletus_mccoy.android_adb](cletus_mccoy/android_adb/README.md) | Manage Android devices over ADB |

## Install

```bash
ansible-galaxy collection install git+https://github.com/Cletus-Mccoy/ansible-collections.git#/cletus_mccoy/android_adb,v0.2.0
```

Or via `requirements.yml`:

```yaml
collections:
  - source: https://github.com/Cletus-Mccoy/ansible-collections.git#/cletus_mccoy/android_adb
    type: git
    version: v0.2.0
```
