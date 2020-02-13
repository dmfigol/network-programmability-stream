from nornir.core import InitNornir
from nornir.plugins.tasks import commands, networking, text
from nornir.plugins.functions.text import print_result


def basic_configuration(task):
    # Transform inventory data to configuration via a template file
    result = task.run(
        task=text.template_file,
        name="Interface Configuration",
        template="interfaces.j2",
        path="templates"
    )

    # Save the compiled configuration into a host variable
    task.host["config"] = result.result

    # Deploy that configuration to the device using NAPALM
    # task.run(
    #     task=networking.napalm_configure,
    #     name="Loading Configuration on the device",
    #     replace=False,
    #     configuration=task.host["config"],
    # )
    # Deploy that configuration to the device using Netmiko
    task.run(
        task=networking.netmiko_send_config,
        name="Loading Configuration on the device [Netmiko]",
        config_commands=task.host["config"].splitlines(),
    )


def main():
    nornir_runner = InitNornir(config_file="config-ansible.yaml")

    inventory = nornir_runner.inventory
    for host in inventory.hosts.values():
        print(host.items())
    # print(nornir_runner.inventory.hosts.items())



if __name__ == '__main__':
    main()
