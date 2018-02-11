import re
import time
import asyncio

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


def read_inventory_yaml(file_name=INVENTORY_FILE):
    with open(file_name) as f:
        result = yaml.load(f)
    return result


def get_switches_ip_addresses():
    return read_inventory_yaml()['switches']


def parse_show_version(cli_output):
    result = dict()
    for regexp in SHOW_VERSION_REGEXP_LIST:
        result.update(regexp.search(cli_output).groupdict())
    return result


def parse_show_mac_address_table(cli_output):
    mac_address_table = [
        match.groupdict()
        for match in SHOW_MAC_ADDR_TABLE_RE.finditer(cli_output)
    ]

    mac_address_table.sort(key=lambda x: x['interface_name'])

    result_str = '\n'.join(
        '{vlan_number:>4}{mac_address:>18}{type:>11}{interface_name:>10}'.format(**mac_address_entry)
        for mac_address_entry in mac_address_table
    )
    result = {
        'mac_address_table_list': mac_address_table,
        'mac_address_table': result_str
    }
    return result


async def get_mac_address_table(host):
    device_params = GLOBAL_DEVICE_PARAMS.copy()
    device_params['host'] = host
    parsed_values = dict()

    async with netdev.create(**device_params) as device_conn:
        show_version_output = await device_conn.send_command('show version')
        parsed_values.update(parse_show_version(show_version_output))

        show_mac_address_table_output = await device_conn.send_command('show mac address-table')
        parsed_values.update(parse_show_mac_address_table(show_mac_address_table_output))
        result = '{hostname} MAC address table:\n{mac_address_table}'.format(**parsed_values)
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
