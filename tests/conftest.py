"""Fixtures del servicio HTTP: una app aislada, con su propia clave y sin llamar nunca a Groq."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from redsana_ai_service.composition import build_anomaly_detector
from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.main import create_app
from redsana_ai_service.readiness import ServiceReadiness
from redsana_ai_service.security import API_KEY_HEADER

_TEST_SERVICE_KEY = "test-service-key"


@pytest.fixture
def service_app() -> FastAPI:
    settings = ServiceSettings(_env_file=None, ai_service_api_key=_TEST_SERVICE_KEY, groq_api_key="")
    return create_app(settings, ServiceReadiness(build_anomaly_detector()))


@pytest.fixture
def service_client(service_app: FastAPI) -> TestClient:
    return TestClient(service_app, headers={API_KEY_HEADER: _TEST_SERVICE_KEY})
