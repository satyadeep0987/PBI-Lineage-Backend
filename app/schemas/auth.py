from typing import Literal

from pydantic import BaseModel, Field


class MicrosoftAuthRequest(BaseModel):
    tenant_id: str = Field(
        min_length=1,
        max_length=128,
    )
    client_id: str = Field(
        min_length=1,
        max_length=128,
    )


class MicrosoftAuthPreparationResponse(BaseModel):
    provider: Literal[
        "powerbi",
        "fabric",
    ]

    tenant_id: str
    client_id: str
    authority: str
    scopes: list[str]

    authentication_flow: str = (
        "authorization_code_pkce"
    )


class PowerBIAuthContext(BaseModel):
    tenant_id: str
    client_id: str


class FabricAuthContext(BaseModel):
    tenant_id: str
    client_id: str


class AuthenticationResponse(BaseModel):
    authenticated: bool
    provider: str
    message: str


# ------------------------------------------------------------------
# Device-code authentication schemas
# Used for development/backend connectivity testing
# ------------------------------------------------------------------


class MicrosoftDeviceAuthRequest(BaseModel):
    tenant_id: str = Field(
        min_length=1,
        max_length=128,
    )

    client_id: str = Field(
        min_length=1,
        max_length=128,
    )


class MicrosoftDeviceAuthStartResponse(BaseModel):
    session_id: str

    verification_uri: str

    user_code: str

    message: str

    expires_in: int


class ProviderScopeAccess(BaseModel):
    scope: str
    permission: str
    granted: bool


class ProviderTestResult(BaseModel):
    connected: bool
    message: str

    error_code: str | None = None

    requested_scopes: list[str] = Field(
        default_factory=list
    )

    granted_scopes: list[str] = Field(
        default_factory=list
    )

    missing_scopes: list[str] = Field(
        default_factory=list
    )

    scope_access: list[ProviderScopeAccess] = Field(
        default_factory=list
    )

class MicrosoftDeviceAuthStatusResponse(BaseModel):
    status: Literal[
        "pending",
        "authenticated",
        "failed",
        "expired",
    ]

    powerbi: ProviderTestResult | None = None

    fabric: ProviderTestResult | None = None

    message: str | None = None