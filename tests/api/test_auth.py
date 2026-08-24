from uuid import uuid4

from app.core.auth_session import AUTH_SESSION_COOKIE
from app.services.auth.device_auth_store import (
    DeviceAuthSession,
    delete_device_session,
    save_device_session,
)
from app.services.auth.microsoft_device_auth_service import (
    MicrosoftDeviceAuthService,
)


def _create_session(
    *,
    status: str,
    powerbi_connected: bool | None = None,
    fabric_connected: bool | None = None,
    error_message: str | None = None,
) -> str:
    session_id = str(uuid4())

    session = DeviceAuthSession(
        flow={},
        tenant_id="test-tenant",
        client_id="test-client",
    )

    session.status = status
    session.powerbi_connected = powerbi_connected
    session.fabric_connected = fabric_connected
    session.error_message = error_message

    save_device_session(
        session_id,
        session,
    )

    return session_id


def test_microsoft_device_start_success(
    client,
    monkeypatch,
):
    async def fake_start(
        self,
        *,
        tenant_id: str,
        client_id: str,
    ):
        return (
            "test-session-id",
            {
                "verification_uri": (
                    "https://microsoft.com/devicelogin"
                ),
                "user_code": "TEST-CODE",
                "message": "Authenticate with Microsoft.",
                "expires_in": 900,
            },
        )

    monkeypatch.setattr(
        MicrosoftDeviceAuthService,
        "start",
        fake_start,
    )

    client.cookies.clear()

    response = client.post(
        "/api/v1/auth/microsoft/device/start",
        json={
            "tenant_id": "test-tenant",
            "client_id": "test-client",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["session_id"] == "test-session-id"
    assert payload["user_code"] == "TEST-CODE"
    assert payload["expires_in"] == 900

    assert (
        response.cookies.get(
            AUTH_SESSION_COOKIE
        )
        == "test-session-id"
    )

    client.cookies.clear()


def test_device_status_requires_session(
    client,
):
    client.cookies.clear()

    response = client.get(
        "/api/v1/auth/microsoft/device/status"
    )

    assert response.status_code == 401


def test_device_status_pending(
    client,
):
    session_id = _create_session(
        status="pending",
    )

    try:
        client.cookies.clear()

        client.cookies.set(
            AUTH_SESSION_COOKIE,
            session_id,
        )

        response = client.get(
            "/api/v1/auth/microsoft/device/status"
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["status"] == "pending"

    finally:
        delete_device_session(session_id)
        client.cookies.clear()


def test_device_status_authenticated(
    client,
):
    session_id = _create_session(
        status="authenticated",
        powerbi_connected=True,
        fabric_connected=True,
    )

    try:
        client.cookies.clear()

        client.cookies.set(
            AUTH_SESSION_COOKIE,
            session_id,
        )

        response = client.get(
            "/api/v1/auth/microsoft/device/status"
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["status"] == "authenticated"

        assert (
            payload["powerbi"]["connected"]
            is True
        )

        assert (
            payload["fabric"]["connected"]
            is True
        )

    finally:
        delete_device_session(session_id)
        client.cookies.clear()


def test_device_status_powerbi_connected_fabric_not_connected(
    client,
):
    session_id = _create_session(
        status="authenticated",
        powerbi_connected=True,
        fabric_connected=False,
    )

    try:
        client.cookies.clear()

        client.cookies.set(
            AUTH_SESSION_COOKIE,
            session_id,
        )

        response = client.get(
            "/api/v1/auth/microsoft/device/status"
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["status"] == "authenticated"

        assert (
            payload["powerbi"]["connected"]
            is True
        )

        assert (
            payload["fabric"]["connected"]
            is False
        )

    finally:
        delete_device_session(session_id)
        client.cookies.clear()


def test_device_status_failed(
    client,
):
    session_id = _create_session(
        status="failed",
        powerbi_connected=False,
        fabric_connected=False,
        error_message="Authentication failed.",
    )

    try:
        client.cookies.clear()

        client.cookies.set(
            AUTH_SESSION_COOKIE,
            session_id,
        )

        response = client.get(
            "/api/v1/auth/microsoft/device/status"
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["status"] == "failed"

        assert (
            payload["message"]
            == "Authentication failed."
        )

    finally:
        delete_device_session(session_id)
        client.cookies.clear()


def test_logout_success(
    client,
):
    session_id = _create_session(
        status="authenticated",
        powerbi_connected=True,
        fabric_connected=True,
    )

    client.cookies.clear()

    client.cookies.set(
        AUTH_SESSION_COOKIE,
        session_id,
    )

    response = client.post(
        "/api/v1/auth/microsoft/device/logout"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "logged_out"

    client.cookies.clear()


def test_request_id_propagation(
    client,
):
    client.cookies.clear()

    request_id = "auth-test-request-id"

    response = client.get(
        "/api/v1/auth/microsoft/device/status",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 401

    assert (
        response.headers["X-Request-ID"]
        == request_id
    )