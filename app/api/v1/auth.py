
from fastapi import APIRouter, Cookie, Response

from app.core.auth_session import (
    AUTH_SESSION_COOKIE,
    AUTH_SESSION_MAX_AGE_SECONDS,
)
from app.core.exceptions import (
    AuthenticationSessionExpiredError,
    AuthenticationSessionRequiredError,
)
from app.core.microsoft_auth import (
    FABRIC_SCOPES,
    POWERBI_SCOPES,
    get_scope_permission,
    normalize_scope_permissions,
)
from app.schemas.auth import (
    MicrosoftDeviceAuthRequest,
    MicrosoftDeviceAuthStartResponse,
    MicrosoftDeviceAuthStatusResponse,
    ProviderScopeAccess,
    ProviderTestResult,
)
from app.services.auth.device_auth_store import (
    DeviceAuthSession,
    delete_device_session,
    get_device_session,
)
from app.services.auth.microsoft_device_auth_service import (
    MicrosoftDeviceAuthService,
)

router = APIRouter()

def _build_scope_access(
    *,
    requested_scopes: list[str],
    granted_scopes: list[str],
) -> list[ProviderScopeAccess]:
    granted_permissions = set(
        normalize_scope_permissions(
            granted_scopes
        )
    )

    return [
        ProviderScopeAccess(
            scope=scope,
            permission=get_scope_permission(
                scope
            ),
            granted=(
                get_scope_permission(scope)
                in granted_permissions
            ),
        )
        for scope in requested_scopes
    ]


def _build_provider_test_result(
    *,
    connected: bool,
    success_message: str,
    failure_message: str,
    requested_scopes: list[str],
    granted_scopes: list[str],
    error_code: str | None = None,
) -> ProviderTestResult:
    scope_access = _build_scope_access(
        requested_scopes=requested_scopes,
        granted_scopes=granted_scopes,
    )

    missing_scopes = [
        item.scope
        for item in scope_access
        if not item.granted
    ]

    message = (
        success_message
        if connected
        else failure_message
    )

    if not connected and error_code:
        message = f"{message}: {error_code}"

    return ProviderTestResult(
        connected=connected,
        message=message,
        error_code=error_code,
        requested_scopes=requested_scopes,
        granted_scopes=normalize_scope_permissions(
            granted_scopes
        ),
        missing_scopes=missing_scopes,
        scope_access=scope_access,
    )


def _build_device_status_response(
    session: DeviceAuthSession,
) -> MicrosoftDeviceAuthStatusResponse:
    if session.status == "pending":
        return MicrosoftDeviceAuthStatusResponse(
            status="pending",
            powerbi=_build_provider_test_result(
                connected=False,
                success_message=(
                    "Power BI connection successful."
                ),
                failure_message=(
                    "Power BI authentication is pending."
                ),
                requested_scopes=POWERBI_SCOPES,
                granted_scopes=[],
            ),
            fabric=_build_provider_test_result(
                connected=False,
                success_message=(
                    "Fabric connection successful."
                ),
                failure_message=(
                    "Fabric authentication is pending."
                ),
                requested_scopes=FABRIC_SCOPES,
                granted_scopes=[],
            ),
            message=(
                "Waiting for Microsoft authentication."
            ),
        )

    if session.status == "failed":
        return MicrosoftDeviceAuthStatusResponse(
            status="failed",
            powerbi=_build_provider_test_result(
                connected=False,
                success_message=(
                    "Power BI connection successful."
                ),
                failure_message=(
                    "Power BI connection failed."
                ),
                requested_scopes=POWERBI_SCOPES,
                granted_scopes=(
                    session.powerbi_granted_scopes
                ),
                error_code=(
                    session.powerbi_error_code
                ),
            ),
            fabric=_build_provider_test_result(
                connected=False,
                success_message=(
                    "Fabric connection successful."
                ),
                failure_message=(
                    "Fabric authentication is not available."
                ),
                requested_scopes=FABRIC_SCOPES,
                granted_scopes=(
                    session.fabric_granted_scopes
                ),
                error_code=(
                    session.fabric_error_code
                ),
            ),
            message=session.error_message,
        )

    return MicrosoftDeviceAuthStatusResponse(
        status="authenticated",
        powerbi=_build_provider_test_result(
            connected=bool(
                session.powerbi_connected
            ),
            success_message=(
                "Power BI connection successful."
            ),
            failure_message=(
                "Power BI connection failed."
            ),
            requested_scopes=POWERBI_SCOPES,
            granted_scopes=(
                session.powerbi_granted_scopes
            ),
            error_code=session.powerbi_error_code,
        ),
        fabric=_build_provider_test_result(
            connected=bool(
                session.fabric_connected
            ),
            success_message=(
                "Fabric connection successful."
            ),
            failure_message=(
                "Fabric authentication is not available."
            ),
            requested_scopes=FABRIC_SCOPES,
            granted_scopes=(
                session.fabric_granted_scopes
            ),
            error_code=session.fabric_error_code,
        ),
        message=None,
    )


@router.get(
    "/microsoft/device/{session_id}/status",
    response_model=MicrosoftDeviceAuthStatusResponse,
)
async def get_microsoft_device_authentication_status(
    session_id: str,
) -> MicrosoftDeviceAuthStatusResponse:
    session = get_device_session(
        session_id
    )

    if session is None:
        return MicrosoftDeviceAuthStatusResponse(
            status="expired",
            message=(
                "Authentication session "
                "does not exist or has expired."
            ),
        )

    return _build_device_status_response(
        session
    )

@router.post(
    "/microsoft/device/start",
    response_model=(
        MicrosoftDeviceAuthStartResponse
    ),
)
async def start_microsoft_device_authentication(
    request: MicrosoftDeviceAuthRequest,
    response: Response,
) -> MicrosoftDeviceAuthStartResponse:
    service = MicrosoftDeviceAuthService()

    session_id, flow = await service.start(
        tenant_id=request.tenant_id,
        client_id=request.client_id,
    )

    response.set_cookie(
        key=AUTH_SESSION_COOKIE,
        value=session_id,
        max_age=(
            AUTH_SESSION_MAX_AGE_SECONDS
        ),
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    return MicrosoftDeviceAuthStartResponse(
        session_id=session_id,
        verification_uri=flow[
            "verification_uri"
        ],
        user_code=flow[
            "user_code"
        ],
        message=flow[
            "message"
        ],
        expires_in=int(
            flow.get(
                "expires_in",
                900,
            )
        ),
    )


@router.get(
    "/microsoft/device/status",
    response_model=MicrosoftDeviceAuthStatusResponse,
)
async def get_microsoft_device_auth_status(
    session_id: str | None = Cookie(
        default=None,
        alias=AUTH_SESSION_COOKIE,
    ),
) -> MicrosoftDeviceAuthStatusResponse:

    if session_id is None:
        raise AuthenticationSessionRequiredError()

    session = get_device_session(
        session_id
    )

    if session is None:
        raise AuthenticationSessionExpiredError()

    if session.status == "pending":
        return _build_device_status_response(
            session
        )

    if session.status == "failed":
        return _build_device_status_response(
            session
        )

    return _build_device_status_response(
        session
    )

@router.post(
    "/microsoft/device/logout",
)
async def logout_microsoft_device_session(
    response: Response,
    session_id: str | None = Cookie(
        default=None,
        alias=AUTH_SESSION_COOKIE,
    ),
) -> dict[str, str]:

    if session_id:
        delete_device_session(
            session_id
        )

    response.delete_cookie(
        key=AUTH_SESSION_COOKIE,
        path="/",
    )

    return {
        "status": "logged_out"
    }