from napalm import get_network_driver

ARISTA_SW_PARAMS = {
    "hostname": "192.168.122.23", "username": "admin", "password": "admin"
}

CSW1_PARAMS = {
    "hostname": "192.168.122.31", "username": "admin", "password": "admin"
}

CONFIG = """interface Ethernet12
description Connected to PC3
"""


def main():
    arista_driver = get_network_driver("eos")
    ios_driver = get_network_driver("ios")
    arista_sw = arista_driver(**ARISTA_SW_PARAMS)

    with arista_driver(**ARISTA_SW_PARAMS) as arista_sw, :
        arista_sw.load_merge_candidate(config=CONFIG)
        print(arista_sw.compare_config())
        arista_sw.commit_config()
        print(arista_sw.get_facts())
        print(arista_sw.get_interface_counters())
        print(arista_sw.get_arp_table())



if __name__ == "__main__":
    main()
