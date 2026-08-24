from fastapi import APIRouter

from app.api.v1 import (
    auth,
    health,
    workspaces,
)

from app.core.auth_session import (
    AUTH_SESSION_COOKIE,
    AUTH_SESSION_MAX_AGE_SECONDS,
)

api_router = APIRouter()

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    workspaces.router,
    prefix="/workspaces",
    tags=["Workspaces"],
)