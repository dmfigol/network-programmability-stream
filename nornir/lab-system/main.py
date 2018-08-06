import argparse
import os
from pathlib import Path
from typing import Tuple, Dict, List


import ruamel.yaml
from mypy_extensions import TypedDict
from nornir.core import InitNornir
from nornir.core.filter import F
from nornir.core.inventory import Inventory
from nornir.core.task import Task
from nornir.plugins.functions.text import print_result

YAML_FILENAME_EXTENSIONS = [".yml", ".yaml"]


DeviceDeploymentDict = TypedDict(
    "DeviceDeploymentDict", {"pod_number": int, "lab_hostname": str}
)

PodDeploymentDict = TypedDict("PodDeploymentDict", {"pod_number": int, "topology": str})


DeploymentDict = TypedDict(
    "DeploymentDict",
    {
        "name": str,
        "devices": Dict[str, DeviceDeploymentDict],
        "pods": List[PodDeploymentDict],
    },
)

LinkDict = TypedDict("LinkDict", {"lab_hostname": str, "port": str})


TopologyDict = TypedDict("TopologyDict", {"connections": List[List[LinkDict]]})

YAML = ruamel.yaml.YAML(typ="safe")


def parse_arguments():
    """

    Returns:

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deployment', help='Specify deployment name, for example: 10_sda_pov')
    parser.add_argument('-T', '--include-show-tech', help='Include show tech',
                        action='store_true')
    parser.add_argument('-p', '--pod', type=str, default='all',
                        help='Specify pod number, default: all')
    args = parser.parse_args()
    return args


def update_host_vars(inventory: Inventory) -> None:
    for host in inventory.hosts.values():
        with open(f"inventory/hosts-data/{host.name}.yml") as f:
            host_info = YAML.load(f)
            host.data.update(host_info)


def load_current_deployment(
    name: str, user_data_dir: str = "user-data"
) -> DeploymentDict:
    path = Path(user_data_dir) / "deployments" / f"{name}.yml"
    with open(path) as f:
        return YAML.load(f)


def load_topologies(user_data_dir: str = "user-data") -> Dict[str, TopologyDict]:
    topologies_dir = Path(user_data_dir) / "topologies"
    topologies = {}
    if topologies_dir.is_dir():
        for dir_path, subdirs, files in os.walk(topologies_dir):
            for filename in files:
                # print(f'dir path: {dir_path} filename: {filename}')
                base_filename, extension = os.path.splitext(filename)
                if (
                    base_filename == "topology"
                    and extension in YAML_FILENAME_EXTENSIONS
                ):
                    full_path = os.path.join(dir_path, filename)
                    dir_name = os.path.basename(os.path.dirname(full_path))
                    with open(full_path) as f:
                        topologies[dir_name] = YAML.load(f)
    return topologies


def update_matrix(
    inventory: Inventory,
    topologies: Dict[str, TopologyDict],
    deployment: DeploymentDict,
) -> None:

    # (lab_hostname, pod_number) -> device hostname in inventory
    # (edge-1, 1000) -> 9348-1

    hostname_and_pod_num_to_device: Dict[Tuple[str, int], str] = {}

    for device, device_info in deployment["devices"].items():
        pod_number = device_info["pod_number"]
        lab_hostname = device_info["lab_hostname"]
        hostname_and_pod_num_to_device[(lab_hostname, pod_number)] = device

    # (R1, Ethernet1/1) -> ('matrix-1', 1)
    device_port_to_matrix_port = {}

    matrix_switches = inventory.filter(F(has_parent_group="matrix-switches")).hosts.values()

    for matrix_switch in matrix_switches:
        for port_number, matrix_interface in enumerate(
            matrix_switch.get("interfaces", [])
        ):
            if matrix_interface.get("mode") == "dot1q-tunnel":
                if "connected_device" not in matrix_interface:
                    raise ValueError(
                        f"Interface {matrix_interface['name']} on the switch "
                        f"{matrix_switch.name} is "
                        f"dot1q-tunnel but does not have connected_device variable"
                    )

                connected_device = matrix_interface["connected_device"]["name"]
                connected_device_port = matrix_interface["connected_device"]["port"]
                # print(connected_device_port, connected_device_name)
                device_port_to_matrix_port[
                    (connected_device, connected_device_port)
                ] = (matrix_switch.name, port_number)

    current_dot1q_tunnel_vlan = matrix_switch.get("dot1q_tunnel_vlan_start")

    for pod in deployment["pods"]:
        pod_number = pod["pod_number"]
        topology = pod["topology"]
        for connection in topologies[topology]["connections"]:
            for connection_end in connection:
                lab_hostname = connection_end["lab_hostname"]
                port = connection_end["port"]
                device = hostname_and_pod_num_to_device[(lab_hostname, pod_number)]
                pod_device = inventory.hosts[device]
                if (
                    pod_device.get("lab_hostname", lab_hostname) != lab_hostname
                    and pod_device.get("pod_number", pod_number) != pod_number
                ):
                    raise ValueError(
                        f"Trying to assign lab hostname '{lab_hostname}' "
                        f"and pod number '{pod_number}', "
                        f"but this device already has"
                        f"lab hostname '{pod_device.name}'"
                        f'and pod number "{pod_device.get("pod_number")}" assigned'
                    )

                else:
                    pod_device["lab_hostname"] = lab_hostname
                    pod_device["pod_number"] = pod_number
                    pod_device["lab_template"] = topology
                    pod_device["updated_vars"] = [
                        "lab_hostname",
                        "pod_number",
                        "lab_template",
                    ]

                (
                    matrix_switch_name,
                    matrix_switch_port_number,
                ) = device_port_to_matrix_port[(device, port)]

                matrix_switch = inventory.hosts[matrix_switch_name]
                matrix_interface = matrix_switch["interfaces"][
                    matrix_switch_port_number
                ]
                if "access_vlan" in matrix_interface:
                    raise ValueError(
                        f"{matrix_switch.name} already has vlan "
                        f"assigned to the interface {mastrix_interface['name']}"
                    )

                elif matrix_interface.get("mode") != "dot1q-tunnel":
                    raise ValueError(
                        f"{matrix_switch.name} interface {matrix_interface['name']} "
                        f"has mode {matrix_interface['mode']} "
                        f"instead of 'dot1q-tunnel'"
                    )

                else:
                    matrix_interface["access_vlan"] = current_dot1q_tunnel_vlan
                    matrix_interface["shutdown"] = False
                    matrix_interface["dynamic"] = True
                    matrix_interface["description"] = (
                        f"connected to {port} {device} "
                        f"| lab hostname: {lab_hostname} "
                        f"| pod: {pod_number}"
                    )
                    # matrix_switch_vars["updated_vars"] = ["interfaces"]

            current_dot1q_tunnel_vlan += 1

        # for the next pod start with the vlan divisible by 10
        remainder = current_dot1q_tunnel_vlan % 10
        if remainder:
            current_dot1q_tunnel_vlan += 10 - remainder

    for matrix_switch in matrix_switches:
        for matrix_interface in matrix_switch["interfaces"]:
            if (
                matrix_interface.get("access_vlan") is None
                and matrix_interface.get("mode") == "dot1q-tunnel"
            ):
                matrix_interface["shutdown"] = True
        # devices["devices"][matrix_switch] = matrix_switch_vars

    # for pod_device in inventory["groups"]["pod-gear"]:
    #     pod_device = task_vars["hostvars"][pod_device]
    # devices["devices"][pod_device] = pod_device


def main() -> None:
    nr = InitNornir("config.yaml")
    matrix_switches = nr.inventory.filter(F(has_parent_group="matrix-switches"))
    update_host_vars(matrix_switches)

    deployment = load_current_deployment("2_mixed")
    topologies = load_topologies()
    update_matrix(nr.inventory, topologies, deployment)
    breakpoint()


if __name__ == "__main__":
    main()
