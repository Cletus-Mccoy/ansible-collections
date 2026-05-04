
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
  filter:
    description: Only include devices matching this substring (serial, model, etc.)
    required: false
    type: str
  group_by_property:
    description: Group devices by a property (e.g., model, brand)
    required: false
    type: str
version_added: '1.1.0'
'''  # noqa

# Advanced usage (planned):
# - filter: Only include devices matching a substring (serial, model, etc.)
# - group_by_property: Group devices by a property (e.g., model, brand)
#
# Example (future):
# plugin: adb_devices
#   filter: "Pixel"
#   group_by_property: model
#   groups:
#     - androids
#
# Implementation would require parsing `adb devices -l` and querying device properties.
