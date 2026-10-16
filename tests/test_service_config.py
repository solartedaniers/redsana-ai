"""La configuración del servicio sale del entorno y, sin clave, queda cerrada."""
import pytest

from redsana_ai_service.config import ServiceSettings


def test_settings_are_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_SERVICE_API_KEY", "shared-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("GROQ_MODEL", "some-model")
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("GROQ_TEMPERATURE", "0.5")
    monkeypatch.setenv("ENABLE_API_DOCS", "true")

    settings = ServiceSettings(_env_file=None)

    assert settings.ai_service_api_key == "shared-key"
    assert settings.groq_api_key == "groq-key"
    assert settings.groq_model == "some-model"
    assert settings.groq_timeout_seconds == 12
    assert settings.groq_temperature == 0.5
    assert settings.enable_api_docs is True


def test_defaults_keep_the_service_closed_and_the_docs_off(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("AI_SERVICE_API_KEY", "GROQ_API_KEY", "ENABLE_API_DOCS"):
        monkeypatch.delenv(name, raising=False)

    settings = ServiceSettings(_env_file=None)

    assert settings.ai_service_api_key == ""
    assert settings.enable_api_docs is False
