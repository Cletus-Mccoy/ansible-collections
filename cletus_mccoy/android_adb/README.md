# cletus_mccoy.android_adb

Ansible collection to manage Android devices over ADB.

## Features
- ADB connection plugin (timeouts + retries)
- Inventory plugin that discovers devices from `adb devices -l`
- **`gather_facts` equivalent for Android** (`adb_facts`) — populates `ansible_facts.android` with real device state; ensures a responsive ADB server and skips asleep/offline devices cleanly
- Device info gathering
- Package listing
- File push/pull via Ansible modules
- System-property configuration (getprop/setprop/backup/validate)
- **Settings-database configuration** (`settings get/put/delete`) — idempotent
- Idempotent APK install/uninstall (with version tracking)
- Idempotent wireless connect/disconnect
- Device reboot with wait-for-boot
- Port forwarding, screen recording, intents, device pairing, logcat
- **Root toggling** (`adb root`/`unroot`) with auto-reconnect + stale-entry pruning
- **App SharedPreferences editing** (SELinux/inode-preserving)
- **UI automation**: screenshot, view-hierarchy dump, tap-by-text/resource-id

## Modules
- **adb_app_pref** — set/remove a key in an app's `shared_prefs` XML, inode/context-preserving (root)
- adb_config — system properties + settings (get/set/backup/validate)
- adb_connect — wireless connect/disconnect (idempotent; optional `prune_offline`)
- adb_device_info
- adb_device_state
- **adb_facts** — `gather_facts` equivalent for Android: populates `ansible_facts.android` (reachable/awake/rooted/model/version/packages…) for `gather_facts: false` hosts; ensures a responsive ADB server, fast connectivity probe, graceful skip on unreachable
- adb_files
- adb_forward — port forwards (idempotent, supports `state: absent`)
- adb_install — APK install (idempotent via `package`/`version`)
- adb_intent — send `am start`/`broadcast` intents
- adb_logcat
- adb_packages
- adb_pair
- adb_reboot — reboot with optional `wait`/`wait_timeout`
- **adb_root** — restart adbd as root/non-root, reconnect wireless + prune stale `offline` entries
- **adb_screencap** — capture a PNG screenshot to the controller
- adb_screenrecord
- **adb_settings** — Settings database get/put/delete (idempotent)
- adb_shell
- **adb_ui_dump** — dump the current UI view hierarchy (XML + parsed nodes)
- **adb_ui_tap** — tap by text/resource-id/content-desc or raw coordinates
- adb_uninstall — APK uninstall (idempotent)

## Roles
- [adb_bootstrap](roles/adb_bootstrap/README.md): One-time device setup; branches on rooted vs non-rooted and persistent vs on-demand ADB strategy
- [android_probe](roles/android_probe/README.md): Probe and gather device info
- [android_config](roles/android_config/README.md): Declarative device configuration (screen timeout, locale, timezone, stay-on, free-form settings/properties)
- [settings_management](roles/settings_management/README.md): Bulk-manage Settings DB values
- [app_management](roles/app_management/README.md): Bulk/targeted APK install/remove/update
- [policy_management](roles/policy_management/README.md): Apply device policies

## Requirements
- adb installed on controller
- Android device with ADB enabled

## Two configuration subsystems

Android device configuration lives in **two different places**:

| Subsystem | Command | Module | Notes |
|---|---|---|---|
| System properties | `getprop`/`setprop` | `adb_config` (action `get`/`set`) | Most `ro.*` and `persist.*` writes need root |
| Settings database | `settings get/put/delete` | `adb_settings` | Write permission is version-dependent — see below |

Use `adb_settings` for user-facing settings (screen timeout, locale toggles, etc.)
and `adb_config` for system properties.

> **Android 16+ permission note.** On older Android the ADB shell could write
> `system`/`global` settings without root. On newer releases (confirmed on
> Android 16) `com.android.shell` is **not** granted `WRITE_SETTINGS`, so
> `settings put system` fails with `SecurityException: ... WRITE_SETTINGS`. The
> module reports this faithfully (`failed`, `changed=false`). To write settings on
> such devices you must either be **rooted**, or `pm grant <app>` the relevant
> permission (`WRITE_SETTINGS` / `WRITE_SECURE_SETTINGS`) to a helper app. Plan
> declarative `adb_settings`/`android_config` accordingly: rooted displays can take
> any setting; non-rooted daily-drivers are effectively read-only for system settings.

### Settings namespace & privilege matrix

`adb_settings` only reaches the **AOSP Settings provider**. What actually works
depends on the namespace and the device's privilege level:

| Write | Module | Root needed? | Notes |
|---|---|---|---|
| `settings put system <k>` | `adb_settings` | Yes on Android 16+ | Needs `WRITE_SETTINGS` (granted to an app) or root — see the note above |
| `settings put secure <k>` | `adb_settings` | Sometimes | `WRITE_SECURE_SETTINGS`; but some keys work root-free… |
| `settings put secure always_on_vpn_app` / `always_on_vpn_lockdown` | `adb_settings` | **No** | Works from the ADB shell without root — handy for VPN lockdown |
| `setprop persist.* …` | `adb_config` (set) | **Yes** | `persist.*` / most `ro.*` writes require root |
| LineageOS-specific settings | — | n/a | Live in a separate `lineagesettings` provider that `settings put` **does not** reach |

### Root path on userdebug / GSI builds

