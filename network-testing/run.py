from nornir import InitNornir
from nornir.plugins.tasks import networking
from nornir.plugins.functions.text import print_result
from nornir.core.filter import F
from tests import krk_vlans


def get_facts(task):
    r = task.run(task=networking.napalm_get, getters=["facts"])
    task.host["facts"] = r.result["facts"]


def get_vlans(nr):
    hosts = nr.filter(F(groups__contains="krk-l2"))
    r = hosts.run(
        task=networking.netmiko_send_command,
        command_string="show vlan",
        use_textfsm=True,
    )
    print_result(r)


def get_stp_stats(nr):
    hosts = nr.filter(F(groups__contains="krk-l2"))
    r = hosts.run(
        task=networking.netmiko_send_command,
        command_string="show spanning-tree",
        use_textfsm=True,
    )
    print_result(r)


def main() -> None:
    nr = InitNornir(config_file="config.yaml")
    krk_vlans.test(nr)
    # facts_result = nr.run(task=get_facts)
    # get_vlans(nr)
    # get_stp_stats(nr)



if __name__ == "__main__":
    main()
