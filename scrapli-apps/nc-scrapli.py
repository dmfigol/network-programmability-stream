import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import shutil
from typing import Any, Dict, cast

from lxml import etree
from ruamel.yaml import YAML
from scrapli_netconf.driver import NetconfDriver

from constants import DEVICES, USERNAME, PASSWORD
import utils

# logging.basicConfig(level="DEBUG")

OUTPUT_DIR = Path("output/netconf/scrapli-netconf")
NUM_WORKERS = 10
SCRAPLI_TRANSPORT = "ssh2"
NC_EDIT_CONFIG_FILE = "input/nc-config.yaml"


def create_conn_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a connection dictionary for scrapli-netconf"""
    result = {
        "host": device_data["host"],
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "transport": SCRAPLI_TRANSPORT,
        "auth_strict_key": False,
        "ssh_config_file": True,
    }
    return result


def nc_get_edit_cfg(device_data: Dict[str, Any], cfg: str):
    """Retrieves config with get-config and changes it with edit-config with the
    input from YAML file using scrapli-netconf"""
    dt_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    device_name = device_data["device_name"]
    output_path = OUTPUT_DIR / f"{device_name}_{dt_str}_config.xml"
    conn_data = create_conn_data(device_data)
    with NetconfDriver(**conn_data) as nc_conn, open(output_path, "wb") as f:
        nc_conn = cast(NetconfDriver, nc_conn)
        nc_response = nc_conn.get_config(source="running")
        xml_bytes = etree.tostring(nc_response.xml_result, pretty_print=True)
        f.write(xml_bytes)

        nc_response = nc_conn.edit_config(cfg, target="running")
        if nc_response.failed:
            raise ValueError(f"{device_name}: {nc_response.result}")


def main():
    if OUTPUT_DIR.is_dir():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(NC_EDIT_CONFIG_FILE) as f:
        cfg = utils.yaml_to_xml_str(f.read(), root="config")

    futures = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        for device_data in DEVICES:
            future = pool.submit(nc_get_edit_cfg, device_data, cfg)
            futures.append(future)

    for future in futures:
        _ = future.result()


if __name__ == "__main__":
    main()
