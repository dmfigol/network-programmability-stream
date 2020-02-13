import hvac
import decouple
from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from typing import Sequence, Dict

HOSTS = [
    '10.48.18.26',
    '10.48.18.30'
]

PARAMS = {
    'device_type': 'cisco_ios'
}

COMMANDS = [
    'show version',
    'show ip int brief',
    'show plat soft status control-processor brief'
]

VAULT_SERVER = 'http://localhost:8200'

# device_conn = ConnectHandler(**device_params)
#
# parsed_values = dict()
# parsed_values.update(parse_show_version(device_conn.send_command('show version')))
# parsed_values.update(
#     parse_show_mac_address_table(device_conn.send_command('show mac address-table')))
#
# result = '{hostname} MAC address table:\n{mac_address_table}'.format(**parsed_values)
# device_conn.disconnect()
# return result

def form_device_params(host: str, params: Dict[str, str]) -> Dict[str, str]:
    return {'host': host, **params, **PARAMS}


def get_username_password(vault_server, vault_token: str) -> Dict[str, str]:
    vault = hvac.Client(url=vault_server, token=vault_token)
    result = {
        'username': vault.read('kv/CSR_USERNAME')['data']['value'],
        'password': vault.read('kv/CSR_PASSWORD')['data']['value'],
    }
    return result


def get_outputs(device_info: Dict[str, str], commands: Sequence[str]) -> Dict[str, str]:
    result = {}
    with ConnectHandler(**device_info) as device_conn:
        for command in commands:
            result[command] = device_conn.send_command(command)
    return result


def main():
    params = get_username_password(VAULT_SERVER, decouple.config('VAULT_TOKEN'))
    worker = partial(get_outputs, commands=COMMANDS)
    devices_params = (form_device_params(host, params) for host in HOSTS)
    with ThreadPoolExecutor(2) as pool:
        results = pool.map(worker, devices_params)

    for host, result in zip(HOSTS, results):
        print(f'===== Device: {host} =====')
        for command, output in result.items():
            print(f'=== output from {command!r} ===')
            print(output, end='\n=========\n')



if __name__ == '__main__':
    main()
