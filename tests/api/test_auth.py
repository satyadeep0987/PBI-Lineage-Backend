from unittest.mock import AsyncMock

from app.core.exceptions import (
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    UpstreamRateLimitError,
)
from app.services.auth.fabric_auth_service import (
    FabricAuthService,
)
from app.services.auth.powerbi_auth_service import (
    PowerBIAuthService,
)

POWERBI_CONTEXT = {
    "tenant_id": "test-tenant",
    "client_id": "test-client",
}


FABRIC_CONTEXT = {
    "tenant_id": "test-tenant",
    "client_id": "test-client",
}


AUTH_HEADERS = {
    "Authorization": (
        "Bearer fake-test-token"
    ),
}


def test_powerbi_validation_success(
    client,
    monkeypatch,
):
    validate_mock = AsyncMock(
        return_value=True
    )

    monkeypatch.setattr(
        PowerBIAuthService,
        "validate",
        validate_mock,
    )

    response = client.post(
        "/api/v1/auth/powerbi/validate",
        json=POWERBI_CONTEXT,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authenticated"] is True
    assert payload["provider"] == "powerbi"


def test_fabric_validation_success(
    client,
    monkeypatch,
):
    validate_mock = AsyncMock(
        return_value=True
    )

    monkeypatch.setattr(
        FabricAuthService,
        "validate",
        validate_mock,
    )

    response = client.post(
        "/api/v1/auth/fabric/validate",
        json=FABRIC_CONTEXT,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["authenticated"] is True
    assert payload["provider"] == "fabric"


def test_missing_authentication_credentials(
    client,
):
    response = client.post(
        "/api/v1/auth/powerbi/validate",
        json=POWERBI_CONTEXT,
    )

    assert response.status_code == 401

    payload = response.json()

    assert (
        payload["error"]["code"]
        == "AUTH_CREDENTIALS_REQUIRED"
    )

    assert "request_id" in payload["error"]


def test_invalid_powerbi_token(
    client,
    monkeypatch,
):
    validate_mock = AsyncMock(
        side_effect=InvalidAccessTokenError(
            "powerbi"
        )
    )

    monkeypatch.setattr(
        PowerBIAuthService,
        "validate",
        validate_mock,
    )

    response = client.post(
        "/api/v1/auth/powerbi/validate",
        json=POWERBI_CONTEXT,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 401

    payload = response.json()

    assert (
        payload["error"]["code"]
        == "AUTH_TOKEN_INVALID"
    )

    assert (
        payload["error"]["provider"]
        == "powerbi"
    )


def test_fabric_insufficient_permissions(
    client,
    monkeypatch,
):
    validate_mock = AsyncMock(
        side_effect=(
            InsufficientPermissionsError(
                "fabric"
            )
        )
    )

    monkeypatch.setattr(
        FabricAuthService,
        "validate",
        validate_mock,
    )

    response = client.post(
        "/api/v1/auth/fabric/validate",
        json=FABRIC_CONTEXT,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 403

    payload = response.json()

    assert (
        payload["error"]["code"]
        == "AUTH_INSUFFICIENT_PERMISSIONS"
    )


def test_powerbi_rate_limit(
    client,
    monkeypatch,
):
    validate_mock = AsyncMock(
        side_effect=UpstreamRateLimitError(
            provider="powerbi",
            retry_after="30",
        )
    )

    monkeypatch.setattr(
        PowerBIAuthService,
        "validate",
        validate_mock,
    )

    response = client.post(
        "/api/v1/auth/powerbi/validate",
        json=POWERBI_CONTEXT,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 429

    assert (
        response.headers["Retry-After"]
        == "30"
    )


def test_request_id_propagation(
    client,
):
    request_id = "frontend-test-123"

    response = client.post(
        "/api/v1/auth/powerbi/validate",
        json=POWERBI_CONTEXT,
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 401

    assert (
        response.headers["X-Request-ID"]
        == request_id
    )

    assert (
        response.json()["error"]["request_id"]
        == request_id
    )