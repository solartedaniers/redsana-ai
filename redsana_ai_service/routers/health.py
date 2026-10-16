from fastapi import APIRouter, Depends, Request

from redsana_ai_service.readiness import ServiceReadiness
from redsana_ai_service.schemas import HealthRead

router = APIRouter(tags=["health"])


def get_readiness(request: Request) -> ServiceReadiness:
    return request.app.state.readiness


# Sin clave a propósito: lo consultan el health check de Render y el backend para saber si ya despertó.
@router.get("/health", response_model=HealthRead)
def health(readiness: ServiceReadiness = Depends(get_readiness)) -> HealthRead:
    return HealthRead(ready=readiness.is_ready)
