from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()

settings = get_settings()


@router.get("")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    return {
        "status": "alive",
    }


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    return {
        "status": "ready",
    }