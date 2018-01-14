#!/usr/bin/env python3
import asyncio
from copy import deepcopy

import netdev
import yaml

from helper import read_yaml, form_connection_params_from_yaml


COMMANDS_LIST = [
    'show clock',
    'show version',
    'show inventory',
    'show ip interface brief'
]


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
