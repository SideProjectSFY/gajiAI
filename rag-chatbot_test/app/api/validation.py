"""
Scenario validation API using Gemini 2.5 Flash
Provides AI-powered validation for "What If" scenarios
"""

from fastapi import APIRouter, HTTPException, Depends
import google.generativeai as genai
import redis.asyncio as redis
import hashlib
import json
import os
import logging
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis cache client (5-minute TTL)
redis_client: Optional[redis.Redis] = None


async def get_redis():
    """Get Redis client (lazy initialization)"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
    return redis_client


# Gemini 2.5 Flash configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set - AI validation will fail")
else:
    genai.configure(api_key=GEMINI_API_KEY)


class ValidationRequest(BaseModel):
    """Request model for scenario validation"""
    book_title: str
    scenario_title: str
    filled_types: Dict[str, str]  # Keys: character_changes, event_alterations, setting_modifications


class ValidationResponse(BaseModel):
    """Response model for validation results"""
    is_valid: bool
    errors: List[str] = []
    plausible_in_universe: bool = True
    logically_consistent: bool = True
    creativity_score: float = 0.5
    reasoning: str = ""


@router.post("/api/validate-scenario", response_model=ValidationResponse)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4)  # 1s, 2s, 4s
)
async def validate_scenario(
    request: ValidationRequest,
    redis_conn: redis.Redis = Depends(get_redis)
):
    """
    AI-powered scenario validation using Gemini 2.5 Flash
    
    Token budget: 2,000 tokens (1,500 input + 500 output)
    Cost: ~$0.00015 per validation
    Cache: 5-minute TTL in Redis
    """
    logger.info(f"Validating scenario for book: {request.book_title}")
    
    # Generate cache key
    cache_key = _generate_cache_key(
        request.book_title,
        request.scenario_title,
        request.filled_types
    )
    
    # Check Redis cache (5-minute TTL)
    try:
        cached = await redis_conn.get(cache_key)
        if cached:
            logger.info(f"Cache hit for validation: {cache_key}")
            return ValidationResponse(**json.loads(cached))
    except Exception as e:
        logger.warning(f"Redis cache read error: {e}")
    
    # Build validation prompt for Gemini
    prompt = _build_validation_prompt(
        request.book_title,
        request.scenario_title,
        request.filled_types
    )
    
    try:
        # Call Gemini 2.5 Flash API
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = await model.generate_content_async(
            prompt,
            generation_config={
                'temperature': 0.2,  # Low temperature for consistent validation
                'max_output_tokens': 500,
                'top_p': 0.95
            }
        )
        
        # Parse Gemini response
        result = _parse_validation_response(response.text)
        
        # Cache result in Redis (5-minute TTL = 300 seconds)
        try:
            await redis_conn.setex(
                cache_key,
                300,
                json.dumps(result.dict())
            )
        except Exception as e:
            logger.warning(f"Redis cache write error: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini API validation error: {e}")
        # Graceful degradation - return valid with note
        return ValidationResponse(
            is_valid=True,
            errors=[],
            creativity_score=0.5,
            reasoning="AI validation temporarily unavailable, using fallback approval"
        )


def _generate_cache_key(book_title: str, scenario_title: str, filled_types: Dict[str, str]) -> str:
    """Generate Redis cache key from scenario content"""
    content = f"{book_title}:{scenario_title}:{json.dumps(filled_types, sort_keys=True)}"
    hash_value = hashlib.md5(content.encode()).hexdigest()
    return f"validation:{hash_value}"


def _build_validation_prompt(
    book_title: str,
    scenario_title: str,
    filled_types: Dict[str, str]
) -> str:
    """Build Gemini validation prompt for unified modal (optimized for 1,500 input tokens)"""
    
    filled_content = []
    
    if 'character_changes' in filled_types:
        filled_content.append(f"Character Changes:\n{filled_types['character_changes']}")
    
    if 'event_alterations' in filled_types:
        filled_content.append(f"Event Alterations:\n{filled_types['event_alterations']}")
    
    if 'setting_modifications' in filled_types:
        filled_content.append(f"Setting Modifications:\n{filled_types['setting_modifications']}")
    
    filled_text = "\n\n".join(filled_content)
    
    return f"""
Validate this "What If" scenario for {book_title}:

Scenario Title: {scenario_title}

{filled_text}

Validation Tasks:
1. Are the described changes plausible within the {book_title} universe? (Yes/No)
2. If characters are mentioned, do they exist in {book_title}? (Yes/No)
3. If events are mentioned, do they exist in {book_title}? (Yes/No)
4. Are the proposed changes logically consistent with the story world? (Yes/No)
5. Creativity score (0.0-1.0): How interesting/novel is this scenario?

Respond in JSON:
{{
  "is_valid": true/false,
  "errors": ["error message if invalid"],
  "plausible_in_universe": true/false,
  "logically_consistent": true/false,
  "creativity_score": 0.0-1.0,
  "reasoning": "Brief explanation"
}}
"""


def _parse_validation_response(response_text: str) -> ValidationResponse:
    """Parse Gemini JSON response"""
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        data = json.loads(response_text.strip())
        
        return ValidationResponse(
            is_valid=data.get("is_valid", True),
            errors=data.get("errors", []),
            plausible_in_universe=data.get("plausible_in_universe", True),
            logically_consistent=data.get("logically_consistent", True),
            creativity_score=data.get("creativity_score", 0.5),
            reasoning=data.get("reasoning", "")
        )
    except Exception as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        logger.error(f"Response text: {response_text}")
        # Fallback to valid (graceful degradation)
        return ValidationResponse(
            is_valid=True,
            errors=[],
            creativity_score=0.5,
            reasoning="AI parsing failed, using fallback approval"
        )

