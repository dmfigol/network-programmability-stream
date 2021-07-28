from collections import defaultdict
from typing import Dict, List, Tuple

from nornir import InitNornir
from nornir.core.filter import F
from nornir import InitNornir
import pytest


@pytest.fixture(scope="session")
def nr_config_file():
    return "config.yaml"


@pytest.fixture(scope="session")
def nr(nr_config_file):
    with InitNornir(nr_config_file) as nr:
        for host in nr.inventory.hosts.values():
            host.data["test"] = defaultdict(dict)

        yield nr

        for host in nr.inventory.hosts.values():
            host.data.pop("test", None)


@pytest.helpers.register
def get_expected_data_from_tags_values(
    data: Dict[Tuple[str, ...], List[str]]
) -> Dict[str, List[str]]:
    nr_obj = InitNornir("config.yaml")
    result = {}
    for tags, expected_value in data.items():
        filtered_nr = nr_obj.filter(F(tags__all=tags))
        for host in filtered_nr.inventory.hosts.values():
            if host.name in result:
                continue
            result[host.name] = expected_value
    return result
