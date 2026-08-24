from typing import Annotated

from fastapi import APIRouter, Depends, Cookie, HTTPException, Response

from app.api.dependencies.credentials import (
    get_powerbi_access_token,
    get_fabric_access_token
)

from app.schemas.auth import (
    AuthenticationResponse,
    FabricAuthContext,
    MicrosoftAuthPreparationResponse,
    MicrosoftAuthRequest,
    PowerBIAuthContext,
    MicrosoftDeviceAuthRequest,
    MicrosoftDeviceAuthStartResponse,
    MicrosoftDeviceAuthStatusResponse,
    ProviderTestResult,
)
from app.services.auth.fabric_auth_service import FabricAuthService
from app.services.auth.microsoft_auth_service import (
    MicrosoftAuthService,
)
from app.services.auth.powerbi_auth_service import PowerBIAuthService

from app.services.auth.microsoft_device_auth_service import (
    MicrosoftDeviceAuthService,
)

from app.core.auth_session import (
    AUTH_SESSION_COOKIE,
    AUTH_SESSION_MAX_AGE_SECONDS,
)

from app.services.auth.device_auth_store import (
    delete_device_session,
    get_device_session
)

from app.core.exceptions import (
    AuthenticationSessionRequiredError,
    AuthenticationSessionExpiredError
)

router = APIRouter()

# @router.post(
#     "/powerbi/validate",
#     response_model=AuthenticationResponse,
# )
# async def validate_powerbi_connection(
#     context: PowerBIAuthContext,
#     access_token: Annotated[
#         str,
#         Depends(get_powerbi_access_token),
#     ],
# ) -> AuthenticationResponse:
#     service = PowerBIAuthService()

#     await service.validate(
#         access_token=access_token,
#     )

#     return AuthenticationResponse(
#         authenticated=True,
#         provider="powerbi",
#         message="Power BI authentication validated successfully.",
#     )

# @router.post(
#     "/fabric/validate",
#     response_model=AuthenticationResponse,
# )
# async def validate_fabric_connection(
#     access_token: Annotated[
#         str,
#         Depends(
#             get_fabric_access_token
#         ),
#     ],
# ) -> AuthenticationResponse:

#     service = FabricAuthService()

#     await service.validate(
#         access_token=access_token,
#     )

#     return AuthenticationResponse(
#         authenticated=True,
#         provider="fabric",
#         message=(
#             "Fabric authentication "
#             "validated successfully."
#         ),
#     )

# @router.post(
#     "/powerbi/prepare",
#     response_model=MicrosoftAuthPreparationResponse,
# )
# async def prepare_powerbi_authentication(
#     request: MicrosoftAuthRequest,
# ) -> MicrosoftAuthPreparationResponse:
#     service = MicrosoftAuthService()

#     return service.prepare_powerbi_auth(
#         tenant_id=request.tenant_id,
#         client_id=request.client_id,
#     )

# @router.post(
#     "/fabric/prepare",
#     response_model=MicrosoftAuthPreparationResponse,
# )
# async def prepare_fabric_authentication(
#     request: MicrosoftAuthRequest,
# ) -> MicrosoftAuthPreparationResponse:
#     service = MicrosoftAuthService()

#     return service.prepare_fabric_auth(
#         tenant_id=request.tenant_id,
#         client_id=request.client_id,
#     )


# @router.get("/debug/cookie/set")
# async def debug_set_cookie(
#     response: Response,
# ) -> dict[str, str]:
#     response.set_cookie(
#         key="pbi_cookie_test",
#         value="cookie-test-123",
#         httponly=True,
#         secure=False,
#         samesite="lax",
#         path="/",
#         max_age=600,
#     )

#     return {
#         "status": "cookie_set"
#     }


# @router.get("/debug/cookie/check")
# async def debug_check_cookie(
#     cookie_value: str | None = Cookie(
#         default=None,
#         alias="pbi_cookie_test",
#     ),
# ) -> dict[str, str | None]:
#     return {
#         "cookie_value": cookie_value
#     }

@router.post(
    "/microsoft/device/start",
    response_model=MicrosoftDeviceAuthStartResponse,
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
        max_age=AUTH_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=False,       # IMPORTANT for localhost HTTP
        samesite="lax",
        path="/",
    )

    return MicrosoftDeviceAuthStartResponse(
        session_id=session_id,
        verification_uri=flow["verification_uri"],
        user_code=flow["user_code"],
        message=flow["message"],
        expires_in=int(
            flow.get(
                "expires_in",
                900,
            )
        ),
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

    if session.status == "pending":
        return MicrosoftDeviceAuthStatusResponse(
            status="pending",
            message=(
                "Waiting for Microsoft "
                "authentication."
            ),
        )

    if session.status == "failed":
        return MicrosoftDeviceAuthStatusResponse(
            status="failed",
            message=session.error_message,
        )

    return MicrosoftDeviceAuthStatusResponse(
        status="authenticated",
        powerbi=ProviderTestResult(
            connected=bool(
                session.powerbi_connected
            ),
            message=(
                "Power BI connection successful."
                if session.powerbi_connected
                else "Power BI connection failed."
            ),
        ),
        fabric=ProviderTestResult(
            connected=bool(
                session.fabric_connected
            ),
            message=(
                "Fabric connection successful."
                if session.fabric_connected
                else "Fabric connection failed."
            ),
        ),
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
        return MicrosoftDeviceAuthStatusResponse(
            status="pending",
            message=(
                "Waiting for Microsoft authentication."
            ),
        )

    if session.status == "failed":
        return MicrosoftDeviceAuthStatusResponse(
            status="failed",
            message=session.error_message,
        )

    return MicrosoftDeviceAuthStatusResponse(
        status="authenticated",
        powerbi=ProviderTestResult(
            connected=bool(
                session.powerbi_connected
            ),
            message=(
                "Power BI connection successful."
                if session.powerbi_connected
                else "Power BI connection failed."
            ),
        ),
        fabric=ProviderTestResult(
            connected=bool(
                session.fabric_connected
            ),
            message=(
                "Fabric connection successful."
                if session.fabric_connected
                else "Fabric authentication is not available."
            ),
        ),
        message=None,
    )

# @router.post(
#     "/microsoft/device/fabric/start",
#     response_model=(
#         MicrosoftDeviceAuthStartResponse
#     ),
# )
# async def start_fabric_device_authentication(
#     session_id: str | None = Cookie(
#         default=None,
#         alias=AUTH_SESSION_COOKIE,
#     ),
# ) -> MicrosoftDeviceAuthStartResponse:

#     if session_id is None:
#         raise AuthenticationSessionRequiredError()

#     service = MicrosoftDeviceAuthService()

#     flow = (
#         await service.start_fabric_authentication(
#             session_id=session_id,
#         )
#     )

#     return MicrosoftDeviceAuthStartResponse(
#         session_id=session_id,
#         verification_uri=flow[
#             "verification_uri"
#         ],
#         user_code=flow[
#             "user_code"
#         ],
#         message=flow[
#             "message"
#         ],
#         expires_in=int(
#             flow.get(
#                 "expires_in",
#                 900,
#             )
#         ),
#     )

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