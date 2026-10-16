"""Todo error sale con el mismo cuerpo tipado {code, message} y sin detalles internos."""
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from redsana_ai import GroqClientError

from redsana_ai_service.errors import ServiceError, ServiceErrorCode, register_error_handlers


class _Payload(BaseModel):
    value: int


def _client() -> TestClient:
    router = APIRouter()

    @router.post("/validated")
    def validated(payload: _Payload) -> dict[str, int]:
        return {"value": payload.value}

    @router.get("/service-error")
    def service_error() -> None:
        raise ServiceError(418, ServiceErrorCode.SERVICE_MISCONFIGURED, "teapot")

    @router.get("/engine-error")
    def engine_error() -> None:
        raise GroqClientError("Groq API error 429: secret provider detail")

    @router.get("/unexpected")
    def unexpected() -> None:
        raise RuntimeError("internal stack detail")

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_service_errors_keep_their_status_and_code() -> None:
    response = _client().get("/service-error")

    assert response.status_code == 418
    assert response.json() == {"code": "service_misconfigured", "message": "teapot"}


def test_validation_errors_name_the_invalid_fields() -> None:
    response = _client().post("/validated", json={"value": "not-a-number"})

    assert response.status_code == 422
    assert response.json() == {"code": "validation_error", "message": "invalid fields: body.value"}


def test_chat_engine_errors_hide_the_provider_detail() -> None:
    response = _client().get("/engine-error")

    assert response.status_code == 502
    assert response.json() == {"code": "chat_engine_unavailable", "message": "chat engine unavailable"}


def test_unknown_routes_use_the_same_error_body() -> None:
    response = _client().get("/missing")

    assert response.status_code == 404
    assert response.json() == {"code": "http_error", "message": "Not Found"}


def test_unexpected_errors_hide_the_internal_detail() -> None:
    response = _client().get("/unexpected")

    assert response.status_code == 500
    assert response.json() == {"code": "internal_error", "message": "internal error"}
