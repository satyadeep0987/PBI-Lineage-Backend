from typing import Any

from app.core.exceptions import (
    ProviderIntegrationNotConfiguredError,
)


class XmlaClient:
    BASE_ENDPOINT = (
        "powerbi://api.powerbi.com/v1.0/myorg"
    )

    def build_workspace_endpoint(
        self,
        *,
        workspace_id: str,
        workspace_name: str | None = None,
    ) -> str:
        workspace_target = (
            workspace_name or workspace_id
        )

        return (
            f"{self.BASE_ENDPOINT}/"
            f"{workspace_target}"
        )

    async def get_semantic_model_metadata(
        self,
        *,
        workspace_id: str,
        semantic_model_id: str,
        access_token: str,
        workspace_name: str | None = None,
        database_name: str | None = None,
    ) -> dict[str, Any]:
        raise ProviderIntegrationNotConfiguredError(
            "xmla"
        )
