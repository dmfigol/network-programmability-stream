import itertools
import logging
from collections import deque, defaultdict, OrderedDict
from pathlib import Path
from typing import (
    Dict,
    List,
    Iterable,
    Any,
    Set,
    NamedTuple,
    Optional,
    ValuesView,
    Iterator,
    Deque,
    DefaultDict,
)

import ruamel.yaml
from mypy_extensions import TypedDict
from nornir.core.inventory import Inventory
from nornir.core.inventory import Host
from nornir.core.filter import F

import constants
from utils import roundup


YAML_FILENAME_EXTENSIONS = [".yml", ".yaml"]

YAML = ruamel.yaml.YAML(typ="safe")


ConnectionEnd = TypedDict(
    "ConnectionEnd",
    {"hostname": str, "port": str, "tag": str, "service": str, "vm": str, "portgroup_num": int, "update_vlan": bool},
    total=False,
)

Connection = List[ConnectionEnd]

VMDict = TypedDict("VMDict", {"name": str})
# TopologyDict = TypedDict("TopologyDict", {"connections": List[List[LinkDict]]})

logger = logging.getLogger("lab_system.deployment")


class Interface(NamedTuple):
    device_name: str
    num: Optional[int] = None
    name: Optional[str] = None


class Portgroup(NamedTuple):
    name: str
    vlan: Optional[int] = None

    def __eq__(self, other) -> bool:
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


DeviceMatrixConnections = Dict[str, Interface]


class VM:
    def __init__(self, name: str, pod: "Pod") -> None:
        self.name = name
        self.pod = pod
        self.portgroups: List[Portgroup] = []
        self.show_portgroups = False
        self.turn_on = True

    def __repr__(self):
        return f"VM(name={self.name!r})"


