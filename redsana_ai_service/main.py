from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from redsana_ai_service.composition import build_anomaly_detector
from redsana_ai_service.config import ServiceSettings, get_settings
from redsana_ai_service.readiness import ServiceReadiness
from redsana_ai_service.routers import health


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
    app.state.readiness = readiness
    app.include_router(health.router)
    return app


app = create_app()
