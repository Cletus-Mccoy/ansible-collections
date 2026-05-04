DOCUMENTATION = r'''
---
module: adb_logcat
short_description: Fetch Android logcat output over ADB
description:
  - Fetches logcat output from an Android device using ADB.
options:
  device:
    description:
      - Device serial or IP:port to target.
    required: false
    type: str
  lines:
    description:
      - Number of log lines to fetch.
    required: false
    type: int
    default: 100
author:
  - Kasper Daems
version_added: '1.0.0'
'''  # noqa