class Deployment:
    def __init__(self, topologies: Dict[str, Dict[str, Any]], inventory) -> None:
        self.topologies: Dict[str, Dict[str, Any]] = topologies
        self.inventory = inventory
        self.pod_id_to_pod: Dict[int, Pod] = {}
        self.unallocated_pod_gear = inventory.filter(
            F(pod="unallocated", has_parent_group="pod-gear")
        ).hosts
        self._load_topologies()
        self.free_matrix_connections = self._parse_matrix_switches()
        self.device_to_pod_mgmt_port = self._parse_pod_mgmt_ports()
        self.internet_vlans = self._parse_pair_routers()
        self.cur_dot1q_tunnel_vlan = constants.DOT1Q_TUNNEL_VLAN_START

        self._allocate_pod_gear()

    @property
    def pods(self) -> ValuesView["Pod"]:
        return self.pod_id_to_pod.values()

    @property
    def vms(self) -> Iterator[VM]:
        return itertools.chain.from_iterable(pod.vms for pod in self.pods)

    @property
    def matrix_switches(self) -> Iterable[Host]:
        return self.inventory.filter(
            F(groups__contains="matrix-switches")
        ).hosts.values()

    def get_device(self, device_name: str) -> Host:
        return self.inventory.hosts[device_name]

    def _load_topologies(self) -> None:
        topologies_dir = Path("topologies")
        for topology_name, topology_info in self.topologies.items():
            topology_dir = topologies_dir / topology_name
            if not topology_dir.is_dir():
                raise OSError(f'Directory "{topology_dir}" was not found')
            configs_dir = topology_dir / "configs"
            with open(topology_dir / "topology.yml") as f:
                logger.info('Loading topology "%s"', topology_name)
                details = YAML.load(f)
            for device_name, device in details.get('devices', {}).items():
                startup_config_path = configs_dir / f'{device_name}.txt'
                if startup_config_path.is_file():
                    with open(startup_config_path) as f:
                        device["startup_config"] = f.read()
            details["configs_dir"] = str(configs_dir)
            topology_info.update(details)

    def _parse_matrix_switches(self) -> DefaultDict[str, DeviceMatrixConnections]:
        result: DefaultDict[str, DeviceMatrixConnections] = defaultdict(OrderedDict)
        for matrix_switch in self.matrix_switches:
            for interface_num, interface in enumerate(
                matrix_switch.get("interfaces", [])
            ):
                connected_device_info = interface.get("connected_device")
                if connected_device_info:
                    device_name = interface["connected_device"]["name"]
                    port = interface["connected_device"].get("port")
                    if port in result[device_name]:
                        matrix_interface = result[device_name][port]
                        raise ValueError(
                            f"{device_name} {port} can't be mapped to "
                            f"{matrix_switch.name} {interface['name']} because it was "
                            f"already mapped to {matrix_interface.device_name} "
                            f"{matrix_interface.name}"
                        )
                    result[device_name][port] = Interface(
                        matrix_switch.name, interface_num, interface["name"]
                    )

                elif interface.get("mode") == "dot1q-tunnel":
                    raise ValueError(
                        f"Interface {interface['name']} on the switch "
                        f"{matrix_switch.name} is 'dot1q-tunnel'"
                        f"but does not have connected_device variable"
                    )
        return result

    def _parse_pod_mgmt_ports(self) -> Dict[str, Interface]:
        result: Dict[str, Interface] = {}
        pod_mgmt_switches = self.inventory.filter(
            F(groups__contains="pod-mgmt")
        ).hosts.values()
        for pod_mgmt_switch in pod_mgmt_switches:
            for int_num, interface in enumerate(pod_mgmt_switch.get("interfaces")):
                interface_name = interface["name"]
                connected_device = interface.get("connected_device")
                if connected_device and not interface.get("management", False):
                    device = connected_device["name"]
                    if device in result:
                        connected_interface = result[device]
                        raise ValueError(
                            f"Device {device} is already connected to "
                            f"{connected_interface.device_name} "
                            f"{connected_interface.name}"
                        )
                    connected_interface = Interface(
                        pod_mgmt_switch.name, int_num, interface_name
                    )
                    result[device] = connected_interface
        return result

    def _parse_pair_routers(self) -> Deque[int]:
        result: Deque[int] = deque()
        presence_set: Set[int] = set()
        pair_routers = self.inventory.filter(
            F(groups__contains="pair-routers")
        ).hosts.values()
        for router in pair_routers:
            for interface in router.get("interfaces", []):
                if interface.get("service") == "internet":
                    vlan = interface.get("vlan")
                    if not isinstance(vlan, int):
                        raise ValueError(
                            f"{router.name} {interface.get('name')} has vlan value is "
                            f"{vlan!r} when it should be of type int"
                        )
                    if vlan in presence_set:
                        raise ValueError(
                            f"{router.name} {interface.get('name')} has vlan value "
                            f"{vlan} which is already in use"
                        )
                    result.append(vlan)
                    presence_set.add(vlan)
        return result

    def _increase_dot1q_tunnel_vlan(self) -> None:
        self.cur_dot1q_tunnel_vlan = roundup(self.cur_dot1q_tunnel_vlan)

    def _allocate_pod_gear(self) -> None:
        topology_pod_id_start = 0
        for topology_name, topology_info in self.topologies.items():
            topology_pod_id_start += constants.POD_ID_STEP
            for i in range(topology_info["quantity"]):
                pod_id = topology_pod_id_start + i + 1
                pod = Pod(pod_id, topology_name, deployment=self)
                self.pod_id_to_pod[pod_id] = pod
                logger.info(f'Allocated pod #{pod_id}, topology: "{topology_name}"')
                self._increase_dot1q_tunnel_vlan()


