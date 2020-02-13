#!/usr/bin/env python3
import logging
import logging.config
import time
from typing import List, Dict, Tuple

from colorama import Fore
from nornir import InitNornir
from nornir.core.inventory import Host
import colorama
import matplotlib.pyplot as plt
import networkx as nx
import requests
import urllib3

import constants
from interface import Interface

logging.config.dictConfig(constants.LOGGING_DICT)
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
colorama.init()


def extract_hostname_from_fqdn(fqdn: str) -> str:
    """Extracts hostname from fqdn-like string

    For example, R1.cisco.com -> R1,  sw1 -> sw1"
    """
    return fqdn.split(".")[0]


def update_lldp_neighbors(task):
    url = constants.RESTCONF_ROOT + constants.OPENCONFIG_LLDP_NEIGHBORS_ENDPOINT
    url = url.format(host=task.host.hostname)
    response = requests.get(
        url,
        headers=constants.HEADERS,
        auth=(task.host.username, task.host.password),
        verify=False,
    )
    response.raise_for_status()
    result = response.json()["openconfig-lldp:interface"]
    device_name = task.host.name
    host_interfaces = {}
    task.host.data["interfaces"] = host_interfaces
    for interface_info in result:
        interface_name = interface_info["name"]
        interface = Interface(interface_name, device_name)
        neighbors = interface_info.get("neighbors")
        if not neighbors:
            continue
        for neighbor_info in neighbors["neighbor"]:
            neighbor_state = neighbor_info["state"]
            remote_interface_name = neighbor_state["port-description"]
            remote_device_fqdn = neighbor_state["system-name"]
            remote_device_name = extract_hostname_from_fqdn(remote_device_fqdn)
            remote_interface = Interface(remote_interface_name, remote_device_name)
            interface.neighbors.append(remote_interface)

        host_interfaces[interface.name] = interface


def build_graph(hosts: List[Host]) -> Tuple[nx.Graph, List[Dict[Tuple[str, str], str]]]:
    edge_labels: List[Dict[Tuple[str, str], str]] = [{}, {}]
    links = set([
        interface.link_from_neighbors()
        for host in hosts
        for interface in host.data["interfaces"].values()
    ])
    graph = nx.Graph()
    graph.add_nodes_from([host.name for host in hosts])

    for link in links:
        if not link.is_point_to_point:
            continue

        edge: Tuple[str, str] = tuple(
            interface.device_name
            for interface in link.interfaces
        )
        for i, interface in enumerate(link.interfaces):
            edge_labels[i][edge] = interface.short_name
        graph.add_edge(*edge)
    logger.info("The network graph was built")
    return graph, edge_labels


def draw_and_save_topology(graph: nx.Graph, edge_labels: List[Dict[Tuple[str, str], str]]) -> None:
    plt.figure(1, figsize=(12, 12))
    pos = nx.spring_layout(graph)
    nx.draw_networkx(graph, pos, node_size=1300, node_color='orange')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels[0], label_pos=0.8)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels[1], label_pos=0.2)
    filename = "topology.png"
    plt.savefig(filename)
    logger.info("The network topology diagram has been saved to %r", filename)


def main():
    start_time = time.time()
    nr = InitNornir("config.yaml", configure_logging=False)
    # result = nr.run(
    #     task=netmiko_send_command,
    #     command_string="show cdp neighbors detail",
    #     use_textfsm=True,
    # )
    nr.run(
        task=update_lldp_neighbors,
    )
    logger.info("LLDP details were successfully fetched using RESTCONF and OPENCONFIG")
    milestone = time.time()
    time_to_run = milestone - start_time
    print(
        f"{Fore.RED}It took {time_to_run:.2f} seconds to get and parse LLDP details"
        f"{Fore.RESET}"
    )
    graph, edge_labels = build_graph(nr.inventory.hosts.values())
    draw_and_save_topology(graph, edge_labels)
    time_to_run = time.time() - milestone
    print(
        f"{Fore.RED}It took additional {time_to_run:.2f} seconds "
        f"to draw and save the network topology{Fore.RESET}"
    )


if __name__ == "__main__":
    main()
