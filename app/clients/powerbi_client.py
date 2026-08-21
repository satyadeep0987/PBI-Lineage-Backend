from app.clients.provider_http_client import provider_get


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