from httpx.client import AsyncClient

from network_overwatch import constants

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}
RESTCONF_BASE_URL = "https://{host}"


class RESTCONF:
    def __init__(self, device_name: str) -> None:
        device_host = constants.DEVICES[device_name.upper()]
        base_url = RESTCONF_BASE_URL.format(host=device_host)
        self.http_client = AsyncClient(
            headers=HEADERS,
            auth=(constants.DEVICE_USERNAME, constants.DEVICE_PASSWORD),
            base_url=base_url,
            verify=False,
        )

    async def get_vrf_list(self):
        response = await self.http_client.get("/restconf/data/native/vrf")
        response.raise_for_status()
        vrfs = []
        for vrf_data in response.json()["Cisco-IOS-XE-native:vrf"]["definition"]:
            vrf_name = vrf_data["name"]
            vrfs.append(vrf_name)
        return vrfs
