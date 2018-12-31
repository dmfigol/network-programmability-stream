import argparse
import logging
from typing import Tuple, Dict

from nornir.core import InitNornir

import setup  # noqa
from deployment import Deployment
from utils import update_description, update_host_vars

logger = logging.getLogger('lab_system.main')


def convert_topology_arg(topology: str) -> Tuple[str, Dict[str, int]]:
    topology, quantity = topology.split(':')
    return topology, {'quantity': int(quantity)}


def parse_arguments() -> argparse.Namespace:
    """Parses arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--topologies",
        nargs='+',
        help=(
            "Specify topology name and quantity separated by :, "
            "for example --topology advanced:2 simple:2"
        ),
        type=convert_topology_arg,
        dest="topologies"
    )
    parser.add_argument(
        "-p", "--pod", type=str, default="all", help="Specify pod number, default: all"
    )
    args = parser.parse_args()
    args.topologies = dict(args.topologies)
    return args


def main() -> None:
    args = parse_arguments()
    nr = InitNornir("config.yaml")
    update_host_vars(nr.inventory)
    update_description(nr.inventory)
    deployment = Deployment(args.topologies, nr.inventory)
    import ipdb;
    ipdb.set_trace()


if __name__ == "__main__":
    main()
