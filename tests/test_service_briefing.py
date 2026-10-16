"""POST /v1/briefing redacta el primer mensaje tras una evaluación con EngineSecurityBriefing."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redsana_ai import ChatEngine, ChatTurn, GroqClientError

from redsana_ai_service.composition import get_chat_engine


class _FixedEngine(ChatEngine):
    def __init__(self) -> None:
        self.turns: list[ChatTurn] = []

    def complete(self, system_prompt: str, turns: list[ChatTurn]) -> str:
        self.turns = turns
        return "## Tu puntaje\nEs **68/100**."


class _FailingEngine(ChatEngine):
    def complete(self, system_prompt: str, turns: list[ChatTurn]) -> str:
        raise GroqClientError("no se pudo contactar a Groq")


def test_briefing_returns_the_cleaned_text_in_the_requested_language(
    service_app: FastAPI, service_client: TestClient
) -> None:
    engine = _FixedEngine()
    service_app.dependency_overrides[get_chat_engine] = lambda: engine

    response = service_client.post("/v1/briefing", json={"user_context": "- Puntaje: 68.", "language": "en"})

    assert response.status_code == 200
    assert response.json() == {"text": "Tu puntaje\nEs 68/100."}
    assert "en ingles" in engine.turns[0].content


def test_briefing_rejects_an_unsupported_language(service_client: TestClient) -> None:
    response = service_client.post("/v1/briefing", json={"user_context": "", "language": "fr"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_briefing_engine_failures_are_a_typed_502(service_app: FastAPI, service_client: TestClient) -> None:
    service_app.dependency_overrides[get_chat_engine] = lambda: _FailingEngine()

    response = service_client.post("/v1/briefing", json={"user_context": "", "language": "es"})

    assert response.status_code == 502
    assert response.json()["code"] == "chat_engine_unavailable"


def test_briefing_requires_the_api_key(service_app: FastAPI) -> None:
    response = TestClient(service_app).post("/v1/briefing", json={"user_context": "", "language": "es"})

    assert response.status_code == 401
