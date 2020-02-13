import os

import requests

from helper import read_yaml, form_device_params_from_yaml

NETBOX_API_ROOT = "http://netbox:32772/api"
NETBOX_DEVICES_ENDPOINT = "/dcim/devices/"
NETBOX_SITES_ENDPOINT = "/dcim/sites/"

SITES = [{"name": "Krakow", "slug": "krk"}, {"name": "Reykjavík", "slug": "rkvk"}]


class NetboxAPITokenNotFound(Exception):
    pass


def form_headers():
    api_token = os.environ.get("NETBOX_API_TOKEN")
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


def add_site(name, slug):
    headers = form_headers()

    data = {"name": name, "slug": slug}

    r = requests.post(
        NETBOX_API_ROOT + NETBOX_SITES_ENDPOINT, headers=headers, json=data
    )

    if r.status_code == 201:
        print(f"Site {name} was created successfully")
    else:
        r.raise_for_status()


def add_sites():
    """Add sites from SITES dictionary"""
    for site in SITES:
        add_site(**site)
    print("All sites have been added")


def add_device(name, device_type_id, site_id, device_role_id):
    headers = form_headers()

    data = {
        "name": name,
        "display_name": name,
        "device_type": device_type_id,  # 2,
        "site": site_id,  # 1,
        "status": 1,
    }
    if device_role_id is not None:
        data["device_role"] = device_role_id

    r = requests.post(
        NETBOX_API_ROOT + NETBOX_DEVICES_ENDPOINT, headers=headers, json=data
    )

    if r.status_code == 201:
        print(f"Device {name} was added successfully")
    else:
        r.raise_for_status()


def add_devices():
    parsed_yaml = read_yaml()
    devices_params_gen = form_device_params_from_yaml(parsed_yaml)
    for device_params in devices_params_gen:
        add_device(**device_params)
    print("All devices have been imported")


def main():
    # headers = form_headers()
    # add_sites()
    add_devices()


if __name__ == "__main__":
    main()
