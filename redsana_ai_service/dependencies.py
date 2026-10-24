"""Dependencias de FastAPI que leen lo que create_app dejó en app.state (así cada app de prueba trae lo suyo)."""

from fastapi import Request

from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.readiness import ServiceReadiness


def get_service_settings(request: Request) -> ServiceSettings:
    return request.app.state.settings


def get_readiness(request: Request) -> ServiceReadiness:
    return request.app.state.readiness
