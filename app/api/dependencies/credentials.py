from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.core.exceptions import (
    InvalidAuthenticationSchemeError,
    MissingAuthenticationCredentialsError,
)

bearer_scheme = HTTPBearer(
    auto_error=False,
)


async def get_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if credentials is None:
        raise (
            MissingAuthenticationCredentialsError()
        )

    if credentials.scheme.lower() != "bearer":
        raise (
            InvalidAuthenticationSchemeError()
        )

    return credentials.credentials