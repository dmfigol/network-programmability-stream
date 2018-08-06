#!/usr/bin/env python3
import ncs
from ncs.maagic import Root
from typing import Iterator, Tuple


NSO_USERNAME = 'admin'
NSO_CONTEXT = 'python'
# NSO_GROUPS = ['ncsadmin']


def get_device_name(nso: Root) -> Iterator[Tuple[str, str]]:
    for device in nso.devices.device:
        # print device.config.ios__cached_show.version.model
        breakpoint()
        yield (device.name, device.ios__cached_show.version.model)


def main() -> None:
    with ncs.maapi.single_read_trans(NSO_USERNAME, NSO_CONTEXT) as transaction:
        nso = ncs.maagic.get_root(transaction)
        devices = nso.devices.device
        # print(devices["isp1-pe1"].config.ios__ntp.server.peer_list)
        # breakpoint()
        for device in devices:
            device.config.ios__ntp.server.peer_list.append({"name": "1.2.3.4"})
            # device.config.ios__ntp.server.ip = "1.2.3.4"
            # print(device.name)
            # print(device.config.ios__ntp)
            # print(device.config.ios__cached_show.version)
        transaction.apply()


if __name__ == '__main__':
    main()
