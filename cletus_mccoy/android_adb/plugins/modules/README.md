# Android ADB Modules

This directory contains Ansible modules for managing Android devices over ADB.

## Features
- Read and set device config values (getprop/setprop)
- Backup and validate device properties
- List installed packages
- Gather device info (battery, storage, network)
- Manage device state (reboot, shutdown, recovery, bootloader)
- Pair devices
- Logcat and intent automation
- **NEW:** Reboot, install/uninstall APKs, screenrecord, port forwarding

## Usage Examples

### adb_config
```yaml
- name: Get a property
  adb_config:
    action: get
    key: ro.product.model

- name: Set a property
  adb_config:
    action: set
    key: persist.sys.locale
    value: en-US

- name: Backup properties
  adb_config:
    action: backup
    backup_path: /tmp/device_props.bak

- name: Validate a property
  adb_config:
    action: validate
    key: ro.product.model
    value: Pixel 7
```

### adb_reboot
```yaml
- name: Reboot device
  adb_reboot:
    mode: normal
```

### adb_install
```yaml
- name: Install APK
  adb_install:
    apk_path: /path/to/app.apk
```

### adb_uninstall
```yaml
- name: Uninstall APK
  adb_uninstall:
    package: com.example.app
```

### adb_screenrecord
```yaml
- name: Record screen
  adb_screenrecord:
    path: /sdcard/demo.mp4
    duration: 15

- name: Record screen for 5 seconds
  cletus_mccoy.android_adb.adb_screenrecord:
    path: /tmp/screenrecord.mp4
    duration: 5
    device: "{{ adb_device }}"
```

### adb_forward
```yaml
- name: Forward port
  adb_forward:
    local: tcp:8000
    remote: tcp:8000
```

### adb_root
```yaml
- name: Restart adbd as root and reconnect the wireless device
  adb_root:
    device: 192.168.1.50:5555
# Reconnects after the transport drops and prunes the stale 'offline' entry.
```

### adb_app_pref
```yaml
- name: Pre-seed Fully Kiosk remote admin (root; inode/context-preserving)
  adb_app_pref:
    package: de.ozerov.fully
    key: remoteAdmin
    type: boolean
    value: "true"
```

### adb_screencap
```yaml
- name: Capture a screenshot to the controller
  adb_screencap:
    dest: /tmp/device.png
```

### adb_ui_dump / adb_ui_tap
```yaml
- name: Dump the UI hierarchy
  adb_ui_dump:
  register: ui

- name: Tap the "Allow" button by text
  adb_ui_tap:
    text: Allow

- name: Tap raw coordinates
  adb_ui_tap:
    x: 540
    y: 1200
```

See each module's documentation for all options and details.