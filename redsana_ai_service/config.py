from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from redsana_ai.anomaly.isolation_forest import (
    ISOLATION_FOREST_CONTAMINATION,
    ISOLATION_FOREST_RANDOM_STATE,
    SEVERITY_CRITICAL_Z_SCORE,
)
from redsana_ai.chat.groq_client import DEFAULT_GROQ_CHAT_COMPLETIONS_URL
from redsana_ai.outage.detector import (
    MAX_GAP_BETWEEN_SAMPLES,
    OUTAGE_CRITICAL_DURATION_MINUTES,
    OUTAGE_PACKET_LOSS_THRESHOLD_PERCENT,
)


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
    # Parámetros de los detectores; por defecto los del paquete. Mismos nombres que en el backend: si cambias uno,
    # ponlo igual allá para que el servicio y el respaldo local del backend den lo mismo.
    anomaly_critical_z_score: float = SEVERITY_CRITICAL_Z_SCORE
    anomaly_contamination: float = ISOLATION_FOREST_CONTAMINATION
    anomaly_random_state: int = ISOLATION_FOREST_RANDOM_STATE
    outage_packet_loss_threshold_percent: float = OUTAGE_PACKET_LOSS_THRESHOLD_PERCENT
    outage_max_gap_minutes: float = MAX_GAP_BETWEEN_SAMPLES.total_seconds() / 60
    outage_critical_duration_minutes: int = OUTAGE_CRITICAL_DURATION_MINUTES

    @model_validator(mode="after")
    def _require_valid_detector_settings(self) -> "ServiceSettings":
        # Rango que acepta IsolationForest de scikit-learn.
        if not 0 < self.anomaly_contamination <= 0.5:
            raise ValueError("ANOMALY_CONTAMINATION must be > 0 and <= 0.5")
        if self.anomaly_critical_z_score <= 0:
            raise ValueError("ANOMALY_CRITICAL_Z_SCORE must be > 0")
        if not 0 < self.outage_packet_loss_threshold_percent <= 100:
            raise ValueError("OUTAGE_PACKET_LOSS_THRESHOLD_PERCENT must be > 0 and <= 100")
        if self.outage_max_gap_minutes <= 0 or self.outage_critical_duration_minutes < 1:
            raise ValueError("OUTAGE_MAX_GAP_MINUTES must be > 0 and OUTAGE_CRITICAL_DURATION_MINUTES >= 1")
        return self


@lru_cache
def get_settings() -> ServiceSettings:
    # La cacheo porque ServiceSettings() vuelve a leer y parsear el .env cada vez.
    return ServiceSettings()
