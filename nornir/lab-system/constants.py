import re

POD_ID_STEP = 100
DOT1Q_TUNNEL_VLAN_START = 2100
INTERFACE_NAME_RE = re.compile(
    r"(?P<interface_type>[a-zA-Z\-_ ]*)(?P<interface_num>[\d.\/]*)"
)