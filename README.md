# ansible-collections

Ansible collections by Kasper Daems.

## Collections

| Collection | Description |
|---|---|
| [kadans.android_adb](kadans/android_adb/README.md) | Manage Android devices over ADB |

## Install

```bash
ansible-galaxy collection install git+https://github.com/kasper-daems/ansible-collections.git#/kadans/android_adb,v0.1.0
```

Or via `requirements.yml`:

```yaml
collections:
  - source: https://github.com/kasper-daems/ansible-collections.git#/kadans/android_adb
    type: git
    version: v0.1.0
```
