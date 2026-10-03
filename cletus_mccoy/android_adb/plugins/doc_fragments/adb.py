# -*- coding: utf-8 -*-
# (c) 2026 Kasper Daems
# MIT License (see LICENSE)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    """Options shared by every module in the collection.

    These are exactly the options that ``module_defaults`` can set for the whole
    ``group/cletus_mccoy.android_adb.adb`` action group.
    """

    # Modules that target one device (almost all of them).
    DOCUMENTATION = r'''
options:
  device:
    description:
      - Device serial or C(IP:port) to target (C(adb -s)).
      - May be omitted when exactly one device is connected.
    type: str
  adb_path:
    description:
      - Path to the C(adb) binary. Resolved from E(PATH) when not set.
    type: str
  adb_server_port:
    description:
      - Talk to a dedicated ADB server on this port instead of the shared
        C(tcp:5037) server (sets E(ANDROID_ADB_SERVER_PORT) for every C(adb)
        call the module makes).
      - Give each device a distinct port (for example from inventory) to
        isolate them, so a fleet can run in parallel instead of one host at a time.
    type: int
'''

    # Modules that manage the connection itself and take an address instead of
    # a device serial (adb_connect, adb_pair).
    SERVER = r'''
options:
  adb_path:
    description:
      - Path to the C(adb) binary. Resolved from E(PATH) when not set.
    type: str
  adb_server_port:
    description:
      - Talk to a dedicated ADB server on this port instead of the shared
        C(tcp:5037) server (sets E(ANDROID_ADB_SERVER_PORT) for every C(adb)
        call the module makes).
      - Give each device a distinct port (for example from inventory) to
        isolate them, so a fleet can run in parallel instead of one host at a time.
    type: int
'''
