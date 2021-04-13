from scrapli import AsyncScrapli
import re
from typing import cast, TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from scrapli.driver import AsyncNetworkDriver

DEVICE = {
    "host": "192.168.152.101",
    "auth_username": "cisco",
    "auth_password": "cisco",
    "auth_strict_key": False,
    "platform": "cisco_iosxe",
    "transport": "asyncssh",
}


async def get_serial_num():
    async with AsyncScrapli(**DEVICE) as device_conn:
        device_conn = cast("AsyncNetworkDriver", device_conn)
        response = await device_conn.send_command("show license udi")
        if re_match := re.search(r"SN:(?P<serial_num>\w+)", response.result):
            return re_match.group("serial_num")
        raise ValueError("Serial number not found")


@pytest.mark.asyncio
@pytest.mark.scrapli_replay
async def test_get_serial_num():
    sn = await get_serial_num()
    print(sn)
    assert len(sn) == 11
