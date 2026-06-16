# policy_management role

Apply device policies over ADB.

Plain (non-rooted) ADB is **not** a Device Policy Controller (MDM), so this role
only enforces policies that map to real, writable Android Settings — using the
idempotent `adb_settings` module, so a no-op re-run reports `changed=false`.
Policies that genuinely require an MDM/DPC are **skipped with a warning** rather
than silently failing. Destructive actions are explicit and guarded.

## Variables
| Variable | Default | Effect |
|---|---|---|
| `policy_device` | `{{ inventory_hostname }}` | Device serial / `ip:port` |
| `adb_delegate_host` | `localhost` | Controller that runs `adb` |
| `enforce_screen_lock` | `false` | Idempotent: sets `secure/lockscreen.disabled=0` |
| `min_password_length` | _unset_ | **Not enforceable over ADB** — skipped with a warning |
| `require_encryption` | `false` | **Not settable over ADB** — skipped with a warning |
| `remote_lock` | `false` | Action: turns the screen off (locks if a secure lock is set) |
| `remote_wipe` | `false` | Action: factory reset — **requires** `policy_confirm_wipe=true` |
| `policy_confirm_wipe` | `false` | Confirmation gate for `remote_wipe` (fails otherwise) |

## Example
```yaml
- hosts: android
  gather_facts: false
  roles:
    - role: cletus_mccoy.android_adb.policy_management
      vars:
        policy_device: "192.168.1.50:5555"
        enforce_screen_lock: true
```

> `remote_wipe` is destructive. It refuses to run unless both `remote_wipe` and
> `policy_confirm_wipe` are `true`.
