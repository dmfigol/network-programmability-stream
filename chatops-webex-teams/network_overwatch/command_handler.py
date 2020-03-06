from typing import Dict, Any, Callable, Awaitable

from network_overwatch.webex_teams import WebexTeams
from network_overwatch.restconf import RESTCONF


async def vrf_handler(
    command_args: str, message_data: Dict[str, Any], webex_teams: WebexTeams
) -> None:
    device_name = command_args.strip().upper()
    restconf = RESTCONF(device_name=device_name)
    vrfs = await restconf.get_vrf_list()
    vrfs_md = "  \n".join([f"* **{vrf}**" for vrf in vrfs])
    md = f"**{device_name}** has VRFs:\n {vrfs_md}\n\n"
    message_data = {"markdown": md, "roomId": message_data["roomId"]}
    await webex_teams.messages.create(message_data)


DISPATCH: Dict[str, Callable[[str, Dict[str, Any], WebexTeams], Awaitable[None]]] = {
    "vrf": vrf_handler,
}


def dispatch_command(command):
    return DISPATCH[command]
