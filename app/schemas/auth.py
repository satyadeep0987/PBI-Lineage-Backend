from pydantic import BaseModel


class PowerBIAuthContext(BaseModel):
    tenant_id: str
    client_id: str


class AuthenticationResponse(BaseModel):
    authenticated: bool
    provider: str
    message: str