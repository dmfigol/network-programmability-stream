from typing import Any

from celery import shared_task
from netmiko import ConnectHandler

from network.models import Device

@shared_task
def switch_interface(device_id: str, interface_name: str, enable_interface: str) -> Any:
    device = Device.objects.get(pk=device_id)
    config_commands = [f'interface {interface_name}']
    result = {"interface_name": interface_name}
    if enable_interface == 'False':
        config_commands.append(' shutdown')
        result["up"] = False
    else:
        config_commands.append(' no shutdown')
        result["up"] = True
    conn_params = {
        'ip': device.host,
        'username': device.username,
        'password': device.password,
        'device_type': device.netmiko_device_type,
    }
    with ConnectHandler(**conn_params) as device_conn:
        device_conn.send_config_set(config_commands)
    return result
