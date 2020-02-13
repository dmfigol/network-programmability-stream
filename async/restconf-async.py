import asyncio
from datetime import datetime
from typing import List, Dict, Any

import aiohttp
import colorama
from bs4 import BeautifulSoup

HOSTS = [
    "198.18.1.101",
    "198.18.1.102",
    "198.18.1.103",
    "198.18.1.104",
    "198.18.1.105",
    "198.18.1.106",
    "198.18.1.107",
    "198.18.1.108",
    "198.18.1.109",
    "198.18.1.110",
]

OTHER_PARAMS = {
    "username": "cisco",
    "password": "cisco",
}

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}


async def get_hostname(host: str) -> str:
    username = OTHER_PARAMS["username"]
    password = OTHER_PARAMS["password"]
    async with aiohttp.ClientSession() as session:
        url = f"https://{host}/restconf/data/native/hostname"
        async with session.get(url, auth=aiohttp.BasicAuth(username, password), headers=HEADERS, verify_ssl=False) as response:
            response.raise_for_status()
            json = await response.json()
            return json["Cisco-IOS-XE-native:hostname"]


def process_interfaces_json(data: Dict[str, any]) -> List[Dict[str, Any]]:
    result = []
    for interface_type, interface_info in data["Cisco-IOS-XE-native:interface"].items():
        for interface in interface_info:
            interface_num = interface["name"]
            interface_name = f"{interface_type}{interface_num}"
            ip_address = interface.get("ip", {}).get("address", {}).get("primary", {}).get("address")
            int_dict = {
                "name": interface_name,
                "ip_address": ip_address
            }
            result.append(int_dict)
    return result


async def get_interfaces(host: str) -> List[Dict[str, Any]]:
    username = OTHER_PARAMS["username"]
    password = OTHER_PARAMS["password"]
    async with aiohttp.ClientSession() as session:
        url = f"https://{host}/restconf/data/native/interface"
        async with session.get(url, auth=aiohttp.BasicAuth(username, password), headers=HEADERS, verify_ssl=False) as response:
            response.raise_for_status()
            data = await response.json()
            return process_interfaces_json(data)


def main() -> None:
    colorama.init()
    start_time = datetime.now()
    loop = asyncio.get_event_loop()

    hostname_tasks = [
        loop.create_task(get_hostname(host))
        for host in HOSTS
    ]

    interface_tasks = [
        loop.create_task(get_interfaces(host))
        for host in HOSTS
    ]

    loop.run_until_complete(asyncio.gather(*hostname_tasks, *interface_tasks))

    for host, hostname_task, interface_task in zip(HOSTS, hostname_tasks, interface_tasks):
        hostname = hostname_task.result()
        interfaces = interface_task.result()
        print(f"Device {host}")
        print(f"Hostname: {hostname}")
        print(f"Has interfaces:")
        for interface in interfaces:
            print(f"  Interface {interface['name']} has ip address: {interface['ip_address']}")
        print(f"=" * 80)
        # print(f"Device {host} has hostname: {hostname}")

    exec_time = (datetime.now() - start_time).total_seconds()
    print(colorama.Fore.GREEN + f"Summary: it took {exec_time:,.2f} seconds to run")


if __name__ == '__main__':
    main()
