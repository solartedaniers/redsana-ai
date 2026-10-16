import logging
from enum import StrEnum

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redsana_ai import ChatEngineError
from starlette.exceptions import HTTPException as StarletteHTTPException

from redsana_ai_service.schemas import ErrorRead

logger = logging.getLogger(__name__)


class ServiceErrorCode(StrEnum):
    """Códigos estables que el backend distingue sin depender del texto del mensaje."""

    INVALID_API_KEY = "invalid_api_key"
    SERVICE_MISCONFIGURED = "service_misconfigured"
    VALIDATION_ERROR = "validation_error"
    CHAT_ENGINE_UNAVAILABLE = "chat_engine_unavailable"
    HTTP_ERROR = "http_error"
    INTERNAL_ERROR = "internal_error"


class ServiceError(Exception):
    def __init__(self, status_code: int, code: ServiceErrorCode, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _error_response(status_code: int, code: ServiceErrorCode, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorRead(code=code, message=message).model_dump(mode="json"))


async def _service_error(_: Request, error: ServiceError) -> JSONResponse:
    return _error_response(error.status_code, error.code, error.message)


async def _validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    fields = sorted({".".join(str(part) for part in issue["loc"]) for issue in error.errors()})
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, ServiceErrorCode.VALIDATION_ERROR, f"invalid fields: {', '.join(fields)}"
    )


async def _chat_engine_error(_: Request, error: ChatEngineError) -> JSONResponse:
    # El detalle real de Groq queda en el log: devolverlo expondría datos internos del proveedor.
    logger.warning("chat engine failed: %s", error)
    return _error_response(
        status.HTTP_502_BAD_GATEWAY, ServiceErrorCode.CHAT_ENGINE_UNAVAILABLE, "chat engine unavailable"
    )


async def _http_error(_: Request, error: StarletteHTTPException) -> JSONResponse:
    return _error_response(error.status_code, ServiceErrorCode.HTTP_ERROR, str(error.detail))


async def _unexpected_error(_: Request, error: Exception) -> JSONResponse:
    logger.exception("unexpected AI service error", exc_info=error)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, ServiceErrorCode.INTERNAL_ERROR, "internal error"
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, _service_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(ChatEngineError, _chat_engine_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected_error)
