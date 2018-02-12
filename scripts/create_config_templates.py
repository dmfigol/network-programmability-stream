import os
import re
import json
from ipaddress import IPv4Interface

import requests

from helper import read_yaml, form_device_params_from_yaml

NETBOX_API_ROOT = 'http://netbox:32774/api'
NETBOX_DEVICES_ENDPOINT = '/dcim/devices/'
NETBOX_INTERFACES_ENDPOINT = '/dcim/interfaces/'
NETBOX_SITES_ENDPOINT = '/dcim/sites/'
NETBOX_IP_ADDRESSES_ENDPOINT = '/ipam/ip-addresses/'
NETBOX_VLANS_ENDPOINT = '/ipam/vlans/'

L2_INTERFACE_NAME_RE = re.compile(r'(?P<interface_name>.+?)\.(?P<vlan_number>\d+)')

SITES = [
    {
        'name': 'Krakow',
        'slug': 'krk'
    },
    {
        'name': 'Reykjavík',
        'slug': 'rkvk'
    }
]


class NetboxAPITokenNotFound(Exception):
    pass


def form_headers():
    api_token = os.environ.get('NETBOX_API_TOKEN')
    if api_token is None:
        raise NetboxAPITokenNotFound('NETBOX_API_TOKEN was not found in environmental variables')

    headers = {
        'Authorization': 'Token {}'.format(api_token),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    return headers


def create_vlan(vlan_number, vendor='cisco'):
    headers = form_headers()
    query_params = {
        'vid': vlan_number
    }
    vlan_netbox_dict = requests.get(NETBOX_API_ROOT + NETBOX_VLANS_ENDPOINT,
                                     headers=headers, params=query_params).json()['results'][0]
    vlan_name = vlan_netbox_dict['name']
    description = vlan_netbox_dict['description']
    config_lines = []
    if vendor.lower() == 'cisco':
        config_lines.append(f' name {vlan_name}')
        config_lines.append(f' description {description}')
        vlan_config_content = '\n'.join(config_lines)
        result = f'vlan {vlan_number}\n{vlan_config_content}\n!'
    return result


def create_device_config(name):
    headers = form_headers()
    result = []

    query_params = {
        'name': name,
    }

    device_netbox_dict = requests.get(NETBOX_API_ROOT + NETBOX_DEVICES_ENDPOINT,
                                      params=query_params, headers=headers).json()['results']
    manufacturer = device_netbox_dict[0]['device_type']['manufacturer']['name']
    device_model = device_netbox_dict[0]['device_type']['model']
    if 'l2' in device_model.lower():
        device_type = 'switch'
    else:
        device_type = 'router'

    query_params = {
        'device': name,
    }

    ip_address_netbox_dict = requests.get(NETBOX_API_ROOT + NETBOX_IP_ADDRESSES_ENDPOINT,
                                          params=query_params, headers=headers).json()['results']

    device_interfaces_netbox_dict = requests.get(NETBOX_API_ROOT + NETBOX_INTERFACES_ENDPOINT,
                                                 params=query_params, headers=headers).json()['results']

    # if manufacturer.lower() == 'cisco' and 'l2' in device_model.lower():

    if manufacturer.lower() == 'cisco':
        result.append(f'hostname {name}')
        for interface_dict in ip_address_netbox_dict:
            interface_config_list = []

            interface_name = interface_dict['interface']['name']
            if interface_dict['interface']['form_factor']['label'] != 'Virtual' and device_type == 'switch':
                interface_config_list.append(' no switchport')

            interface_connection = interface_dict['interface'].get('interface_connection')
            if interface_connection is not None:
                remote_interface = interface_connection['interface']
                description = f"To {remote_interface['device']['name']} {remote_interface['name']}"
            else:
                description = interface_dict['description']

            interface_config_list.append(f' description {description}')

            ip_address = IPv4Interface(interface_dict['address'])
            interface_config_list.append(f' ip address {ip_address.ip} {ip_address.netmask}')
            if interface_dict['interface']['enabled']:
                interface_config_list.append(' no shutdown')

            interface_config = '\n'.join(interface_config_list)
            result.append(f'interface {interface_name}\n{interface_config}\n!')

        vlans_config_list = []
        for interface_dict in device_interfaces_netbox_dict:
            interface_name = interface_dict['name']
            description = interface_dict['description']
            if 'access' in description.lower():
                match = L2_INTERFACE_NAME_RE.match(interface_name)
                interface_name = match.group('interface_name')
                vlan_number = match.group('vlan_number')
                interface_config_list = list()
                vlans_config_list.append(create_vlan(vlan_number, manufacturer))

                interface_config_list.append(' switchport mode access')
                interface_config_list.append(f' switchport access vlan {vlan_number}')

                if interface_dict['enabled']:
                    interface_config_list.append(' no shutdown')

                interface_config = '\n'.join(interface_config_list)
                result.append(f'interface {interface_name}\n{interface_config}\n!')

    vlans_config = '\n'.join(vlans_config_list)
    result.insert(1, vlans_config)
    return '\n'.join(result)


def main():
    config = create_device_config('SJ-SW1')
    print(config)


if __name__ == '__main__':
    main()
