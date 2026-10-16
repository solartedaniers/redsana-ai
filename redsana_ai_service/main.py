from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from redsana_ai_service.composition import build_anomaly_detector
from redsana_ai_service.config import ServiceSettings, get_settings
from redsana_ai_service.errors import register_error_handlers
from redsana_ai_service.readiness import ServiceReadiness
from redsana_ai_service.routers import anomaly, briefing, chat, health


def create_app(settings: ServiceSettings | None = None, readiness: ServiceReadiness | None = None) -> FastAPI:
    settings = settings or get_settings()
    readiness = readiness or ServiceReadiness(build_anomaly_detector())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        readiness.start_warm_up()
        yield

    docs_enabled = settings.enable_api_docs
    app = FastAPI(
        title="RedSana AI Service",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.state.settings = settings
    app.state.readiness = readiness
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(briefing.router)
    app.include_router(anomaly.router)
    return app


app = create_app()
