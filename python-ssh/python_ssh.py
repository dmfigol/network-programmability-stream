#!/usr/bin/env python3
from copy import deepcopy
from pprint import pprint

import netmiko
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


def collect_outputs(devices, commands):
    """
    Collects commands from the dictionary of devices

    Args:
        devices (dict): dictionary, where key is the hostname, value is netmiko connection dictionary
        commands (list): list of commands to be executed on every device

    Returns:
        dict: key is the hostname, value is string with all outputs
    """
    for device in devices:
        hostname = device.pop('hostname')
        connection = netmiko.ConnectHandler(**device)
        device_result = ['{0} {1} {0}'.format('=' * 20, hostname)]

        for command in commands:
            command_result = connection.send_command(command)
            device_result.append('{0} {1} {0}'.format('=' * 20, command))
            device_result.append(command_result)

        device_result_string = '\n\n'.join(device_result)
        connection.disconnect()
        yield device_result_string


def main():
    parsed_yaml = read_yaml()
    connection_params = form_connection_params_from_yaml(parsed_yaml, site=SITE_NAME)
    for device_result in collect_outputs(connection_params, COMMANDS_LIST):
        print(device_result)


if __name__ == '__main__':
    main()
