DOCUMENTATION = r'''
name: adb_devices
author: Kasper Daems
short_description: Inventory plugin for Android devices via ADB
description:
  - Discovers Android devices connected via ADB and adds them to inventory.
options:
  plugin:
    description: Name of the plugin
    required: true
    choices: ['adb_devices']
  groups:
    description: List of groups to assign devices to
    required: false
    type: list
  keyed_groups:
    description: List of keyed groups to add hosts to
    required: false
    type: list
  strict:
    description: Fail if no devices are found
    required: false
    type: bool
    default: false
version_added: '1.0.0'
'''  # noqa
