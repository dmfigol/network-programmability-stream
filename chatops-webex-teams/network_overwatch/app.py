import logging
import os

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from network_overwatch.constants import WEBEX_WEBHOOK_ENDPOINT
from network_overwatch.webex_teams import WebexTeams
from network_overwatch.webhook_manager import (
    get_bot_id,
    create_or_update_webhook,
    handle_event,
)


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


async def homepage(request) -> Response:
    return PlainTextResponse("Homepage")


async def about(request) -> Response:
    return PlainTextResponse("About")


async def webex_webhooks(request) -> Response:
    data = await request.json()
    await handle_event(
        event=data,
        webex_teams=request.app.state.webex_teams,
        bot_id=request.app.state.bot_id,
    )
    return Response(status_code=204)


async def on_startup() -> None:
    webex_teams = WebexTeams(os.environ["OVERWATCH_WEBEX_BOT_TOKEN"])
    app.state.webex_teams = webex_teams
    app.state.bot_id = await get_bot_id(webex_teams)
    app.state.webhook_id = await create_or_update_webhook(webex_teams)


routes = [
    Route("/", endpoint=homepage),
    Route("/about", endpoint=about),
    Route(WEBEX_WEBHOOK_ENDPOINT, endpoint=webex_webhooks, methods=["POST"]),
]

app = Starlette(routes=routes, on_startup=[on_startup],)
