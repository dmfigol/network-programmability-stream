from typing import (
    Sequence,
    TYPE_CHECKING,
    cast,
    Dict,
    Any,
    List,
    Sequence,
    Tuple,
    Iterable,
)

import pytest
from nornir.core.filter import F
from nornir_scrapli.tasks import send_command

if TYPE_CHECKING:
    from scrapli.response import Response as ScrapliResponse


EXPECTED_VRFS = {
    ("csr1000v", "edge"): {"Mgmt-vrf", "Edge"},
    ("csr1000v",): {"Mgmt-vrf"},
}


EXPECTED_DATA = pytest.helpers.get_expected_data_from_tags_values(EXPECTED_VRFS)

UNSET = object()


def collect_vrfs(task, keyword: str):
    task.host.data["test"][keyword]["actual"] = UNSET

    result = task.run(send_command, command="show vrf")
    scrapli_response: ScrapliResponse = result.scrapli_response
    data = cast(Dict[str, Any], scrapli_response.genie_parse_output())
    actual_vrfs = set(data["vrf"].keys())
    task.host.data["test"][keyword]["actual"] = actual_vrfs


class TestParsedShowVrf:
    keyword = "vrfs"
    msg = "Host {device_name!r} has vrfs {actual!r}, expected: {expected!r}"

    @pytest.fixture(autouse=True)
    def collect(self, nr):
        nr.run(task=collect_vrfs, keyword=self.keyword)

    @pytest.mark.parametrize(
        "device_name,expected", EXPECTED_DATA.items(), ids=EXPECTED_DATA.keys()
    )
    def test_vrfs(self, nr, device_name: str, expected: List[str]):
        host = nr.inventory.hosts[device_name]
        actual = host.data["test"][self.keyword]["actual"]
        assert expected == actual, self.msg.format(**locals())
