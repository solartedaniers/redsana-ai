from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from redsana_ai import BriefingLanguage, ChatRole, DeviatingMetric, NetworkMetricVector


class HealthRead(BaseModel):
    status: Literal["ok"] = "ok"
    ready: bool


class ErrorRead(BaseModel):
    """Cuerpo de todo error del servicio: code es estable, message es solo para humanos y logs."""

    code: str
    message: str


class ChatTurnPayload(BaseModel):
    role: ChatRole
    content: str


class ChatRequest(BaseModel):
    """Lo mismo que recibe SecurityChat.ask: los datos reales ya armados por el backend, nunca su base de datos."""

    user_context: str
    history: list[ChatTurnPayload] = Field(default_factory=list)
    user_message: str
    topic_context: str | None = None


class ChatReply(BaseModel):
    reply: str


class BriefingRequest(BaseModel):
    """user_context ya trae la evaluación más reciente; guardar el resumen es trabajo del backend."""

    user_context: str
    language: BriefingLanguage


class BriefingReply(BaseModel):
    text: str


class AnomalyRequest(BaseModel):
    """Cada vector es (latency_ms, jitter_ms, packet_loss_percent); history nunca incluye a latest."""

    history: list[NetworkMetricVector] = Field(min_length=1)
    latest: NetworkMetricVector


class DeviationRead(BaseModel):
    deviating_metric: DeviatingMetric
    severity: Literal["warning", "critical"]
    current: float
    typical: float


class AnomalyReply(BaseModel):
    # None cuando latest es normal, igual que AnomalyDetector.evaluate.
    classification: DeviationRead | None


class OutageSamplePayload(BaseModel):
    recorded_at: datetime
    packet_loss_percent: float


class OutageRequest(BaseModel):
    # De más nueva a más vieja, como OutageDetector.detect.
    window: list[OutageSamplePayload]


class OutageEpisodeRead(BaseModel):
    started_at: datetime
    recovered_at: datetime
    duration_minutes: int
    severity: Literal["warning", "critical"]


class OutageReply(BaseModel):
    # None cuando no hay una recuperación que reportar, igual que OutageDetector.detect.
    episode: OutageEpisodeRead | None
