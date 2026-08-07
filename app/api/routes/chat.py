import logging

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini import GeminiService

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def create_chat_reply(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    try:
        reply = GeminiService(settings).generate_reply(request)
    except Exception:
        logger.exception("Gemini response generation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="땅콩이가 잠시 말을 고르는 중이에요. 잠시 후 다시 시도해 주세요.",
        ) from None

    return ChatResponse(reply=reply, model=settings.gemini_model)
