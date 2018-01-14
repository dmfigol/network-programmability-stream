from copy import deepcopy

import yaml


SITES = {
    'sjc': 1,
    'bru': 2,
}

DEVICE_TYPES = {
    'csr1000v': 1,
    'iosv-l2': 2,
}

DEVICE_ROLES = {
    'access': 1,
    'edge': 2,
    'core': 3
}


def read_yaml(path='inventory.yml'):
    """
    Reads inventory yaml file and return dictionary with parsed values

    Args:
        path (str): path to inventory YAML

    Returns:
        dict: parsed inventory YAML values
    """
    with open(path) as f:
        yaml_content = yaml.load(f.read())
    return yaml_content


def form_connection_params_from_yaml(parsed_yaml, site_name=None):
    """
    Form dictionary of netmiko connections parameters for all devices on the site

    Args:
        parsed_yaml (dict): dictionary with parsed yaml file
        site_name (str): name of the site. Default is 'all'

    Returns:
        dict: key is hostname, value is dictionary containing netmiko connection parameters for the host
    """
    parsed_yaml = deepcopy(parsed_yaml)
    global_params = parsed_yaml['all']['vars']
    found = False
    for site_dict in parsed_yaml['all']['sites']:
        if not site_name or site_dict['name'] == site_name:
            for host in site_dict['hosts']:
                host_dict = {}
                if 'device_type_netmiko' in host:
                    host['device_type'] = host.pop('device_type_netmiko')
                host_dict.update(global_params)
                host_dict.update(host)
                yield host_dict

    if site_name is not None and not found:
        raise KeyError('Site {} is not specified in inventory YAML file'.format(site_name))


def form_device_params_from_yaml(parsed_yaml):
    """
    Form dictionary of device parameters for all devices on the site to import to Netbox

    Args:
        parsed_yaml (dict): dictionary with parsed yaml file

    Returns:
        dict: key is hostname, value is dictionary containing device parameter for import to netbox
    """
    parsed_yaml = deepcopy(parsed_yaml)
    for site_dict in parsed_yaml['all']['sites']:
        site_name = site_dict['name']
        site_id = SITES.get(site_name)
        for host_dict in site_dict['hosts']:
            device_params = dict()
            device_params['name'] = host_dict['hostname']
            device_params['site_id'] = site_id
            device_params['device_type_id'] = DEVICE_TYPES.get(host_dict.get('device_type'))
            device_params['device_role_id'] = DEVICE_ROLES.get(host_dict.get('device_role'))
            yield device_params
