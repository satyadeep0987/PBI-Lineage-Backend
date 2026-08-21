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