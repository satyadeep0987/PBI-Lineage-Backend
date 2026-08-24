from typing import Any

import httpx

from app.core.exceptions import (
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    UpstreamRateLimitError,
    UpstreamRequestError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
    ProviderResourceNotFoundError
)

DEFAULT_TIMEOUT_SECONDS = 30.0


def _handle_provider_response(
    response: httpx.Response,
    provider: str,
) -> None:
    if response.is_success:
        return

    if response.status_code == 401:
        raise InvalidAccessTokenError(provider)

    if response.status_code == 403:
        raise InsufficientPermissionsError(provider)

    if response.status_code == 429:
        raise UpstreamRateLimitError(
            provider=provider,
            retry_after=response.headers.get("Retry-After"),
        )

    if response.status_code >= 500:
        raise UpstreamUnavailableError(provider)

    raise UpstreamRequestError(provider)


async def provider_get(
    *,
    provider: str,
    url: str,
    access_token: str,
    params: dict[str, Any] | None = None,
    not_found_resource: str | None = None,
) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS),
        ) as client:
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )

    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(provider) from exc

    except httpx.RequestError as exc:
        raise UpstreamUnavailableError(provider) from exc

    _handle_provider_response(
        response=response,
        provider=provider,
    )

    if (
        response.status_code == 404
        and not_found_resource
    ):
        raise ProviderResourceNotFoundError(
            provider=provider,
            resource=not_found_resource,
        )

    return response