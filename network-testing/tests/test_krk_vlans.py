from operator import itemgetter
from pathlib import Path
from typing import Dict, Any

from ruamel.yaml import YAML
from nornir.core.filter import F
from nornir.plugins.tasks import networking

CONFIG_FILE = "krk_vlans.yaml"


def load_config(config_file: str) -> Dict[str, Any]:
    yaml = YAML(typ="safe")
    dir_path = Path(__file__).parent
    with open(dir_path / config_file) as f:
        return yaml.load(f)


def process_data(data, config):
    result = []
    for vlan_data in data:
        name = vlan_data["name"]
        id_ = int(vlan_data["vlan_id"])
        if id_ not in config["excluded_vlans"]:
            vlan_dict = {"id": id_, "name": name}
            result.append(vlan_dict)
    return sorted(result, key=itemgetter("id"))


def get_data(task, config):
    # task.host["vlans"] =
    data = task.run(
        task=networking.netmiko_send_command,
        command_string="show vlan",
        use_textfsm=True,
    ).result
    task.host["vlans"] = process_data(data, config)


def test_krk_vlans(nr):
    config = load_config(CONFIG_FILE)
    hosts = nr.filter(F(groups__contains=config["group"]))
    hosts.run(task=get_data, config=config)

    desired_vlans = config["data"]["vlans"]

    for host in hosts.inventory.hosts.values():
        configured_vlans = host["vlans"]
        assert configured_vlans == desired_vlans, f"Failed for host: {host.name}"
        # if not configured_vlans == desired_vlans:
        # raise ValueError(
        #     f"{host.name!r} has vlans: {configured_vlans}, but "
        #     f"desired vlans: {desired_vlans}"
        # )

    # print("Test passed: Vlans are correct")
