import asyncio
import os
import re
import json
import sys
import time
from ipaddress import IPv4Interface

import aiohttp
import requests
import decouple
import jinja2
import netdev

from helper import read_yaml, form_connection_params_from_yaml

NETBOX_API_ROOT = "http://netbox:32768/api"
NETBOX_DEVICES_ENDPOINT = "/dcim/devices/"
NETBOX_INTERFACES_ENDPOINT = "/dcim/interfaces/"
NETBOX_SITES_ENDPOINT = "/dcim/sites/"
NETBOX_IP_ADDRESSES_ENDPOINT = "/ipam/ip-addresses/"
NETBOX_VLANS_ENDPOINT = "/ipam/vlans/"

L2_INTERFACE_NAME_RE = re.compile(r"(?P<interface_name>.+?)\.(?P<vlan_number>\d+)")

SITES = [{"name": "Krakow", "slug": "krk"}, {"name": "Reykjavík", "slug": "rkvk"}]

TEMPLATES = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))


class NetboxAPITokenNotFound(Exception):
    pass


def form_headers():
    api_token = decouple.config("NETBOX_API_TOKEN")
    if api_token is None:
        raise NetboxAPITokenNotFound(
            "NETBOX_API_TOKEN was not found in environmental variables"
        )

    headers = {
        "Authorization": "Token {}".format(api_token),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return headers


async def fetch_netbox_info(netbox_session, url, params):
    async with netbox_session.get(url, params=params) as response:
        result = await response.json()
        return result["results"]


async def create_vlan(netbox_session, vlan_number, vendor="cisco"):
    query_params = {"vid": vlan_number}
    vlan_netbox_dict = (
        await fetch_netbox_info(
            netbox_session, NETBOX_API_ROOT + NETBOX_VLANS_ENDPOINT, params=query_params
        )
    )[
        0
    ]
    vlan_name = vlan_netbox_dict["name"]
    description = vlan_netbox_dict["description"]
    config_lines = []
    if vendor.lower() == "cisco":
        config_lines.append(f" name {vlan_name}")
        config_lines.append(f" description {description}")
        vlan_config_content = "\n".join(config_lines)
        result = f"vlan {vlan_number}\n{vlan_config_content}\n!"
    return result


async def create_device_config(name):
    async with aiohttp.ClientSession(headers=form_headers()) as netbox_session:
        result = []

        query_params = {"name": name}

        device_netbox_dict = await fetch_netbox_info(
            netbox_session,
            NETBOX_API_ROOT + NETBOX_DEVICES_ENDPOINT,
            params=query_params,
        )
        manufacturer = device_netbox_dict[0]["device_type"]["manufacturer"]["name"]
        device_model = device_netbox_dict[0]["device_type"]["model"]
        if "l2" in device_model.lower():
            device_type = "switch"
        else:
            device_type = "router"

        query_params = {"device": name}

        ip_address_netbox_dict = await fetch_netbox_info(
            netbox_session,
            NETBOX_API_ROOT + NETBOX_IP_ADDRESSES_ENDPOINT,
            params=query_params,
        )

        device_interfaces_netbox_dict = await fetch_netbox_info(
            netbox_session,
            NETBOX_API_ROOT + NETBOX_INTERFACES_ENDPOINT,
            params=query_params,
        )

        # if manufacturer.lower() == 'cisco' and 'l2' in device_model.lower():

        vlans_config_list = []

        if manufacturer.lower() == "cisco":
            result.append(f"hostname {name}")
            for interface_dict in ip_address_netbox_dict:
                format_params = dict()

                format_params["interface_name"] = interface_dict["interface"]["name"]
                if interface_dict["interface"]["form_factor"][
                    "label"
                ] != "Virtual" and device_type == "switch":
                    format_params["switch_l3_interface"] = True

                interface_connection = interface_dict["interface"].get(
                    "interface_connection"
                )
                if interface_connection is not None:
                    remote_interface = interface_connection["interface"]
                    format_params["description"] = (
                        f"To {remote_interface['device']['name']}"
                        f"{remote_interface['name']}"
                    )
                else:
                    format_params["description"] = interface_dict["description"]

                format_params["ip_address"] = IPv4Interface(interface_dict["address"])

                if interface_dict["interface"]["enabled"]:
                    format_params["enabled"] = True

                result.append(
                    TEMPLATES.get_template(
                        "config/cisco/ios/l3_interface.template"
                    ).render(
                        format_params
                    )
                )

            for interface_dict in device_interfaces_netbox_dict:
                interface_name = interface_dict["name"]
                description = interface_dict["description"]

                if "access" in description.lower():
                    # Interface description has "access" in it
                    match = L2_INTERFACE_NAME_RE.match(interface_name)
                    if match is not None:
                        format_params = match.groupdict()
                        format_params[
                            "interface_description"
                        ] = "Access port in VLAN {vlan_number}".format(
                            **format_params
                        )
                        format_params["enabled"] = interface_dict["enabled"]
                        vlans_config_list.append(
                            await create_vlan(
                                netbox_session,
                                format_params["vlan_number"],
                                manufacturer,
                            )
                        )

                        result.append(
                            TEMPLATES.get_template(
                                "config/cisco/ios/access_port.template"
                            ).render(
                                format_params
                            )
                        )

        vlans_config = "\n".join(vlans_config_list)
        result.insert(1, vlans_config)
        return "\n".join(result)


async def configure_device_from_netbox(connection_params):
    hostname = connection_params.pop("hostname")
    async with netdev.create(**connection_params) as device_conn:
        device_config = await create_device_config(hostname)
        device_config_list = device_config.split("\n")
        device_response = await device_conn.send_config_set(device_config_list)
        return device_response


def main():
    start_time = time.time()

    parsed_yaml = read_yaml()
    devices_params_gen = form_connection_params_from_yaml(parsed_yaml, site_name="sjc")

    loop = asyncio.get_event_loop()

    tasks = [
        loop.create_task(configure_device_from_netbox(device_params))
        for device_params in devices_params_gen
    ]

    loop.run_until_complete(asyncio.wait(tasks))

    # for task in tasks:
    #     print(task.result())

    print("It took {} seconds to run".format(time.time() - start_time))


if __name__ == "__main__":
    main()
