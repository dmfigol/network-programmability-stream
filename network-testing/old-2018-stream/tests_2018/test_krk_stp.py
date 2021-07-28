from collections import defaultdict
from operator import itemgetter
from pathlib import Path
from typing import Dict, Any

from ruamel.yaml import YAML
from nornir.core.filter import F
from nornir.plugins.tasks import networking

CONFIG_FILE = "test_krk_stp.yaml"


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


def update_stp_root(task, stp_stats, vlan_ids) -> None:
    for vlan_id in vlan_ids:
        output = task.run(
            task=networking.netmiko_send_command,
            command_string=f"show spanning-tree vlan {vlan_id}",
        ).result
        if "This bridge is the root" in output:
            stp_stats["stp_root"]["vlans"][vlan_id].append(task.host.name)


def test_krk_stp_root(nr):
    config = load_config(CONFIG_FILE)
    hosts = nr.filter(F(groups__contains=config["group"]))
    configured_stp_stats = {"stp_root": {"vlans": defaultdict(list)}}
    desired_stp_stats = config["data"]
    hosts.run(
        task=update_stp_root,
        stp_stats=configured_stp_stats,
        vlan_ids=desired_stp_stats["stp_root"]["vlans"].keys(),
    )

    desired_stp_stats = config["data"]

    assert dict(configured_stp_stats["stp_root"]["vlans"]) == desired_stp_stats["stp_root"]["vlans"]
