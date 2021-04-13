from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from typing import Dict, Any, cast
from pathlib import Path
import shutil

from scrapli import Scrapli
from scrapli.driver import NetworkDriver

from constants import USERNAME, PASSWORD, DEVICES

# logging.basicConfig(level="INFO")

NUM_WORKERS = 10
COMMANDS = [
    "show version",
    "show running-config",
    "show ip interface brief",
    "show arp",
    "show platform resources",
]
CFG = "banner motd $CONFIGURED USING SCRAPLI ON {device}$\ninterface loopback 100\ndescription SCRAPLI"
SCRAPLI_TRANSPORT = "ssh2"
PLATFORM = "cisco_iosxe"
OUTPUT_PATH = Path("output/cli/scrapli")


def create_conn_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a connection dictionary for scrapli"""
    result = {
        "host": device_data["host"],
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "transport": SCRAPLI_TRANSPORT,
        "platform": PLATFORM,
        "auth_strict_key": False,
        "ssh_config_file": True,
    }
    return result


def show_commands_and_config(device_data: Dict[str, Any]):
    """Sends show commands and a config and saves output to a file using scrapli"""
    dt_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    device_name = device_data["device_name"]
    output_path = OUTPUT_PATH / f"{device_name}_{dt_str}.txt"
    cfg = CFG.format(device=device_name).splitlines()
    conn_data = create_conn_data(device_data)
    with Scrapli(**conn_data) as conn, open(output_path, "w") as f:
        # conn = IOSXEDriver(**CONN_DATA)
        # conn.open()
        conn = cast(NetworkDriver, conn)
        sh_commands_responses = conn.send_commands(COMMANDS, strip_prompt=False)
        for response in sh_commands_responses:
            f.write(f"===== {response.channel_input} ===== \n{response.result}\n")
        # print([response.failed for response in sh_commands_responses])
        f.write("\nSending configuration...\n")
        cfg_responses = conn.send_configs(cfg, strip_prompt=False)
        for response in cfg_responses:
            f.write(f"{response.channel_input}\n{response.result} ")
        # print([response.failed for response in responses])


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
