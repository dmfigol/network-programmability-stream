from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from pathlib import Path
import shutil
from typing import Dict, Any

from netmiko import ConnectHandler

from constants import USERNAME, PASSWORD, DEVICES

NUM_WORKERS = 10

COMMANDS = [
    "show version",
    "show running-config",
    "show ip interface brief",
    "show arp",
    "show platform resources",
]
CFG = "banner motd $CONFIGURED USING NETMIKO ON {device}$\ninterface loopback 200\ndescription NETMIKO"
OUTPUT_PATH = Path("output/cli/netmiko")

PLATFORM = "cisco_ios"


def create_conn_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a connection dictionary for netmiko"""
    result = {
        "host": device_data["host"],
        "username": USERNAME,
        "password": PASSWORD,
        "device_type": PLATFORM,
        "fast_cli": True,
    }
    return result


def show_commands_and_config(device_data: Dict[str, Any]):
    """Sends show commands and a config and saves output to a file using netmiko"""
    dt_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    device_name = device_data["device_name"]
    output_file_path = OUTPUT_PATH / f"{device_name}_{dt_str}.txt"
    conn_data = create_conn_data(device_data)
    cfg = CFG.format(device=device_name).splitlines()
    with ConnectHandler(**conn_data) as conn, open(output_file_path, "w") as f:
        for command in COMMANDS:
            command_output = conn.send_command(command)
            f.write(f"===== {command} ===== \n{command_output}\n")

        f.write("\nSending configuration...\n")
        output = conn.send_config_set(cfg)
        f.write(output)


def main():
    if OUTPUT_PATH.is_dir():
        shutil.rmtree(OUTPUT_PATH)
    OUTPUT_PATH.mkdir(exist_ok=True)

    futures = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        for device_data in DEVICES:
            future = pool.submit(show_commands_and_config, device_data)
            futures.append(future)

    for future in futures:
        _ = future.result()


if __name__ == "__main__":
    main()
