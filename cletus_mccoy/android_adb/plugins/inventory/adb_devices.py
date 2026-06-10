DOCUMENTATION = r'''
name: adb_devices
author: Kasper Daems
short_description: Inventory source for Android devices reachable via ADB
description:
  - Discovers Android devices from C(adb devices -l) and adds them to inventory.
  - Each device's serial (or C(IP:port) for wireless devices) becomes the
    inventory hostname, with C(ansible_connection) set to the collection's
    C(adb) connection plugin.
  - Optionally queries device properties via C(getprop) to build host variables
    and keyed groups.
extends_documentation_fragment:
  - constructed
options:
  plugin:
    description: Token that ensures this is a source file for the C(adb_devices) plugin.
    required: true
    choices: ['cletus_mccoy.android_adb.adb_devices', 'adb_devices']
  adb_path:
    description: Path to the C(adb) binary.
    required: false
    type: str
    default: adb
  filter:
    description: Only include devices whose serial or queried properties contain this substring.
    required: false
    type: str
  group_by_property:
    description:
      - Group devices by a system property (e.g. C(ro.product.model)). Devices
        sharing a property value are placed in a group named after it.
    required: false
    type: str
  properties:
    description:
      - System properties to query for each device and expose as host variables
        (e.g. C(ro.product.model), C(ro.build.version.release)).
    required: false
    type: list
    elements: str
    default: []
  only_authorized:
    description: Skip devices in C(unauthorized)/C(offline) state.
    required: false
    type: bool
    default: true
version_added: '0.2.0'
'''

EXAMPLES = r'''
# adb_devices.yml
plugin: cletus_mccoy.android_adb.adb_devices
properties:
  - ro.product.model
  - ro.product.brand
group_by_property: ro.product.brand
filter: Pixel
compose:
  ansible_host: inventory_hostname
keyed_groups:
  - key: adb_state
    prefix: adb
'''

import subprocess

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'cletus_mccoy.android_adb.adb_devices'

    def verify_file(self, path):
        if not super(InventoryModule, self).verify_file(path):
            return False
        return path.endswith(('adb_devices.yml', 'adb_devices.yaml',
                              'adb.yml', 'adb.yaml'))

    def _run(self, args):
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise AnsibleParserError(
                "adb command failed: %s" % (result.stderr.strip() or result.stdout.strip())
            )
        return result.stdout

    def _list_devices(self, adb_path):
        """Return list of (serial, state) tuples from `adb devices -l`."""
        out = self._run([adb_path, "devices", "-l"])
        devices = []
        for line in out.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "unknown"
            devices.append((serial, state))
        return devices

    def _getprop(self, adb_path, serial, prop):
        try:
            return self._run([adb_path, "-s", serial, "shell", "getprop", prop]).strip()
        except AnsibleParserError:
            return ""

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        config = self._read_config_data(path)

        adb_path = self.get_option('adb_path')
        wanted_props = self.get_option('properties') or []
        group_by = self.get_option('group_by_property')
        substring = self.get_option('filter')
        only_authorized = self.get_option('only_authorized')

        if group_by and group_by not in wanted_props:
            wanted_props = list(wanted_props) + [group_by]

        strict = self.get_option('strict')

        for serial, state in self._list_devices(adb_path):
            if only_authorized and state != "device":
                continue

            props = {p: self._getprop(adb_path, serial, p) for p in wanted_props}

            if substring:
                haystack = " ".join([serial] + list(props.values()))
                if substring not in haystack:
                    continue

            self.inventory.add_host(serial)
            self.inventory.set_variable(serial, 'ansible_connection',
                                        'cletus_mccoy.android_adb.adb')
            self.inventory.set_variable(serial, 'adb_state', state)
            for prop, value in props.items():
                # expose as a sanitized variable name, e.g. ro.product.model -> ro_product_model
                self.inventory.set_variable(serial, prop.replace('.', '_'), value)

            if group_by:
                value = props.get(group_by)
                if value:
                    group_name = self._sanitize_group_name(value)
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, serial)

            host_vars = dict(props)
            host_vars['adb_state'] = state
            self._set_composite_vars(self.get_option('compose'), host_vars, serial, strict=strict)
            self._add_host_to_composed_groups(self.get_option('groups'), host_vars, serial, strict=strict)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host_vars, serial, strict=strict)

    @staticmethod
    def _sanitize_group_name(value):
        return ''.join(c if c.isalnum() else '_' for c in value).strip('_').lower()
