"""
Context Window API Router

Story 2.2: Conversation Context Window Manager
Endpoint: POST /api/ai/build-context
"""

from typing import List, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import structlog

from app.services.context_window_manager import get_context_window_manager

logger = structlog.get_logger()

router = APIRouter(prefix="/api/ai", tags=["AI Context Management"])


class Message(BaseModel):
    """Single conversation message"""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What would happen if I chose to trust the stranger?"
            }
        }


class BuildContextRequest(BaseModel):
    """Request to build conversation context"""
    scenario_id: str = Field(..., description="Scenario ID for system instruction")
    conversation_id: str = Field(..., description="Conversation ID for caching")
    messages: List[Message] = Field(..., description="Conversation message history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
                "conversation_id": "conv_123456789",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, I'm exploring this alternative timeline."
                    },
                    {
                        "role": "assistant",
                        "content": "Welcome! I'm here to help you navigate this scenario."
                    }
                ]
            }
        }


class BuildContextResponse(BaseModel):
    """Response with built context"""
    system_instruction: str = Field(..., description="System instruction for Gemini")
    messages: List[Dict[str, str]] = Field(..., description="Optimized message list")
    token_count: int = Field(..., description="Total token count")
    optimization_applied: bool = Field(..., description="Whether context was optimized")
    cache_hit: bool = Field(..., description="Whether result came from cache")
    scenario_id: str = Field(..., description="Scenario ID")
    conversation_id: str = Field(..., description="Conversation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_instruction": "You are Sherlock Holmes in an alternative timeline where...",
                "messages": [
                    {"role": "user", "content": "What if I investigate the library?"}
                ],
                "token_count": 1250,
                "optimization_applied": False,
                "cache_hit": False,
                "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
                "conversation_id": "conv_123456789"
            }
        }


class ContextMetricsResponse(BaseModel):
    """Context window metrics"""
    average_token_usage: float = Field(..., description="Average tokens per context")
    optimization_rate: float = Field(..., description="% of contexts optimized")
    cache_hit_rate: float = Field(..., description="% of cache hits")
    total_contexts_built: int = Field(..., description="Total contexts built")


@router.post(
    "/build-context",
    response_model=BuildContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Build conversation context for Gemini",
    description=(
        "Build optimized conversation context for Gemini 2.5 Flash. "
        "Includes system instruction, message history, and token counting. "
        "Automatically optimizes long conversations (>10K tokens) by summarizing old messages. "
        "Results are cached for 5 minutes."
    )
)
async def build_context(request: BuildContextRequest):
    """
    Build conversation context for Gemini 2.5 Flash
    
    **Features**:
    - Token counting using Gemini API
    - Smart optimization for conversations >10K tokens
    - Character reminder injection every 50 messages
    - Redis caching (5-min TTL)
    - Token limit validation (1M input max)
    
    **Optimization Strategy**:
    - Conversations <10K tokens: Full history included
    - Conversations >10K tokens: Summarize old messages, keep recent 100 in full
    
    **Returns**:
    - system_instruction: Scenario-adapted prompt from Story 2.1
    - messages: Optimized message list with character reminders
    - token_count: Total tokens (system instruction + messages)
    - optimization_applied: Whether context was optimized
    - cache_hit: Whether result came from Redis cache
    """
    try:
        # Get ContextWindowManager instance
        manager = get_context_window_manager()
        
        # Convert Pydantic messages to dicts
        messages_dict = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Build context
        result = await manager.build_context(
            scenario_id=request.scenario_id,
            conversation_id=request.conversation_id,
            messages=messages_dict
        )
        
        logger.info("context_built_via_api",
                   conversation_id=request.conversation_id,
                   token_count=result["token_count"],
                   optimization_applied=result["optimization_applied"],
                   cache_hit=result["cache_hit"])
        
        return BuildContextResponse(**result)
        
    except ValueError as e:
        # Token limit exceeded or validation error
        logger.error("context_build_validation_failed",
                    error=str(e),
                    conversation_id=request.conversation_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected error
        logger.error("context_build_failed",
                    error=str(e),
                    conversation_id=request.conversation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build context: {str(e)}"
        )


@router.get(
    "/context-metrics",
    response_model=ContextMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get context window metrics",
    description=(
        "Retrieve metrics about context window usage: "
        "average token count, optimization rate, cache hit rate"
    )
)
async def get_context_metrics():
    """
    Get context window usage metrics
    
    **Metrics**:
    - average_token_usage: Average tokens per context built
    - optimization_rate: Percentage of contexts that required optimization
    - cache_hit_rate: Percentage of requests served from cache
    - total_contexts_built: Total number of contexts built
    
    **Note**: Metrics are aggregated across all conversations
    """
    try:
        manager = get_context_window_manager()
        metrics = await manager.get_metrics()
        
        logger.info("context_metrics_retrieved", **metrics)
        
        return ContextMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error("context_metrics_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )
