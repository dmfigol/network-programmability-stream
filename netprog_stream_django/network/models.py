from django.db import models


NAPALM_MAPPING = {
    'cisco_ios': 'ios',
    'cisco_iosxe': 'ios',
}

NETMIKO_MAPPING = {
    'cisco_ios': 'cisco_ios',
    'cisco_iosxe': 'cisco_ios',
}


class Device(models.Model):
    name = models.CharField(max_length=100)
    host = models.CharField(max_length=70)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(
        max_length=30, choices=(("router", "Router"), ("switch", "Switch"), ("firewall", "Firewall")), blank=True
    )
    platform = models.CharField(
        max_length=30, choices=(("cisco_ios", "Cisco IOS"), ("cisco_iosxe", "Cisco IOS XE")), blank=True
    )

    def __str__(self) -> str:
        return self.name

    @property
    def napalm_driver(self) -> str:
        return NAPALM_MAPPING[self.platform]

    @property
    def netmiko_device_type(self) -> str:
        return NETMIKO_MAPPING[self.platform]
