import httpx


class PowerBIClient:
    BASE_URL = "https://api.powerbi.com/v1.0/myorg"

    async def validate_connection(
        self,
        access_token: str,
    ) -> bool:
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
        ) as client:
            response = await client.get(
                f"{self.BASE_URL}/groups",
                headers=headers,
                params={"$top": 1},
            )

        return response.is_success