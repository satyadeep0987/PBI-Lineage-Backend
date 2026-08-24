from typing import Any

from app.clients.provider_http_client import provider_get
from app.core.exceptions import UpstreamInvalidResponseError


class PowerBIClient:
    BASE_URL = "https://api.powerbi.com/v1.0/myorg"

    async def validate_connection(
        self,
        access_token: str,
    ) -> bool:
        await provider_get(
            provider="powerbi",
            url=f"{self.BASE_URL}/groups",
            access_token=access_token,
            params={
                "$top": 1,
            },
        )

        return True

    async def get_workspaces(
        self,
        *,
        access_token: str,
        top: int,
        skip: int,
    ) -> list[dict[str, Any]]:
        response = await provider_get(
            provider="powerbi",
            url=f"{self.BASE_URL}/groups",
            access_token=access_token,
            params={
                "$top": top,
                "$skip": skip,
            },
        )

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamInvalidResponseError(
                "powerbi"
            ) from exc

        workspaces = payload.get("value")

        if not isinstance(workspaces, list):
            raise UpstreamInvalidResponseError(
                "powerbi"
            )

        return workspaces