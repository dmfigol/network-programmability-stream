import re
import time
import asyncio
from collections import defaultdict

import netdev
from decouple import config
import yaml


INVENTORY_FILE = 'mac_address_table_inventory.yml'

TEST_IP_LIST = ['10.48.18.24', '10.48.18.30']

GLOBAL_DEVICE_PARAMS = {
        'device_type': 'cisco_ios',
        'username': config('USERNAME'),
        'password': config('PASSWORD')
}

SHOW_VERSION_REGEXP_LIST = [
    re.compile(r'(?P<hostname>^\S+)\s+uptime', re.M),
    re.compile(r'^System image file is "(?P<boot_image>\S+)"\s?', re.M)
]

SHOW_MAC_ADDR_TABLE_RE = re.compile(
    r'^\s*(?P<vlan_number>\d+)\s+(?P<mac_address>\S+)\s+(?P<type>\S+)\s+(?P<interface_name>\S+)', re.M
)

CDP_NEIGHBOR_RE = re.compile(
    r'^Device ID: (?P<remote_hostname>\S+).+?^Interface: (?P<local_interface>\S+),\s+Port ID (outgoing port): (?P<remote_hostname>\S+)',
    re.M | re.S
)

LLDP_NEIGHBOR_RE = re.compile(
    r'^Local Intf: (?P<local_interface>\S+).+?^Port id: (?P<remote_interface>\S+).+?System Name: (?P<remote_hostname>\S+)',
    re.M | re.S
)

NEIGHBOR_SPLIT_RE = re.compile(r'\n\n-{6,}\n')
INTERFACE_NAME_RE = re.compile(r'(?P<interface_type>[a-zA-Z\-]+)(?P<interface_number>[\d/.\-]+)')

def read_inventory_yaml(file_name=INVENTORY_FILE):
    with open(file_name) as f:
        result = yaml.load(f)
    return result


def get_switches_ip_addresses():
    return read_inventory_yaml()['switches']


def shorten_interface_name(interface_name):
    match = INTERFACE_NAME_RE.match(interface_name)
    if match is not None:
        parsed_values = match.groupdict()
        parsed_values['interface_type'] = parsed_values['interface_type'][:2]
        return '{interface_type}{interface_number}'.format(**parsed_values)
    return interface_name


def parse_show_version(cli_output):
    result = dict()
    for regexp in SHOW_VERSION_REGEXP_LIST:
        result.update(regexp.search(cli_output).groupdict())
    return result


def parse_show_mac_address_table(cli_output, neighbors):
    def get_interface_neighbors_string(interface_name):
        interface_neighbors = neighbors.get(interface_name)
        if interface_neighbors is not None:
            return ', '.join('{remote_hostname} {remote_interface} {protocol}'.format(**interface_neighbors))
        return '-'

    mac_address_table = [
        match.groupdict()
        for match in SHOW_MAC_ADDR_TABLE_RE.finditer(cli_output)
    ]

    mac_address_table.sort(key=lambda x: x['interface_name'])

    result_list = []
    for mac_address_entry in mac_address_table:
        mac_address_entry['neighbors_string'] = get_interface_neighbors_string(mac_address_entry['interface_name'])
        result_list.append(
            '{vlan_number:>4}{mac_address:>18}{type:>11}{interface_name:>10}   {neighbors_string}'.format(
                **mac_address_entry
            )
        )
    result = {
        'mac_address_table_list': mac_address_table,
        'mac_address_table': '\n'.join(result_list)
    }
    return result


def parse_show_cdp_neighbors(cli_output, result):
    for neighbor_output in NEIGHBOR_SPLIT_RE.split(cli_output):
        match = CDP_NEIGHBOR_RE.search(neighbor_output)
        if match:
            parsed_values = match.groupdict()
            parsed_values['protocol'] = 'C'
            short_local_interface_name = shorten_interface_name(parsed_values.pop('local_interface'))
            parsed_values['remote_interface'] = shorten_interface_name(parsed_values['remote_interface'])
            result[short_local_interface_name].append(parsed_values)


def parse_show_lldp_neighbors(cli_output, result):
    for neighbor_output in NEIGHBOR_SPLIT_RE.split(cli_output):
        match = LLDP_NEIGHBOR_RE.search(neighbor_output)
        if match:
            parsed_values = match.groupdict()
            parsed_values['protocol'] = 'L'
            short_local_interface_name = parsed_values.pop('local_interface')
            result[short_local_interface_name].append(parsed_values)


async def get_mac_address_table(host):
    device_params = GLOBAL_DEVICE_PARAMS.copy()
    device_params['host'] = host
    parsed_values = dict()
    neighbors = defaultdict(list)

    async with netdev.create(**device_params) as device_conn:
        show_version_output = await device_conn.send_command('show version')
        parsed_values.update(parse_show_version(show_version_output))

        show_lldp_neighbor_output = await device_conn.send_command('show lldp neighbors detail')
        parse_show_lldp_neighbors(show_lldp_neighbor_output, neighbors)

        show_cdp_neighbor_output = await device_conn.send_command('show cdp neighbors detail')
        parse_show_cdp_neighbors(show_cdp_neighbor_output, neighbors)

        show_mac_address_table_output = await device_conn.send_command('show mac address-table')
        parsed_values.update(parse_show_mac_address_table(show_mac_address_table_output, neighbors))
        result = '{hostname} MAC address table:\n{mac_address_table}\n'.format(**parsed_values)
        return result


def main():
    start_time = time.time()

    ip_list = get_switches_ip_addresses()

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(get_mac_address_table(ip))
        for ip in ip_list
    ]

    loop.run_until_complete(asyncio.wait(tasks))

    for task in tasks:
        print(task.result())

    print('It took {} seconds to run'.format(time.time() - start_time))


if __name__ == '__main__':
    main()
