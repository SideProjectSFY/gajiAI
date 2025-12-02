"""
AI Generation Router

Gemini 2.5 Flash를 사용한 대화 생성 및 Long Polling 지원
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import structlog
import google.generativeai as genai

from app.config import settings
from app.utils.redis_client import RedisClient

logger = structlog.get_logger()
router = APIRouter(prefix="/api/ai", tags=["AI Generation"])

# Initialize Gemini
genai.configure(api_key=settings.gemini_api_key)

# Initialize Redis client
redis_client = RedisClient()


class MessageHistory(BaseModel):
    """대화 히스토리 항목"""
    role: str = Field(..., description="user 또는 assistant")
    content: str = Field(..., description="메시지 내용")


class GenerationRequest(BaseModel):
    """AI 생성 요청"""
    conversation_id: str = Field(..., description="대화 ID")
    scenario_context: str = Field(..., description="시나리오 컨텍스트 (시스템 프롬프트)")
    user_message: str = Field(..., description="사용자 메시지")
    history: List[MessageHistory] = Field(default_factory=list, description="대화 히스토리")


class GenerationResponse(BaseModel):
    """AI 생성 응답"""
    conversation_id: str
    status: str = Field(..., description="queued, processing, completed, failed")
    message: str


async def generate_ai_response(
    conversation_id: str,
    scenario_context: str,
    user_message: str,
    history: List[MessageHistory]
):
    """
    Background task for Gemini AI generation
    
    Args:
        conversation_id: 대화 ID
        scenario_context: 시나리오 컨텍스트 (시스템 프롬프트)
        user_message: 사용자 메시지
        history: 대화 히스토리
    """
    try:
        # Update status to processing
        await redis_client.set_task_status(conversation_id, "processing", ttl=600)
        
        logger.info(
            "ai_generation_started",
            conversation_id=conversation_id,
            history_length=len(history)
        )
        
        # Prepare chat history for Gemini
        chat_history = []
        for msg in history:
            chat_history.append({
                "role": msg.role,
                "parts": [msg.content]
            })
        
        # Add current user message
        chat_history.append({
            "role": "user",
            "parts": [user_message]
        })
        
        # Configure Gemini model
        generation_config = genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1000,
        )
        
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=generation_config,
            system_instruction=scenario_context
        )
        
        # Start chat with history
        chat = model.start_chat(history=chat_history[:-1])  # Exclude last user message
        
        # Generate response
        response = chat.send_message(user_message)
        
        generated_text = response.text
        
        logger.info(
            "ai_generation_completed",
            conversation_id=conversation_id,
            response_length=len(generated_text)
        )
        
        # Store completed result
        await redis_client.set_task_status(conversation_id, "completed", ttl=600)
        await redis_client.set_task_content(conversation_id, generated_text, ttl=600)
        
    except Exception as e:
        logger.error(
            "ai_generation_failed",
            conversation_id=conversation_id,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Store error
        await redis_client.set_task_status(conversation_id, "failed", ttl=600)
        await redis_client.set_task_error(conversation_id, str(e), ttl=600)


@router.post("/generate", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_response(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    AI 응답 생성 (비동기)
    
    즉시 202 Accepted 반환하고 백그라운드에서 생성 처리
    """
    logger.info(
        "generation_request_received",
        conversation_id=request.conversation_id,
        user_message_length=len(request.user_message)
    )
    
    # Set initial status
    await redis_client.set_task_status(request.conversation_id, "queued", ttl=600)
    
    # Add background task
    background_tasks.add_task(
        generate_ai_response,
        conversation_id=request.conversation_id,
        scenario_context=request.scenario_context,
        user_message=request.user_message,
        history=request.history
    )
    
    return GenerationResponse(
        conversation_id=request.conversation_id,
        status="queued",
        message="AI generation started. Use polling endpoint to check status."
    )
