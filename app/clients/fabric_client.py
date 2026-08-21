from app.clients.provider_http_client import provider_get


class FabricClient:
    BASE_URL = "https://api.fabric.microsoft.com/v1"

    async def validate_connection(
        self,
        access_token: str,
    ) -> bool:
        await provider_get(
            provider="fabric",
            url=f"{self.BASE_URL}/workspaces",
            access_token=access_token,
        )

        return True