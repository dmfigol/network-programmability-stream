import asyncio
import logging
import re
from typing import List, Dict, Any, TYPE_CHECKING

import httpx

from network_overwatch.constants import WEBEX_WEBHOOK_ENDPOINT, NGROK_TUNNEL
from network_overwatch.command_handler import dispatch_command

if TYPE_CHECKING:
    from network_overwatch.webex_teams import WebexTeams

WEBHOOK = {
    "name": "New messages",
    "targetUrl": "",
    "resource": "messages",
    "event": "created",
}

NGROK_API_ROOT = "http://localhost:4040/api"


logger = logging.getLogger(__name__)

MENTION_REGEXP = re.compile(r"@?[\w\-]+\s*")
COMMAND_REGEXP = re.compile(r"^(?P<command>[\w\-]+)\s*")


async def get_bot_id(webex_teams: "WebexTeams") -> str:
    bot_data = await webex_teams.people.me()
    bot_id = bot_data["id"]
    return bot_id


async def create_or_update_webhook(webex_teams: "WebexTeams") -> str:
    fetch_tunnel_data_task = asyncio.create_task(fetch_ngrok_tunnels_data())
    fetch_webhooks_list_task = asyncio.create_task(webex_teams.webhooks.list())
    await asyncio.gather(fetch_tunnel_data_task, fetch_webhooks_list_task)

    target_webhook_url = build_webex_webhook_url(fetch_tunnel_data_task.result())
    # found_correct_webhook = False
    for webhook_data in fetch_webhooks_list_task.result():
        if (
            webhook_data["resource"] == "messages"
            and webhook_data["event"] == "created"
        ):
            webhook_id = webhook_data["id"]
            if webhook_data["targetUrl"] != target_webhook_url:
                logger.info(
                    "Found a webhook for new messages but "
                    "with different URL, updating"
                )
                data = {
                    "id": webhook_data["id"],
                    "name": WEBHOOK["name"],
                    "targetUrl": target_webhook_url,
                }
                await webex_teams.webhooks.update(data)
            else:
                status = webhook_data["status"]
                logger.info(
                    "Required webhook is already registered, " "status: %r", status,
                )
            return webhook_id

    # if not found_correct_webhook:
    return await create_webhook(url=target_webhook_url, webex_teams=webex_teams)


async def create_webhook(url: str, webex_teams: "WebexTeams") -> str:
    webhook = WEBHOOK.copy()
    webhook["targetUrl"] = url
    created_webhook = await webex_teams.webhooks.create(data=webhook)
    created_webhook_id = created_webhook["id"]
    logger.info("Created webhook %r", created_webhook_id)
    return created_webhook_id


async def fetch_ngrok_tunnels_data() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient() as http_client:
        url = NGROK_API_ROOT + "/tunnels"
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
        result = data.get("tunnels", [])  # type: ignore
        return result


def build_webex_webhook_url(tunnels_data: List[Dict[str, Any]]):
    for tunnel in tunnels_data:
        if tunnel["config"]["addr"] == NGROK_TUNNEL and "https" in tunnel["public_url"]:
            result = tunnel["public_url"] + WEBEX_WEBHOOK_ENDPOINT
            return result
    raise ValueError(f"No ngrok tunnel for {NGROK_TUNNEL}")


async def handle_event(event, webex_teams: "WebexTeams", bot_id: str) -> None:
    resource = event["resource"]
    event_type = event["event"]
    actor_id = event["actorId"]
    if actor_id == bot_id:
        return
    if resource == "messages" and event_type == "created":
        message = await webex_teams.messages.get(id=event["data"]["id"])
        return await handle_new_message(message=message, webex_teams=webex_teams)
    else:
        raise ValueError(f"Unknown event {resource} | {event_type}")


async def handle_new_message(message: Dict[str, Any], webex_teams: "WebexTeams"):
    command_line = message["text"].strip()
    room_type = message["roomType"]
    if room_type == "group":
        command_line = MENTION_REGEXP.sub("", command_line, count=1).strip()
    command_match = COMMAND_REGEXP.match(command_line)
    if not command_match:
        raise ValueError(f"Can't parse the line: {command_line}")
    command = command_match.group("command")
    command_args = COMMAND_REGEXP.sub("", command_line)
    command_fn = dispatch_command(command)
    await command_fn(
        command_args=command_args.strip(),
        message_data=message,
        webex_teams=webex_teams,
    )
