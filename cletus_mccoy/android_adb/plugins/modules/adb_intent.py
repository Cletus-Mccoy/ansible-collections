DOCUMENTATION = r'''
---
module: adb_intent
short_description: Send Android intent over ADB
description:
  - Sends an intent to an Android device using ADB shell am start.
options:
  device:
    description:
      - Device serial or IP:port to target.
    required: false
    type: str
  action:
    description:
      - Intent action to send.
    required: true
    type: str
  data:
    description:
      - Data URI for the intent.
    required: false
    type: str
author:
  - Kasper Daems
version_added: '1.0.0'
'''  # noqa
