from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
from pathlib import Path
import shutil
from typing import Any, Dict

from lxml import etree
from ncclient import manager

from constants import DEVICES, USERNAME, PASSWORD
import utils

# logging.basicConfig(level="DEBUG", filename="nc.log")

OUTPUT_DIR = Path("output/netconf/ncclient")
NUM_WORKERS = 10
NC_EDIT_CONFIG_FILE = "input/nc-config.yaml"


def create_conn_data(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a connection dictionary for ncclient"""
    result = {
        "host": device_data["host"],
        "username": USERNAME,
        "password": PASSWORD,
        "hostkey_verify": False,
    }
    return result


def nc_get_edit_cfg(device_data: Dict[str, Any], cfg: str) -> None:
    """Retrieves config with get-config and changes it with edit-config with the
    input from YAML file using ncclient"""
    dt_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    device_name = device_data["device_name"]
    output_path = OUTPUT_DIR / f"{device_name}_{dt_str}_config.xml"

    nc_conn_data = create_conn_data(device_data)
    with manager.connect(**nc_conn_data) as nc_conn, open(output_path, "wb") as f:
        nc_response = nc_conn.get_config(source="running")
        xml_bytes = etree.tostring(nc_response.data_ele, pretty_print=True)
        f.write(xml_bytes)

        nc_response = nc_conn.edit_config(config=cfg, target="running")
        if not nc_response.ok:
            raise ValueError(f"{device_name}: {nc_response.xml}")


def main():
    if OUTPUT_DIR.is_dir():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(NC_EDIT_CONFIG_FILE) as f:
        default_ns = "urn:ietf:params:xml:ns:netconf:base:1.0"
        root_element = etree.Element("config", nsmap={None: default_ns})  # type: ignore
        cfg = utils.yaml_to_xml_str(f.read(), root=root_element)

    futures = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        for device_data in DEVICES:
            future = pool.submit(nc_get_edit_cfg, device_data, cfg)
            futures.append(future)

    for future in futures:
        _ = future.result()


if __name__ == "__main__":
    main()
