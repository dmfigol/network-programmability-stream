import re

from scrapli import Scrapli
from scrapli_cfg import ScrapliCfg
from scrapli.logging import enable_basic_logging

# enable_basic_logging(file=True, level="DEBUG")
device = {
    "host": "192.168.152.101",
    "auth_username": "cisco",
    "auth_password": "cisco",
    "auth_strict_key": False,
    "platform": "cisco_iosxe",
    "transport": "ssh2",
}
CFG_FILE = "input/R1.txt"

# use https://regex101.com/ with running config example to verify your regexp
BGP_PATTERN = re.compile(r"^router bgp \d+$(?:\n^\s+.*$)*\n!\n", flags=re.I | re.M)


def main():
    """This example covers a more complex case of replacing config where some
    part of running config should be left untouched, e.g. bgp config, which is marked
    {{ bgp }} in the config file and needs to be also marked with correct regexp.
    Check easier examples in scrapli-cfg docs for full config replacement"""
    with open(CFG_FILE, "r") as f:
        cfg = f.read()
        # cfg = "banner motd ^Configured by scrapli-cfg5^"

    with Scrapli(**device) as conn:
        cfg_conn = ScrapliCfg(conn=conn)  # type: ignore
        cfg_conn.open()
        # do regexp on running-config, extract it
        # put into desired config string instead of {{ bgp }}
        rendered_config = cfg_conn.render_substituted_config(
            config_template=cfg, substitutes=[("bgp", BGP_PATTERN)]
        )
        cfg_conn.load_config(config=rendered_config, replace=True)
        diff = cfg_conn.diff_config()
        print(diff.side_by_side_diff)
        print(diff.unified_diff)
        cfg_response = cfg_conn.commit_config()
        cfg_response.raise_for_status()


if __name__ == "__main__":
    main()
