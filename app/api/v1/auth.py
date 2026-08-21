from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies.credentials import get_bearer_token
from app.schemas.auth import (
    AuthenticationResponse,
    FabricAuthContext,
    PowerBIAuthContext,
)
from app.services.auth.fabric_auth_service import FabricAuthService
from app.services.auth.powerbi_auth_service import PowerBIAuthService

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

    await service.validate(
        access_token=access_token,
    )

    return AuthenticationResponse(
        authenticated=True,
        provider="powerbi",
        message="Power BI authentication validated successfully.",
    )

@router.post(
    "/fabric/validate",
    response_model=AuthenticationResponse,
)
async def validate_fabric_connection(
    context: FabricAuthContext,
    access_token: Annotated[
        str,
        Depends(get_bearer_token),
    ],
) -> AuthenticationResponse:
    service = FabricAuthService()

    await service.validate(
        access_token=access_token,
    )

    return AuthenticationResponse(
        authenticated=True,
        provider="fabric",
        message="Fabric authentication validated successfully.",
    )