On rooted phh-Treble GSIs (and other userdebug builds), `adb root` is the reliable
root path — prefer the **`adb_root`** module over `su -c` in `adb_shell`. Magisk
`su` is often unreliable there (it competes with phh's `/system/xbin/su` and can
land in an "Abnormal State", denying the shell without prompting). `adb root` needs
Developer options → **"Rooted debugging"** enabled; otherwise adbd reports
*"ADB Root access is disabled by system setting"* and `adb_root` fails with that
guidance.

`adb root`/`unroot`/`tcpip` all drop the current TCP transport, leaving a stale
`offline` entry next to the live device in `adb devices`. `adb_root` reconnects and
prunes those automatically; `adb_connect` gained `prune_offline: true` for the same
cleanup.

### Persistent ADB across reboots

The reliable, no-re-pair combo on a rooted device:

1. Developer options → **"Rooted debugging"** (enables `adb root`).
2. `setprop persist.adb.tcp.port 5555` (via `adb_config`, needs root).
3. Persist the controller's key in `/data/misc/adb/adb_keys`.

This survives reboot with no re-pair, and the `android_probe` role's 37000–44999
port scan then correctly falls back to the fixed `adb_port`.

### UI automation

First-time setup is often unavoidably UI-driven (Tailscale login, toggling
"Rooted debugging", etc.). Use `adb_screencap` to see the screen, `adb_ui_dump` to
read the view hierarchy, and `adb_ui_tap` to tap by `text`/`resource_id` or raw
coordinates. **Force-stop foreground-stealing overlay apps first** (e.g. a
rotation-lock app) — they grab focus and fight UI automation.

## Gathering facts (the `setup`-module equivalent)

Android hosts run `gather_facts: false` (no on-device Python/SSH). Instead of
faking facts from inventory, run `adb_facts` as a pre-task — it talks to the
device over ADB from the controller and populates `ansible_facts.android`:

```yaml
- hosts: android
  gather_facts: false
  serial: 1
  pre_tasks:
    - name: Gather Android facts
      cletus_mccoy.android_adb.adb_facts:
        device: "{{ local_ip }}:{{ adb_port }}"
        connect: true
        gather_subset: [min, hardware, root]
      delegate_to: localhost

    - name: Skip asleep/offline devices without failing the run
      ansible.builtin.meta: end_host
      when: not ansible_facts.android.reachable
```

`adb_facts` ensures a responsive ADB server first (restarting a hung/stale
fork-server), then does a **bounded** connectivity probe. An unreachable device
returns `ansible_facts.android.reachable == false` and the task **succeeds** — so
you no longer need play-level `ignore_unreachable: true` / `any_errors_fatal:
false` to keep one offline phone from stalling a `serial: 1` batch.

## ADB server lifecycle & throughput

- One `adb -L tcp:5037` fork-server is shared per controller. A wedged server
  holds the socket and silently degrades every later run. `adb_facts` (and any
  module via `module_utils.adb.ensure_server`) detects an unresponsive server and
  `kill-server`/`start-server`s it. **Every** adb call in the collection now has a
  finite timeout (`AdbTimeout`) — there are no unbounded hangs.
- Wi-Fi ADB contention is why fleet runs use `serial: 1`. Because the server is
  shared, true per-device parallelism needs connection isolation (separate
  `ANDROID_ADB_SERVER_PORT` per device/fork) — keep `serial: 1` unless you set
  that up.

## Persistent vs on-demand ADB strategy

- **Persistent ADB** (always-listening wireless debugging) suits devices that
  never leave the network (wall tablets, kiosks). **Never enable persistent ADB
  on devices that leave the network** (phones) — when they roam, the open debug
  port travels with them. Phones are **on-demand**: paired/connected only for a
  run, expected asleep/off otherwise (hence the graceful-skip behaviour above).
- **Pairing (Android 11+):** the pairing code and port are shown in a
  *Wireless debugging → Pair device with pairing code* dialog that **times out**
  and must be held open. Use `adb_pair` with the port+code while that dialog is
  visible; if it expires, reopen the dialog to get a fresh code and retry.

## Notes for downstream / integration use (v0.4.1)

- Modules shell out to `adb` on the controller, so target them with
  `delegate_to: localhost` (or set `adb_delegate_host`) while the play host is the
  Android device. Use `gather_facts: no` and `serial: 1` for Wi-Fi ADB hosts.
- **Idempotency / fingerprint-gating:** the write modules read before they write
  and report `changed` accurately (`adb_config`/`adb_settings` compare the current
  value; `adb_install` compares the installed `versionName`). `app_management`'s
  `bulk_update` now threads `package`/`version`, so an update to an already-present
  version reports `changed=false` — consumers can fingerprint-gate Android roles
  like Linux ones. `policy_management` enforces only ADB-settable policies
  idempotently and guards destructive actions (`remote_wipe` needs
  `policy_confirm_wipe=true`).
- **Available and idempotent:** `adb_connect`, `adb_install`, `adb_uninstall`,
  `adb_settings`, `adb_config` (set), `adb_forward`, `adb_reboot` (with wait),
  `adb_app_pref`. `adb_root` is idempotent on adbd's own report. Roles
  `adb_bootstrap` and `android_config` are filled in.
- **Action modules (not idempotent by design):** `adb_intent`, `adb_shell`,
  `adb_screenrecord`, `adb_screencap`, `adb_ui_dump`, `adb_ui_tap`,
  `adb_device_state`, `adb_logcat`, `adb_pair`.
- **Require root:** `adb_app_pref` (and `adb_root` itself, which enables it).

## Example

```yaml
- hosts: android
  connection: cletus_mccoy.android_adb.adb
  gather_facts: no

  tasks:
    - name: Get device info
      cletus_mccoy.android_adb.adb_device_info:
```
