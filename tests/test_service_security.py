"""Las rutas protegidas exigen la clave compartida; sin clave configurada el servicio queda cerrado."""
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from redsana_ai_service.composition import build_anomaly_detector
from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.main import create_app
from redsana_ai_service.readiness import ServiceReadiness
from redsana_ai_service.security import API_KEY_HEADER, require_api_key


def _client(api_key: str) -> TestClient:
    app = create_app(ServiceSettings(_env_file=None, ai_service_api_key=api_key), ServiceReadiness(build_anomaly_detector()))
    protected = APIRouter(dependencies=[Depends(require_api_key)])

    @protected.get("/protected")
    def protected_route() -> dict[str, bool]:
        return {"ok": True}

    app.include_router(protected)
    return TestClient(app)


def test_the_right_key_is_accepted() -> None:
    response = _client("shared-key").get("/protected", headers={API_KEY_HEADER: "shared-key"})

    assert response.status_code == 200


def test_a_missing_key_is_rejected() -> None:
    response = _client("shared-key").get("/protected")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_api_key"


def test_a_wrong_key_is_rejected() -> None:
    response = _client("shared-key").get("/protected", headers={API_KEY_HEADER: "other-key"})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_api_key"


def test_without_a_configured_key_every_protected_request_is_refused() -> None:
    response = _client("").get("/protected", headers={API_KEY_HEADER: ""})

    assert response.status_code == 503
    assert response.json()["code"] == "service_misconfigured"


def test_health_does_not_need_the_key() -> None:
    assert _client("shared-key").get("/health").status_code == 200
