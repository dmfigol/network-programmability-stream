import re
from typing import Optional, Tuple

from link import Link


INTERFACE_NAME_RE = re.compile(
    r"(?P<interface_type>[a-zA-Z\-_ ]*)(?P<interface_num>[\d.\/]*)"
)

NORMALIZED_INTERFACES = (
    "FastEthernet",
    "GigabitEthernet",
    "TenGigabitEthernet",
    "FortyGigabitEthernet",
    "Ethernet",
    "Loopback",
    "Serial",
    "Vlan",
    "Tunnel",
    "Portchannel",
    "Management",
)




class Interface:
    def __init__(self, name: str, device_name: Optional[str] = None) -> None:
        self.type, self.num = self.normalize_interface_name(name)
        self.device_name = device_name
        self.neighbors = []

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}("
            f"name={self.name!r}, "
            f"device_name={self.device_name!r})"
        )

    def __str__(self) -> str:
        return f"{self.device_name} {self.name}"

    def __lt__(self, other) -> bool:
        return (self.device_name, self.name) < (other.device_name, other.name)

    def __eq__(self, other) -> bool:
        return (self.name, self.device_name) == (other.name, other.device_name)

    def __hash__(self) -> int:
        return hash((self.name, self.device_name))

    @property
    def name(self) -> str:
        return self.type + self.num

    @property
    def short_name(self) -> str:
        return self.type[:2] + self.num

    def link_from_neighbors(self) -> Link:
        interfaces = [self, *self.neighbors]
        return Link(interfaces)

    @staticmethod
    def normalize_interface_name(interface_name: str) -> Tuple[str, str]:
        """Normalizes interface name

        For example:
            Gi0/1 is converted to GigabitEthernet1
            Te1/1 is converted to TenGigabitEthernet1/1
        """
        match = INTERFACE_NAME_RE.search(interface_name)
        if match:
            int_type = match.group("interface_type")
            normalized_int_type = Interface.normalize_interface_type(int_type)
            int_num = match.group("interface_num")
            return normalized_int_type, int_num
        raise ValueError(f"Does not recognize {interface_name} as an interface name")

    @staticmethod
    def normalize_interface_type(interface_type: str) -> str:
        """Normalizes interface type

        For example:
            G is converted to GigabitEthernet
            Te is converted to TenGigabitEthernet
        """
        int_type = interface_type.strip().lower()
        for norm_int_type in NORMALIZED_INTERFACES:
            if norm_int_type.lower().startswith(int_type):
                return norm_int_type

        return int_type
