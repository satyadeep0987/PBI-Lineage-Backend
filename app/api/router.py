from fastapi import APIRouter

from app.api.v1 import (
    auth,
    health,
    workspaces,
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