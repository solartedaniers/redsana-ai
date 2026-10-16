from fastapi import APIRouter, Depends
from redsana_ai import ChatEngine, ChatTurn

from redsana_ai_service.composition import build_security_chat, get_chat_engine
from redsana_ai_service.schemas import ChatReply, ChatRequest
from redsana_ai_service.security import require_api_key

router = APIRouter(prefix="/v1", tags=["chat"], dependencies=[Depends(require_api_key)])


@router.post("/chat", response_model=ChatReply)
def chat(payload: ChatRequest, engine: ChatEngine = Depends(get_chat_engine)) -> ChatReply:
    history = [ChatTurn(turn.role, turn.content) for turn in payload.history]
    reply = build_security_chat(engine).ask(payload.user_context, history, payload.user_message, payload.topic_context)
    return ChatReply(reply=reply)
