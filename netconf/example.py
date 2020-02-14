#!/usr/bin/env python
import xml.dom.minidom
import json

import jinja2
import xmltodict
from ncclient import manager

CONNECTION_PARAMS = {
    'host': '192.168.153.101',
    'username': 'cisco',
    'password': 'cisco',
    'hostkey_verify': False,
}

CONFIG_DATA = {
    'loopbacks': [
        {
            'number': '1500',
            'description': 'This one has a description'
        },
        {
            'number': '1501',
            'ipv4_address': '100.64.151.1',
            'ipv4_mask': '255.255.255.0',
        }
    ]
}

TEMPLATES = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))


def prettify_xml(xml_string):
    xml_dom = xml.dom.minidom.parseString(str(xml_string))
    return xml_dom.toprettyxml()


def get_config(nc_conn):
    nc_reply = nc_conn.get_config(source='running')
    current_config = xmltodict.parse(nc_reply.data_xml)['data']
    # print(json.dumps(current_config, indent=2))
    sw_version = current_config['native']['version']
    hostname = current_config['native']['hostname']
    print(f'SW version: {sw_version}')
    print(f'hostname: {hostname}')


def configure_device(nc_conn, config_data, template_name):
    template = TEMPLATES.get_template(template_name)
    config = template.render(config_data)
    nc_reply = nc_conn.edit_config(
        target='running',
        config=config,
    )
    if nc_reply.ok:
        print("Successfully performed NETCONF edit config operation")


def main():
    with manager.connect(**CONNECTION_PARAMS) as nc_connection:
        get_config(nc_connection)
        configure_device(
            nc_connection,
            config_data=CONFIG_DATA,
            template_name='loopbacks.j2'
        )


if __name__ == '__main__':
    main()
