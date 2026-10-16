from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from redsana_ai.chat.groq_client import DEFAULT_GROQ_CHAT_COMPLETIONS_URL


class ServiceSettings(BaseSettings):
    """Configuración del servicio, cargada desde las variables de entorno (.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Vacía a propósito: sin clave el servicio rechaza toda petición protegida en vez de quedar abierto.
    ai_service_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_api_url: str = DEFAULT_GROQ_CHAT_COMPLETIONS_URL
    groq_timeout_seconds: int = 30
    # Baja a propósito: con temperatura alta el asistente cambiaba dígitos al copiar DNS (llegó a escribir 0.0.0.3).
    groq_temperature: float = 0.2
    # Apagada por defecto: la documentación interactiva describe la API a cualquiera que la abra.
    enable_api_docs: bool = False


@lru_cache
def get_settings() -> ServiceSettings:
    # La cacheo porque ServiceSettings() vuelve a leer y parsear el .env cada vez.
    return ServiceSettings()
