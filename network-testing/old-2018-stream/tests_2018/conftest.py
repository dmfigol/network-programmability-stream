import pytest

from nornir import InitNornir


@pytest.fixture(scope="session", autouse=True)
def nr():
    return InitNornir(config_file="config.yaml")
