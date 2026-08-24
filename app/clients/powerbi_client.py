from typing import Any

import httpx

from app.clients.provider_http_client import provider_get
from app.core.exceptions import UpstreamInvalidResponseError


class PowerBIClient:
    BASE_URL = "https://api.powerbi.com/v1.0/myorg"

    @staticmethod
    def _parse_object_response(
        response: httpx.Response,
    ) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamInvalidResponseError(
                "powerbi"
            ) from exc

        if not isinstance(payload, dict):
            raise UpstreamInvalidResponseError(
                "powerbi"
            )

        return payload

    @staticmethod
    def _parse_list_response(
        response: httpx.Response,
    ) -> list[dict[str, Any]]:
        payload = PowerBIClient._parse_object_response(
            response
        )

        items = payload.get("value")

        if not isinstance(items, list):
            raise UpstreamInvalidResponseError(
                "powerbi"
            )

        if not all(
            isinstance(item, dict)
            for item in items
        ):
            raise UpstreamInvalidResponseError(
                "powerbi"
            )

        return items

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

        return self._parse_list_response(
            response
        )

    async def get_workspace(
        self,
        *,
        workspace_id: str,
        access_token: str,
    ) -> dict[str, Any]:
        response = await provider_get(
            provider="powerbi",
            url=(
                f"{self.BASE_URL}/groups/"
                f"{workspace_id}"
            ),
            access_token=access_token,
        )

        return self._parse_object_response(
            response
        )

    async def get_reports_in_workspace(
        self,
        *,
        workspace_id: str,
        access_token: str,
    ) -> list[dict[str, Any]]:
        response = await provider_get(
            provider="powerbi",
            url=(
                f"{self.BASE_URL}/groups/"
                f"{workspace_id}/reports"
            ),
            access_token=access_token,
        )

        return self._parse_list_response(
            response
        )

    async def get_semantic_models_in_workspace(
        self,
        *,
        workspace_id: str,
        access_token: str,
    ) -> list[dict[str, Any]]:
        response = await provider_get(
            provider="powerbi",
            url=(
                f"{self.BASE_URL}/groups/"
                f"{workspace_id}/datasets"
            ),
            access_token=access_token,
        )

        return self._parse_list_response(
            response
        )