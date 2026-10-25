"""Único lugar donde el servicio construye las piezas de redsana_ai; cambiar una implementación es tocar solo aquí."""

from datetime import timedelta

from fastapi import Depends
from redsana_ai import (
    AnomalyDetector,
    ChatEngine,
    EngineSecurityBriefing,
    EngineSecurityChat,
    GroqClient,
    IsolationForestAnomalyDetector,
    OutageDetector,
    SecurityBriefing,
    SecurityChat,
    StreakOutageDetector,
)

from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.dependencies import get_service_settings


def get_chat_engine(settings: ServiceSettings = Depends(get_service_settings)) -> ChatEngine:
    # Va como dependencia aparte para poder reemplazarla en las pruebas sin llamar a la API real de Groq.
    return GroqClient(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        timeout_seconds=settings.groq_timeout_seconds,
        temperature=settings.groq_temperature,
        api_url=settings.groq_api_url,
    )


def build_security_chat(engine: ChatEngine) -> SecurityChat:
    return EngineSecurityChat(engine)


def build_security_briefing(engine: ChatEngine) -> SecurityBriefing:
    return EngineSecurityBriefing(engine)


def build_anomaly_detector(settings: ServiceSettings = Depends(get_service_settings)) -> AnomalyDetector:
    # Con los valores por defecto da lo mismo que el modo local del backend.
    return IsolationForestAnomalyDetector(
        contamination=settings.anomaly_contamination,
        random_state=settings.anomaly_random_state,
        critical_z_score=settings.anomaly_critical_z_score,
    )


def build_outage_detector(settings: ServiceSettings = Depends(get_service_settings)) -> OutageDetector:
    return StreakOutageDetector(
        packet_loss_threshold_percent=settings.outage_packet_loss_threshold_percent,
        max_gap_between_samples=timedelta(minutes=settings.outage_max_gap_minutes),
        critical_duration_minutes=settings.outage_critical_duration_minutes,
    )
