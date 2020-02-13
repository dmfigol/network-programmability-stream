import asyncio
from datetime import datetime
from typing import List, Dict, Any, Iterable, Tuple

import netdev
import colorama

HOSTS = {
    "R1": "198.18.1.101",
    "R2": "198.18.1.102",
    "R3": "198.18.1.103",
    "R4": "198.18.1.104",
    "R5": "198.18.1.105",
    "R6": "198.18.1.106",
    "R7": "198.18.1.107",
    "R8": "198.18.1.108",
    "R9": "198.18.1.109",
    "R10": "198.18.1.110",
}

OTHER_PARAMS = {
    "username": "cisco",
    "password": "cisco",
    "device_type": "cisco_ios",
}


COMMANDS = [
    "show version",
    "show ip int brief",
    "show plat soft status control-processor br"
]


async def get_outputs(host_info: Tuple[str, str], commands: Iterable[str]) -> Iterable[str]:
    hostname, host = host_info
    device_params = {
        "host": host
    }
    device_params.update(OTHER_PARAMS)

    async with netdev.create(**device_params) as device_conn:
        outputs = [await device_conn.send_command(command) for command in commands]
        return outputs


def main() -> None:
    colorama.init()
    start_time = datetime.now()
    loop = asyncio.get_event_loop()

    tasks = [
        loop.create_task(get_outputs(host_info, COMMANDS))
        for host_info in HOSTS.items()
    ]

    loop.run_until_complete(asyncio.wait(tasks))

    for hostname, task in zip(HOSTS, tasks):
        outputs = task.result()
        print(f"Device {hostname}")
        for command, output in zip(COMMANDS, outputs):
            print(f"===== Output from command {command} =====")
            print(f"{output}\n")
        print(f"=" * 80)

    exec_time = (datetime.now() - start_time).total_seconds()
    print(colorama.Fore.GREEN + f"Summary: it took {exec_time:,.2f} seconds to run")


if __name__ == '__main__':
    main()
