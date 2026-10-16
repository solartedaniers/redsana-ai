from typing import Literal

from pydantic import BaseModel, Field
from redsana_ai import ChatRole


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
