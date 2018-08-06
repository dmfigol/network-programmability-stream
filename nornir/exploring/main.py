from nornir.core import InitNornir
from nornir.plugins.tasks import commands, networking, text, apis
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
    # for host in inventory.hosts.values():
    #     print(host.items())
    # print(nornir_runner.inventory.hosts.items())
    nornir_runner.filter(filter_func=lambda x: x.get("site") == "sj" or x.get("country") == 'us').inventory.hosts.keys()

    servers = nornir_runner.filter(role="server")
    result = servers.run(task=commands.remote_command, command="whoami ; python -V")
    print_result(result)
    result = servers.run(task=apis.http_method, url="http://localhost:3080/v2/computes")
    print_result(result)

    # sj_edge = nornir_runner.filter(site="sj")
    # result = sj_edge.run(task=networking.napalm_get, name="Collecting facts using NAPALM", getters=["facts"])
    # print_result(result)
    #
    # result = sj_edge.run(task=basic_configuration, name="Compiling and applying configuration")
    # print_result(result)

    sj_br1 = nornir_runner.filter(name="sj-br1")
    result = sj_br1.run(task=networking.netmiko_file_transfer,
                        name="send file using Netmiko",
                        source_file="config-ansible.yaml",
                        dest_file="config-ansible.yaml")

    print_result(result)


if __name__ == '__main__':
    main()
