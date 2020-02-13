from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail
from pprint import pprint


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        # create a dictionary to store new variables per device
        devices = {"devices": {}}

        # (lab_hostname, pod_number) -> device hostname in ansible inventory
        # (edge-1, 1000) -> 9348-1

        hostname_and_pod_num_to_device = {}

        for device, device_dict in task_vars["devices"].items():
            pod_number = device_dict["pod_number"]
            lab_hostname = device_dict["lab_hostname"]
            hostname_and_pod_num_to_device[(lab_hostname, pod_number)] = device

        # (R1, Ethernet1/1) -> ('matrix-1', 1)
        device_port_to_matrix_port = {}

        for matrix_switch in task_vars["groups"]["matrix-switches"]:
            matrix_switch_vars = task_vars["hostvars"][matrix_switch]
            for port_number, interface in enumerate(matrix_switch_vars["interfaces"]):
                if interface.get("mode") == "dot1q-tunnel":
                    if "connected_device" not in interface:
                        raise AnsibleActionFail(
                            (
                                "Interface {interface_name} on the switch {switch_name} is "
                                "dot1q-tunnel but does not have connected_device variable"
                            ).format(
                                interface_name=interface["name"],
                                switch_name=matrix_switch,
                            )
                        )

                    connected_device = interface["connected_device"]["name"]
                    connected_device_port = interface["connected_device"]["port"]
                    # print(connected_device_port, connected_device_name)
                    device_port_to_matrix_port[
                        (connected_device, connected_device_port)
                    ] = (
                        matrix_switch_vars["inventory_hostname"], port_number
                    )

        current_dot1q_tunnel_vlan = task_vars["dot1q_tunnel_vlan_start"]

        for pod in task_vars["pods"]:
            pod_number = pod["pod_number"]
            lab_template = pod["lab_template"]
            for connection in task_vars["topologies"][lab_template]["connections"]:
                for connection_end in connection:
                    lab_hostname = connection_end["lab_hostname"]
                    port = connection_end["port"]
                    device = hostname_and_pod_num_to_device[(lab_hostname, pod_number)]
                    pod_device_vars = task_vars["hostvars"][device]
                    if (
                        pod_device_vars.get("lab_hostname", lab_hostname)
                        != lab_hostname
                        and pod_device_vars.get("pod_number", pod_number) != pod_number
                    ):
                        raise AnsibleActionFail(
                            (
                                'Trying to assign lab hostname "{target_lab_hostname}" '
                                'and pod number "{target_pod_number}", '
                                "but this device already has"
                                'lab hostname "{current_lab_hostname}"'
                                'and pod number "{current_pod_number" assigned'.format(
                                    target_lab_hostname=lab_hostname,
                                    target_pod_number=pod_number,
                                    current_lab_hostname=pod_device_vars[
                                        "lab_hostname"
                                    ],
                                    current_pod_number=pod_device_vars["pod_number"],
                                )
                            )
                        )

                    else:
                        pod_device_vars["lab_hostname"] = lab_hostname
                        pod_device_vars["pod_number"] = pod_number
                        pod_device_vars["lab_template"] = lab_template
                        pod_device_vars["updated_vars"] = [
                            "lab_hostname", "pod_number", "lab_template"
                        ]

                    (
                        matrix_switch_name, matrix_switch_port_number
                    ) = device_port_to_matrix_port[
                        (device, port)
                    ]

                    matrix_switch_vars = task_vars["hostvars"][matrix_switch_name]
                    interface = matrix_switch_vars["interfaces"][
                        matrix_switch_port_number
                    ]
                    if "access_vlan" in interface:
                        raise AnsibleActionFail(
                            (
                                "{matrix_switch_name} already has vlan "
                                "assigned to the interface {interface_name}"
                            ).format(
                                matrix_switch_name=matrix_switch_name,
                                interface_name=interface["name"],
                            )
                        )

                    elif interface.get("mode") != "dot1q-tunnel":
                        raise AnsibleActionFail(
                            (
                                "{matrix_switch_name} interface {interface_name} "
                                'has mode {interface_mode} instead of "dot1q-tunnel"'
                            ).format(
                                matrix_switch_name=matrix_switch_name,
                                interface_name=interface["name"],
                                interface_mode=interface["mode"],
                            )
                        )

                    else:
                        interface["access_vlan"] = current_dot1q_tunnel_vlan
                        interface["state"] = "present"
                        interface["dynamic"] = True
                        interface["description"] = (
                            "connected to {port} {device} "
                            "| lab hostname: {lab_hostname} "
                            "| pod: {pod_number}".format(
                                port=port,
                                device=device,
                                lab_hostname=lab_hostname,
                                pod_number=pod_number,
                            )
                        )
                        matrix_switch_vars["updated_vars"] = ["interfaces"]

                current_dot1q_tunnel_vlan += 1

            # for the next pod start with the vlan divisible by 10
            remainder = current_dot1q_tunnel_vlan % 10
            if remainder:
                current_dot1q_tunnel_vlan += 10 - remainder

        for matrix_switch in task_vars["groups"]["matrix-switches"]:
            matrix_switch_vars = task_vars["hostvars"][matrix_switch]
            for interface in matrix_switch_vars["interfaces"]:
                if (
                    interface.get("access_vlan") is None
                    and interface.get("mode") == "dot1q-tunnel"
                ):
                    interface["state"] = "absent"
            devices["devices"][matrix_switch] = matrix_switch_vars

        for pod_device in task_vars["groups"]["pod-gear"]:
            pod_device_vars = task_vars["hostvars"][pod_device]
            devices["devices"][pod_device] = pod_device_vars

        result["ansible_facts"] = devices

        return result
