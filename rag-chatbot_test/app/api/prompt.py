"""
Prompt Adaptation API Router

Story 2.1: /api/ai/adapt-prompt endpoint
SEC-001: Protected by rate limiting (100 req/min)
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import structlog

from app.services.prompt_adapter import get_prompt_adapter

logger = structlog.get_logger()

router = APIRouter(prefix="/api/ai", tags=["AI Prompt Adaptation"])


class AdaptPromptRequest(BaseModel):
    """Request model for prompt adaptation"""
    scenario_id: str = Field(..., description="Scenario unique identifier")
    base_prompt: str = Field(..., description="Base instruction template")
    scenario_data: Dict[str, Any] = Field(..., description="Scenario parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "550e8400-e29b-41d4-a716-446655440000",
                "base_prompt": "You are a helpful assistant guiding users through alternate timeline scenarios.",
                "scenario_data": {
                    "type": "CHARACTER_CHANGE",
                    "base_story": "Harry Potter",
                    "parameters": {
                        "character": "Hermione Granger",
                        "original_property": "Gryffindor student",
                        "new_property": "Slytherin student"
                    }
                }
            }
        }


class AdaptPromptResponse(BaseModel):
    """Response model for prompt adaptation"""
    system_instruction: str = Field(..., description="Gemini-optimized system instruction")
    character_traits: Optional[Dict[str, Any]] = Field(None, description="Character traits from VectorDB")
    scenario_context: Dict[str, Any] = Field(..., description="Scenario parameters")
    cache_hit: bool = Field(False, description="Whether result was from cache")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_instruction": "You are a helpful assistant...\n\nSCENARIO ALTERATION - Harry Potter:\nCharacter: Hermione Granger\nChange: Gryffindor student → Slytherin student...",
                "character_traits": {
                    "name": "Hermione Granger",
                    "role": "Student",
                    "personality_traits": ["intelligent", "ambitious", "determined"],
                    "source": "vectordb"
                },
                "scenario_context": {
                    "character": "Hermione Granger",
                    "original_property": "Gryffindor student",
                    "new_property": "Slytherin student"
                },
                "cache_hit": False
            }
        }


class CircuitBreakerStatusResponse(BaseModel):
    """Response model for circuit breaker status"""
    state: str = Field(..., description="Circuit breaker state: closed, open, half_open")
    failure_count: int = Field(..., description="Current failure count")
    success_count: int = Field(..., description="Success count in half_open state")
    last_failure_time: Optional[str] = Field(None, description="Last failure timestamp")
    time_in_current_state: float = Field(..., description="Seconds in current state")


@router.post("/adapt-prompt", response_model=AdaptPromptResponse)
async def adapt_prompt(request: AdaptPromptRequest):
    """
    Convert scenario parameters into Gemini 2.5 Flash system_instruction
    
    SEC-001: Rate limited to 100 requests/minute per user
    TECH-001: Uses circuit breaker for VectorDB with fallback
    
    Performance:
    - Cached: <50ms
    - Uncached with VectorDB: <500ms
    - Fallback (VectorDB down): <100ms
    """
    
    try:
        prompt_adapter = get_prompt_adapter()
        
        result = await prompt_adapter.adapt_prompt(
            scenario_id=request.scenario_id,
            base_prompt=request.base_prompt,
            scenario_data=request.scenario_data
        )
        
        logger.info(
            "prompt_adapted_successfully",
            scenario_id=request.scenario_id,
            cache_hit=result.get("cache_hit", False),
            has_character_traits=result.get("character_traits") is not None
        )
        
        return AdaptPromptResponse(**result)
        
    except Exception as e:
        logger.error(
            "prompt_adaptation_failed",
            scenario_id=request.scenario_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adapt prompt: {str(e)}"
        )


@router.get("/circuit-breaker/status", response_model=CircuitBreakerStatusResponse)
async def get_circuit_breaker_status():
    """
    Get VectorDB circuit breaker status
    
    Useful for monitoring and debugging TECH-001 implementation
    """
    
    try:
        prompt_adapter = get_prompt_adapter()
        state = prompt_adapter.get_circuit_breaker_state()
        
        return CircuitBreakerStatusResponse(**state)
        
    except Exception as e:
        logger.error("circuit_breaker_status_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker status: {str(e)}"
        )
