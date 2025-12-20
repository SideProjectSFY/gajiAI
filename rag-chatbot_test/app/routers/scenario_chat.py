from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict
from uuid import UUID
import structlog

from app.services.scenario_chat_service import ScenarioChatService
from app.middleware.jwt_auth import jwt_auth, get_jwt_token
from app.dto.response import success_response
from app.exceptions import GajiException, ErrorCode

logger = structlog.get_logger()

router = APIRouter(prefix="/api/ai/chat", tags=["ai-chat"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[UUID] = None
    conversation_partner_type: Optional[str] = "stranger"
    other_main_character: Optional[Dict] = None

@router.post("/scenarios/{scenario_id}")
async def chat_with_scenario(
    scenario_id: UUID,
    request: ChatRequest,
    req: Request,
    user: dict = Depends(jwt_auth)
):
    """
    시나리오 기반 AI 대화 (PostgreSQL 저장)
    
    Vue.js Frontend에서 사용하는 엔드포인트
    """
    try:
        jwt_token = get_jwt_token(req)
        user_id = user.get("sub")
        
        if not user_id:
            raise GajiException(ErrorCode.UNAUTHORIZED, "User ID not found in token")
        
        chat_service = ScenarioChatService()
        result = await chat_service.first_conversation(
            scenario_id=str(scenario_id),
            initial_message=request.message,
            output_language="ko",
            is_creator=True,
            conversation_id=str(request.conversation_id) if request.conversation_id else None,
            conversation_partner_type=request.conversation_partner_type or "stranger",
            other_main_character=request.other_main_character,
            jwt_token=jwt_token,
            user_id=user_id
        )
        
        return success_response(
            data=result,
            message="Chat response generated successfully"
        )
        
    except GajiException:
        raise
    except ValueError as e:
        logger.error("chat_validation_error", error=str(e), scenario_id=str(scenario_id))
        raise GajiException(
            ErrorCode.MESSAGE_GENERATION_FAILED,
            details={"error": str(e)}
        )
    except Exception as e:
        logger.error("chat_failed", error=str(e), exc_info=True, scenario_id=str(scenario_id))
        raise GajiException(
            ErrorCode.MESSAGE_GENERATION_FAILED,
            details={"error": str(e)}
        )

