from typing import Any

import httpx

from app.core.exceptions import (
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    ProviderResourceNotFoundError,
    UpstreamRateLimitError,
    UpstreamRequestError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

DEFAULT_TIMEOUT_SECONDS = 30.0


def _handle_provider_response(
    *,
    response: httpx.Response,
    provider: str,
    not_found_resource: str | None = None,
) -> None:
    if response.is_success:
        return

    if response.status_code == 401:
        raise InvalidAccessTokenError(
            provider
        )

    if response.status_code == 403:
        raise InsufficientPermissionsError(
            provider
        )

    if (
        response.status_code == 404
        and not_found_resource
    ):
        raise ProviderResourceNotFoundError(
            provider=provider,
            resource=not_found_resource,
        )

    if response.status_code == 429:
        raise UpstreamRateLimitError(
            provider=provider,
            retry_after=response.headers.get(
                "Retry-After"
            ),
        )

    if response.status_code >= 500:
        raise UpstreamUnavailableError(
            provider
        )

    raise UpstreamRequestError(
        provider
    )


async def _provider_request(
    *,
    method: str,
    provider: str,
    url: str,
    access_token: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    not_found_resource: str | None = None,
) -> httpx.Response:
    headers = {
        "Authorization": (
            f"Bearer {access_token}"
        ),
        "Accept": "application/json",
    }

    request_kwargs: dict[
        str,
        Any,
    ] = {
        "headers": headers,
        "params": params,
    }

    if json_body is not None:
        request_kwargs["json"] = (
            json_body
        )

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                DEFAULT_TIMEOUT_SECONDS
            ),
        ) as client:
            response = await client.request(
                method=method,
                url=url,
                **request_kwargs,
            )

    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(
            provider
        ) from exc

    except httpx.RequestError as exc:
        raise UpstreamUnavailableError(
            provider
        ) from exc

    _handle_provider_response(
        response=response,
        provider=provider,
        not_found_resource=(
            not_found_resource
        ),
    )

    return response


async def provider_get(
    *,
    provider: str,
    url: str,
    access_token: str,
    params: dict[str, Any] | None = None,
    not_found_resource: str | None = None,
) -> httpx.Response:
    return await _provider_request(
        method="GET",
        provider=provider,
        url=url,
        access_token=access_token,
        params=params,
        not_found_resource=(
            not_found_resource
        ),
    )


async def provider_post(
    *,
    provider: str,
    url: str,
    access_token: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    not_found_resource: str | None = None,
) -> httpx.Response:
    return await _provider_request(
        method="POST",
        provider=provider,
        url=url,
        access_token=access_token,
        params=params,
        json_body=json_body,
        not_found_resource=(
            not_found_resource
        ),
    )