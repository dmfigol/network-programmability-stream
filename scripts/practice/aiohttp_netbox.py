import asyncio
import async_timeout
import time
from pprint import pprint

import aiohttp
import decouple


NETBOX_API_ROOT = 'http://netbox:32768/api'
NETBOX_DEVICES_ENDPOINT = '/dcim/devices/'
NETBOX_INTERFACES_ENDPOINT = '/dcim/interfaces/'
NETBOX_SITES_ENDPOINT = '/dcim/sites/'
NETBOX_IP_ADDRESSES_ENDPOINT = '/ipam/ip-addresses/'
NETBOX_VLANS_ENDPOINT = '/ipam/vlans/'


def form_headers():
    api_token = decouple.config('NETBOX_API_TOKEN')

    headers = {
        'Authorization': 'Token {}'.format(api_token),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    return headers


async def fetch_json(url, params=None):
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(10):
            async with session.get(url, headers=form_headers(), params=params) as response:
                return await response.json()


async def get_everything_from_netbox():
    query_params = {
        'device': 'SJ-R1',
    }

    ip_address_netbox_dict_coroutine = await fetch_json(NETBOX_API_ROOT + NETBOX_IP_ADDRESSES_ENDPOINT,
                                                        params=query_params)
    ip_address_netbox_dict = ip_address_netbox_dict_coroutine['results']

    pprint(ip_address_netbox_dict)

    device_interfaces_netbox_dict_coroutine = await fetch_json(NETBOX_API_ROOT + NETBOX_INTERFACES_ENDPOINT,
                                                               params=query_params)
    device_interfaces_netbox_dict = device_interfaces_netbox_dict_coroutine['results']

    pprint(device_interfaces_netbox_dict)


def main():
    start_time = time.time()

    urls = [NETBOX_API_ROOT + NETBOX_DEVICES_ENDPOINT, NETBOX_API_ROOT + NETBOX_IP_ADDRESSES_ENDPOINT]

    loop = asyncio.get_event_loop()

    # tasks = [
    #     loop.create_task(get_information_from_netbox(url))
    #     for url in urls
    # ]

    tasks = [loop.create_task(get_everything_from_netbox())]

    loop.run_until_complete(asyncio.wait(tasks))

    # for task in tasks:
    #     print(task.result())

    print('It took {} seconds to run'.format(time.time() - start_time))


if __name__ == '__main__':
    main()
