#!/usr/bin/env python3
import asyncio
from copy import deepcopy
from pprint import pprint


import netdev
import yaml

SITE_NAME = 'SJ-HQ'

COMMANDS_LIST = [
    'show clock',
    'show version',
    'show inventory',
    'show ip interface brief'
]


def read_yaml(path='inventory.yml'):
    """
    Reads inventory yaml file and return dictionary with parsed values

    Args:
        path (str): path to inventory YAML

    Returns:
        dict: prased inventory YAML values
    """
    with open(path) as f:
        yaml_content = yaml.load(f.read())
    return yaml_content


def form_connection_params_from_yaml(parsed_yaml, site='all'):
    """
    Form dictionary of netmiko connections parameters for all devices on the site
    
    Args:
        parsed_yaml (dict): dictionary with parsed yaml file
        site (str): name of the site. Default is 'all'

    Returns:
        dict: key is hostname, value is dictionary containing netmiko connection parameters for the host
    """
    parsed_yaml = deepcopy(parsed_yaml)
    global_params = parsed_yaml['all']['vars']
    site_dict = parsed_yaml['all']['groups'].get(site)
    if site_dict is None:
        raise KeyError('Site {} is not specified in inventory YAML file'.format(site))

    for host in site_dict['hosts']:
        host_dict = {}
        host_dict.update(global_params)
        host_dict.update(host)
        yield host_dict


async def collect_outputs(device_params, commands):
    """
    Collects commands from the dictionary of devices

    Args:
        device_params (dict): dictionary, where key is the hostname, value is netmiko connection dictionary
        commands (list): list of commands to be executed on every device

    Returns:
        dict: key is the hostname, value is string with all outputs
    """
    hostname = device_params.pop('hostname')
    async with netdev.create(**device_params) as connection:
        device_result = ['{0} {1} {0}'.format('=' * 20, hostname)]

        for command in commands:
            command_result = await connection.send_command(command)
            device_result.append('{0} {1} {0}'.format('=' * 20, command))
            device_result.append(command_result)

        device_result_string = '\n\n'.join(device_result)
        return device_result_string


def main():
    parsed_yaml = read_yaml()
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(collect_outputs(device, COMMANDS_LIST))
             for device in form_connection_params_from_yaml(parsed_yaml, site=SITE_NAME)]
    loop.run_until_complete(asyncio.wait(tasks))
    for task in tasks:
        print(task.result())


if __name__ == '__main__':
    main()
