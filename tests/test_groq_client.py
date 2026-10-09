"""Sin red: urlopen falso para comprobar que todo lo que usa el cliente entra por el constructor."""
import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from redsana_ai import ChatTurn, GroqClient, GroqClientError


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        self.close()


def _client() -> GroqClient:
    return GroqClient(
        api_key="test-key", model="test-model", timeout_seconds=7, temperature=0.3,
        api_url="https://llm.example/v1/chat", user_agent="test-agent",
    )


def test_request_uses_every_constructor_parameter() -> None:
    payload = {"choices": [{"message": {"content": "hola"}}]}
    with patch("urllib.request.urlopen", return_value=_Response(json.dumps(payload).encode())) as urlopen:
        reply = _client().complete("reglas", [ChatTurn("user", "pregunta")])

    request = urlopen.call_args.args[0]
    assert reply == "hola"
    assert request.full_url == "https://llm.example/v1/chat"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert request.get_header("User-agent") == "test-agent"
    assert urlopen.call_args.kwargs["timeout"] == 7
    assert json.loads(request.data) == {
        "model": "test-model",
        "temperature": 0.3,
        "messages": [{"role": "system", "content": "reglas"}, {"role": "user", "content": "pregunta"}],
    }


def test_network_failure_becomes_a_groq_client_error() -> None:
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sin red")):
        with pytest.raises(GroqClientError):
            _client().complete("reglas", [ChatTurn("user", "pregunta")])


def test_unexpected_payload_becomes_a_groq_client_error() -> None:
    with patch("urllib.request.urlopen", return_value=_Response(b'{"choices": []}')):
        with pytest.raises(GroqClientError):
            _client().complete("reglas", [ChatTurn("user", "pregunta")])
