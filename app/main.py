from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_id import RequestIDMiddleware
from app.core.request_logging import RequestLoggingMiddleware

settings = get_settings()

configure_logging(
    settings.log_level
)



settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        RequestLoggingMiddleware,
    )

    app.add_middleware(
        RequestIDMiddleware,
    )

    register_exception_handlers(app)

    app.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return app


app = create_app()