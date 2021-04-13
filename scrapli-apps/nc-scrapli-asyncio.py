import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import shutil
from typing import Any, Dict, cast

import aiofiles
from lxml import etree
from ruamel.yaml import YAML
from scrapli_netconf.driver import AsyncNetconfDriver
import uvloop

from constants import DEVICES, USERNAME, PASSWORD
import utils

# logging.basicConfig(level="DEBUG")

OUTPUT_DIR = Path("output/netconf/scrapli-netconf-asyncio")
SCRAPLI_TRANSPORT = "asyncssh"
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


async def nc_get_edit_cfg(device_data: Dict[str, Any], cfg: str):
    """Retrieves config with get-config and changes it with edit-config with the
    input from YAML file using scrapli-netconf"""
    dt_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    device_name = device_data["device_name"]
    output_path = OUTPUT_DIR / f"{device_name}_{dt_str}_config.xml"
    conn_data = create_conn_data(device_data)
    async with AsyncNetconfDriver(**conn_data) as nc_conn, aiofiles.open(
        output_path, "wb"
    ) as f:
        nc_conn = cast(AsyncNetconfDriver, nc_conn)
        nc_response = await nc_conn.get_config(source="running")
        xml_bytes = etree.tostring(nc_response.xml_result, pretty_print=True)
        await f.write(xml_bytes)

        nc_response = await nc_conn.edit_config(cfg, target="running")
        if nc_response.failed:
            raise ValueError(f"{device_name}: {nc_response.result}")


async def main():
    if OUTPUT_DIR.is_dir():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(exist_ok=True)

    async with aiofiles.open(NC_EDIT_CONFIG_FILE) as f:
        cfg = utils.yaml_to_xml_str(await f.read(), root="config")

    tasks = [nc_get_edit_cfg(device_data, cfg) for device_data in DEVICES]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
