#!/usr/bin/env python
import xml.dom.minidom
import json

import jinja2
import xmltodict
from ncclient import manager

CONNECTION_PARAMS = {
    'host': '192.168.122.11',
    'username': 'admin',
    'password': 'admin',
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
    return xml_dom.toprettyxml(indent=" ")


def get_config(connection_params):
    with manager.connect(**connection_params) as connection:
        current_config_xml = connection.get_config(source='running').data_xml
        current_config = xmltodict.parse(current_config_xml)['data']
        # print(json.dumps(current_config, indent=2))
        sw_version = current_config['native']['version']
        hostname = current_config['native']['hostname']
        print(f'SW version: {sw_version}')
        print(f'hostname: {hostname}')


def configure_device(connection_params, config_data, template_name):
    template = TEMPLATES.get_template(template_name)
    config = template.render(config_data)

    with manager.connect(**connection_params) as connection:
        response_xml = connection.edit_config(
            target='running',
            config=config,
        )


def main():
    configure_device(
        connection_params=CONNECTION_PARAMS,
        config_data=CONFIG_DATA,
        template_name='loopbacks.j2'
    )


if __name__ == '__main__':
    main()
