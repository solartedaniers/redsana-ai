from dataclasses import asdict

from fastapi import APIRouter, Depends
from redsana_ai import AnomalyDetector

from redsana_ai_service.composition import build_anomaly_detector
from redsana_ai_service.schemas import AnomalyReply, AnomalyRequest, DeviationRead
from redsana_ai_service.security import require_api_key

router = APIRouter(prefix="/v1", tags=["anomaly"], dependencies=[Depends(require_api_key)])


@router.post("/anomaly/evaluate", response_model=AnomalyReply)
def evaluate_anomaly(
    payload: AnomalyRequest, detector: AnomalyDetector = Depends(build_anomaly_detector)
) -> AnomalyReply:
    classification = detector.evaluate(payload.history, payload.latest)
    return AnomalyReply(classification=DeviationRead(**asdict(classification)) if classification else None)
