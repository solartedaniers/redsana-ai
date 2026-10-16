from dataclasses import asdict

from fastapi import APIRouter, Depends
from redsana_ai import OutageDetector

from redsana_ai_service.composition import build_outage_detector
from redsana_ai_service.schemas import OutageEpisodeRead, OutageReply, OutageRequest
from redsana_ai_service.security import require_api_key

router = APIRouter(prefix="/v1", tags=["outage"], dependencies=[Depends(require_api_key)])


@router.post("/outage/detect", response_model=OutageReply)
def detect_outage(payload: OutageRequest, detector: OutageDetector = Depends(build_outage_detector)) -> OutageReply:
    episode = detector.detect([(sample.recorded_at, sample.packet_loss_percent) for sample in payload.window])
    return OutageReply(episode=OutageEpisodeRead(**asdict(episode)) if episode else None)
