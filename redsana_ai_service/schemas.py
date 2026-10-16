from typing import Literal

from pydantic import BaseModel


class HealthRead(BaseModel):
    status: Literal["ok"] = "ok"
    ready: bool


class ErrorRead(BaseModel):
    """Cuerpo de todo error del servicio: code es estable, message es solo para humanos y logs."""

    code: str
    message: str
