import hmac

from fastapi import Depends, Header, status

from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.dependencies import get_service_settings
from redsana_ai_service.errors import ServiceError, ServiceErrorCode

# Nombre del encabezado acordado con el backend; el valor de la clave sí vive solo en el entorno.
API_KEY_HEADER = "X-AI-Service-Key"


def require_api_key(
    api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
    settings: ServiceSettings = Depends(get_service_settings),
) -> None:
    expected = settings.ai_service_api_key
    if not expected:
        # Sin clave configurada no atiendo a nadie: un servicio abierto gastaría la cuota de Groq de cualquiera.
        raise ServiceError(
            status.HTTP_503_SERVICE_UNAVAILABLE, ServiceErrorCode.SERVICE_MISCONFIGURED, "API key not configured"
        )
    # compare_digest tarda lo mismo acierte o no, para no filtrar la clave por tiempos de respuesta.
    if api_key is None or not hmac.compare_digest(api_key.encode("utf-8"), expected.encode("utf-8")):
        raise ServiceError(status.HTTP_401_UNAUTHORIZED, ServiceErrorCode.INVALID_API_KEY, "missing or invalid API key")