class Pod:
    def __init__(self, pod_id: int, topology_name: str, deployment: Deployment) -> None:
        self.id = pod_id
        self.deployment = deployment
        self.topology_name = topology_name

        topology_info = self.deployment.topologies[topology_name]
        self.devices = topology_info.get("devices", {})
        self.vm_name_to_vm: Dict[str, VM] = {}
        self.connections = topology_info.get("connections", [])

        self.hostname_to_device: Dict[str, Host] = {}

        self._update_vms(topology_info.get("vms", []))
        self._allocate_gear()
        self._process_connections()
        self._flatten_template_data()

    @property
    def vms(self) -> ValuesView[VM]:
        return self.vm_name_to_vm.values()

    @property
    def sequence_num(self) -> int:
        return self.id % constants.POD_ID_STEP

    @property
    def inventory(self) -> Inventory:
        return self.deployment.inventory

    @property
    def free_matrix_connections(
        self
    ) -> DefaultDict[str, DeviceMatrixConnections]:
        return self.deployment.free_matrix_connections

    @property
    def unallocated_pod_gear(self) -> Dict[str, Host]:
        return self.deployment.unallocated_pod_gear

    def get_device(
        self, hostname: Optional[str] = None, device_name: Optional[str] = None
    ) -> Host:
        if hostname:
            return self.hostname_to_device[hostname]
        elif device_name:
            return self.deployment.get_device(device_name)
        else:
            raise ValueError(f"Neither hostname nor device_name were provided")

    def get_vm_name(self, vm_name: str) -> str:
        return f"{self.topology_name}__{vm_name}__{self.sequence_num:02d}"

    def get_vm_portgroup_name(self, vm_name: str, portgroup_num: Optional[int] = None) -> str:
        pod_vm_name = self.get_vm_name(vm_name)
        if portgroup_num is None:
            return pod_vm_name
        else:
            return f"{pod_vm_name}__{portgroup_num:02d}"

    def _update_vms(self, vms: List[VMDict]) -> None:
        for vm_info in vms:
            vm_name = vm_info["name"]
            full_vm_name = self.get_vm_name(vm_name)
            self.vm_name_to_vm[vm_name] = VM(full_vm_name, self)

    def _process_special_reset_device(self, device: Host) -> None:
        device.data["special_reset"] = True
        pod_mgmt_interface = self.deployment.device_to_pod_mgmt_port[device.name]
        device_name = pod_mgmt_interface.device_name
        pod_mgmt_interfaces = self.get_device(device_name=device_name).get("interfaces")
        pod_mgmt_interfaces[pod_mgmt_interface.num]["shutdown"] = True

    def _allocate_gear(self) -> None:
        for device, device_info in self.devices.items():
            unallocated = True
            group = device_info.get("group")
            if group:
                group = f"{group}__{self.sequence_num:02d}"
            else:
                group = "dynamic"
            tags = device_info.get("tags", [])
            exclude_tags = device_info.get("exclude_tags", [])
            special_reset = device_info.get("special_reset", False)
            for free_device_name, free_device in list(
                self.unallocated_pod_gear.items()
            ):
                free_device_tags = free_device.get("tags", [])
                if (
                    free_device.has_parent_group(group)
                    and all(tag in free_device_tags for tag in tags)
                    and not any(tag in free_device_tags for tag in exclude_tags)
                ):
                    self.unallocated_pod_gear.pop(free_device_name)
                    free_device.data["pod"] = self.id
                    free_device.data["lab_hostname"] = device
                    startup_config = device_info.get("startup_config")
                    if startup_config is not None:
                        free_device.data["startup_config"] = startup_config
                    self.hostname_to_device[device] = free_device
                    if special_reset:
                        self._process_special_reset_device(free_device)
                    unallocated = False
                    break
            if unallocated:
                raise ValueError(
                    f'Cannot allocate pod #{self.id}, topology "{self.topology_name}" '
                    f"because an unallocated device with tags: {tags} and "
                    f'the group "{group}" was not found'
                )

    @staticmethod
    def skip_tunnel_creation(connection: Connection) -> bool:
        return any(
            "vm" in connection_end and not connection_end.get("update_vlan", True)
            for connection_end in connection
        )

    @staticmethod
    def is_internet_service(connection: Connection) -> bool:
        return {"service": "internet"} in connection

    def _process_matrix_bypass(self, connection: Connection) -> None:
        if len(connection) != 2:
            raise ValueError(
                f"update_vlan is set to False but there are "
                f"{len(connection)} devices. Should be exactly 2."
            )
        device = None
        port_num = None
        vm = None
        for host in connection:
            if "hostname" in host:
                device = self.get_device(host["hostname"])
            if "port" in host:
                port = host["port"]
                port_num_match = constants.INTERFACE_NAME_RE.search(port)
                if port_num_match is None:
                    raise ValueError(
                        f"Port {port} could not be parsed with regular expression"
                    )
                port_num = port_num_match.group("interface_num").replace("/", "-")
            if "vm" in host:
                vm = self.vm_name_to_vm[host["vm"]]
        if device and port_num and vm:
            portgroup = Portgroup(f"{device.name}__{port_num}")
            vm.portgroups.append(portgroup)
            vm.show_portgroups = True
        else:
            raise ValueError(
                f"Either 'device' or 'port' or 'vm' was not specified in: {connection}"
            )

    def _process_connection_end(self, connection_end: ConnectionEnd, dot1q_vlan: int) -> None:
        if "hostname" in connection_end:
            hostname = connection_end["hostname"]
            device = self.get_device(hostname)
            device_free_matrix_ports = self.free_matrix_connections[device.name]
            if "port" in connection_end:
                port = connection_end["port"]
                matrix_int = device_free_matrix_ports.pop(port, None)
                if matrix_int is None:
                    raise ValueError(
                        f'Port {port!r} on the device {device.name!r} is not available '
                        f'for matrix connection'
                    )
            else:
                try:
                    port, matrix_int = device_free_matrix_ports.popitem(last=False)  # type: ignore
                except KeyError:
                    raise ValueError(
                        f'No more matrix free connections left for {device.name!r}'
                    )

                template_data = device.data.get("template_data")
                if template_data is None:
                    template_data = {'interfaces': {}}
                    device.data["template_data"] = template_data
                if 'tag' in connection_end:
                    tag = connection_end['tag']
                else:
                    int_num = len(device.data["template_data"]["interfaces"]) + 1
                    tag = f'interface_{int_num}'
                template_data["interfaces"][tag] = port

            matrix_switch = self.get_device(device_name=matrix_int.device_name)
            matrix_int_num = matrix_int.num
            matrix_int_details = matrix_switch["interfaces"][matrix_int_num]
            matrix_int_details["access_vlan"] = dot1q_vlan
            matrix_int_details["shutdown"] = False
            matrix_int_details["description"] += (
                f" | pod: {self.id} | hostname: {hostname}"
            )
        elif "vm" in connection_end:
            vm_name = connection_end["vm"]
            full_vm_name = self.get_vm_name(vm_name)
            vm = VM(full_vm_name, self)
            self.vm_name_to_vm[vm_name] = vm
            portgroup_num = connection_end.get("portgroup_num")
            portgroup_name = self.get_vm_portgroup_name(vm_name, portgroup_num)
            vm.portgroups.append(Portgroup(portgroup_name, vlan=dot1q_vlan))
        elif "service" in connection_end:
            pass

    def _process_matrix_connection(
        self, connection: Connection, dot1q_vlan: int
    ) -> None:
        for connection_end in connection:
            self._process_connection_end(connection_end, dot1q_vlan)

    def _process_connections(self) -> None:
        for connection in self.connections:
            if self.skip_tunnel_creation(connection):
                self._process_matrix_bypass(connection)
            else:
                if self.is_internet_service(connection):
                    dot1q_vlan = self.deployment.internet_vlans.popleft()
                else:
                    dot1q_vlan = self.deployment.cur_dot1q_tunnel_vlan
                    self.deployment.cur_dot1q_tunnel_vlan += 1
                self._process_matrix_connection(connection, dot1q_vlan)

    def _flatten_template_data(self) -> None:
        for device in self.hostname_to_device.values():
            if 'template_data' in device.data:
                template_data = device.data["template_data"]
                template_data.update(template_data.pop('interfaces', {}))
