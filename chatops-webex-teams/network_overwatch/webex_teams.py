from httpx.client import AsyncClient

from typing import Any, List, Dict, Union, Optional


class WebexTeams:
    BASE_URL = "https://api.ciscospark.com/v1"

    def __init__(self, token: str) -> None:
        # self.token = token
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        self.http_client = AsyncClient(headers=headers)
        self.webhooks = WebhooksCRUD(self)
        self.messages = MessagesCRUD(self)
        self.people = PeopleCRUD(self)

    async def _request(
        self, method: str, endpoint: str, params=None, data=None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        url = self.BASE_URL + endpoint
        response = await self.http_client.request(method, url, params=params, json=data)
        response.raise_for_status()
        if response.content:
            return response.json()
        else:
            return None

    async def _get(self, url, params=None) -> Any:
        return await self._request("GET", url, params=params)

    async def _post(self, url, params=None, data=None) -> Any:
        return await self._request("POST", url, params=params, data=data)

    async def _put(self, url, params=None, data=None) -> Any:
        return await self._request("PUT", url, params=params, data=data)

    async def _delete(self, url, params=None) -> Any:
        return await self._request("DELETE", url, params=params)


class BaseCRUD:
    endpoint = ""

    def __init__(self, webex_teams: "WebexTeams"):
        self.webex_teams = webex_teams

    async def list(self) -> List[Dict[str, Any]]:
        response_data = await self.webex_teams._get(self.endpoint)
        return response_data["items"]

    async def get(self, id: str) -> Dict[str, Any]:
        response_data = await self.webex_teams._get(f"{self.endpoint}/{id}")
        return response_data

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response_data = await self.webex_teams._post(self.endpoint, data=data)
        return response_data

    async def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        url = "{endpoint}/{id}".format(endpoint=self.endpoint, id=data["id"])
        response_data = await self.webex_teams._put(url, data=data)
        return response_data

    async def delete(self, id: str) -> None:
        response_data = await self.webex_teams._delete(f"{self.endpoint}/{id}")
        return response_data


class WebhooksCRUD(BaseCRUD):
    endpoint = "/webhooks"


class MessagesCRUD(BaseCRUD):
    endpoint = "/messages"


class PeopleCRUD(BaseCRUD):
    endpoint = "/people"

    async def me(self) -> Dict[str, Any]:
        response_data = await self.webex_teams._get(f"{self.endpoint}/me")
        return response_data
