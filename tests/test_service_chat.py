"""POST /v1/chat responde con EngineSecurityChat; el motor se reemplaza para no llamar a Groq."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redsana_ai import ChatEngine, ChatTurn, GroqClientError

from redsana_ai_service.composition import get_chat_engine


class _FixedEngine(ChatEngine):
    def __init__(self, reply: str = "**Todo** bien") -> None:
        self.calls: list[tuple[str, list[ChatTurn]]] = []
        self._reply = reply

    def complete(self, system_prompt: str, turns: list[ChatTurn]) -> str:
        self.calls.append((system_prompt, turns))
        return self._reply


class _FailingEngine(ChatEngine):
    def complete(self, system_prompt: str, turns: list[ChatTurn]) -> str:
        raise GroqClientError("Groq API error 500: provider detail")


def test_chat_returns_the_cleaned_reply_and_sends_history_in_order(
    service_app: FastAPI, service_client: TestClient
) -> None:
    engine = _FixedEngine()
    service_app.dependency_overrides[get_chat_engine] = lambda: engine

    response = service_client.post(
        "/v1/chat",
        json={
            "user_context": "- Dispositivos conectados: 3.",
            "history": [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "¿en qué te ayudo?"}],
            "user_message": "¿mi red es segura?",
            "topic_context": None,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "Todo bien"}
    system_prompt, turns = engine.calls[0]
    assert "- Dispositivos conectados: 3." in system_prompt
    assert turns == [
        ChatTurn("user", "hola"),
        ChatTurn("assistant", "¿en qué te ayudo?"),
        ChatTurn("user", "¿mi red es segura?"),
    ]


def test_chat_engine_failures_are_a_typed_502(service_app: FastAPI, service_client: TestClient) -> None:
    service_app.dependency_overrides[get_chat_engine] = lambda: _FailingEngine()

    response = service_client.post("/v1/chat", json={"user_context": "", "user_message": "hola"})

    assert response.status_code == 502
    assert response.json()["code"] == "chat_engine_unavailable"


def test_chat_rejects_an_unknown_role(service_client: TestClient) -> None:
    response = service_client.post(
        "/v1/chat", json={"user_context": "", "history": [{"role": "system", "content": "x"}], "user_message": "hola"}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_chat_requires_the_api_key(service_app: FastAPI) -> None:
    response = TestClient(service_app).post("/v1/chat", json={"user_context": "", "user_message": "hola"})

    assert response.status_code == 401
