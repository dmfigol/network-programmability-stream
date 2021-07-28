from typing import TYPE_CHECKING, Dict, Any, cast, Iterable

import pytest
from nornir.core.filter import F
from nornir_scrapli.tasks import send_command

if TYPE_CHECKING:
    from scrapli.response import Response as ScrapliResponse


UNSET = object()


def collect_sw_version(task, keyword: str):
    task.host.data["test"][keyword]["actual"] = UNSET
    result = task.run(send_command, command="show version")
    scrapli_response: ScrapliResponse = result.scrapli_response
    data = cast(Dict[str, Any], scrapli_response.genie_parse_output())
    actual_sw_version = data["version"]["version"]
    task.host.data["test"][keyword]["actual"] = actual_sw_version


EXPECTED_SW_VERSION = {
    "R1": "17.3.2",
    "R2": "17.3.2",
    "R3": "17.3.2",
    "R4": "17.3.3",
    "R5": "17.3.2",
    "R6": "17.3.2",
    "R7": "17.3.2",
    "R8": "17.3.2",
    "R9": "17.3.2",
    "R10": "17.3.3",
}


class TestParsedShowVersion:
    keyword = "version"
    msg = "Host {device_name!r} has SW version {actual!r}, expected: {expected!r}"

    @pytest.fixture(autouse=True)
    def collect(self, nr):
        nr.run(task=collect_sw_version, keyword=self.keyword)

    @pytest.mark.parametrize(
        "device_name,expected",
        EXPECTED_SW_VERSION.items(),
        ids=EXPECTED_SW_VERSION.keys(),
    )
    def test_sw_version(self, nr, device_name: str, expected: str):
        host = nr.inventory.hosts[device_name]
        actual = host.data["test"][self.keyword]["actual"]
        assert expected == actual, self.msg.format(**locals())
