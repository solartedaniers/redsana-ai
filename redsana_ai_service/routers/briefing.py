from fastapi import APIRouter, Depends
from redsana_ai import ChatEngine

from redsana_ai_service.composition import build_security_briefing, get_chat_engine
from redsana_ai_service.schemas import BriefingReply, BriefingRequest
from redsana_ai_service.security import require_api_key

router = APIRouter(prefix="/v1", tags=["briefing"], dependencies=[Depends(require_api_key)])


@router.post("/briefing", response_model=BriefingReply)
def briefing(payload: BriefingRequest, engine: ChatEngine = Depends(get_chat_engine)) -> BriefingReply:
    return BriefingReply(text=build_security_briefing(engine).write(payload.user_context, payload.language))
