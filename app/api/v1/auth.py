from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.credentials import get_bearer_token
from app.schemas.auth import (
    AuthenticationResponse,
    PowerBIAuthContext,
)
from app.services.auth.powerbi_auth_service import (
    PowerBIAuthService,
)


router = APIRouter()


@router.post(
    "/powerbi/validate",
    response_model=AuthenticationResponse,
)
async def validate_powerbi_connection(
    context: PowerBIAuthContext,
    access_token: Annotated[
        str,
        Depends(get_bearer_token),
    ],
) -> AuthenticationResponse:
    service = PowerBIAuthService()

    authenticated = await service.validate(
        access_token=access_token,
    )

    if authenticated:
        return AuthenticationResponse(
            authenticated=True,
            provider="powerbi",
            message="Power BI authentication validated successfully.",
        )

    return AuthenticationResponse(
        authenticated=False,
        provider="powerbi",
        message="Unable to validate Power BI authentication.",
    )