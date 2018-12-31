import math
from pathlib import Path

import ruamel.yaml
from nornir.core.inventory import Inventory
from nornir.core.filter import F

YAML = ruamel.yaml.YAML(typ="safe")


def update_description(inventory: Inventory) -> None:
    infra_devices = inventory.filter(F(has_parent_group='infra')).hosts.values()
    for device in infra_devices:
        for interface in device.get('interfaces', []):
            if 'connected_device' in interface:
                connected_device_info = interface["connected_device"]
                connected_device_name = connected_device_info["name"]
                port = connected_device_info["port"]
                connected_device = inventory.hosts[connected_device_name]
                rack = connected_device['rack']
                rack_unit = connected_device['rack_unit']
                description = (
                    f"To Rack {rack} RU {rack_unit} -> {connected_device_name} {port}"
                )
                interface["description"] = description


def update_host_vars(inventory: Inventory) -> None:
    for host in inventory.hosts.values():
        path = Path(f"inventory/host_vars/{host.name}.yml")
        if path.is_file():
            with open(path) as f:
                host_info = YAML.load(f)
                host.data.update(host_info)


def roundup(value: float) -> int:
    return int(math.ceil(value / 10)) * 10
