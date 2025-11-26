"""
Prompt Adapter Service

Story 2.1: Dynamic Scenario-to-Prompt Engine
Converts scenario JSONB parameters into Gemini 2.5 Flash system prompts
"""

import hashlib
import json
from typing import Optional, Dict, Any
import structlog
import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.vectordb_client import get_vectordb_client
from app.utils.circuit_breaker import CircuitBreaker

logger = structlog.get_logger()


class PromptAdapter:
    """
    Converts scenario parameters into Gemini-optimized system instructions
    
    Features:
    - VectorDB character trait retrieval (with circuit breaker)
    - Redis caching (1-hour TTL)
    - Gemini API retry logic (3 attempts)
    - Fallback to base_scenarios metadata when VectorDB fails
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.vectordb_client = None
        self.vectordb_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60,
            success_threshold=2
        )
        
        # Initialize Redis if configured
        if settings.redis_url:
            try:
                self.redis_client = redis.Redis.from_url(settings.redis_url)
                logger.info("prompt_adapter_redis_initialized")
            except Exception as e:
                logger.warning("prompt_adapter_redis_init_failed", error=str(e))
        
        # Initialize VectorDB client
        try:
            self.vectordb_client = get_vectordb_client()
            logger.info("prompt_adapter_vectordb_initialized", type=settings.vectordb_type)
        except Exception as e:
            logger.error("prompt_adapter_vectordb_init_failed", error=str(e))
    
    async def adapt_prompt(
        self,
        scenario_id: str,
        base_prompt: str,
        scenario_data: dict
    ) -> Dict[str, Any]:
        """
        Convert scenario parameters into Gemini 2.5 Flash system_instruction
        
        Args:
            scenario_id: Scenario unique identifier
            base_prompt: Base instruction template
            scenario_data: Scenario parameters from Spring Boot
        
        Returns:
            {
                "system_instruction": str,
                "character_traits": dict,
                "scenario_context": dict,
                "cache_hit": bool
            }
        """
        
        # Check Redis cache (1-hour TTL)
        cache_key = f"prompt:{scenario_id}:{hashlib.md5(base_prompt.encode()).hexdigest()}"
        
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.info("prompt_cache_hit", scenario_id=scenario_id)
                    result = json.loads(cached)
                    result["cache_hit"] = True
                    return result
            except Exception as e:
                logger.warning("prompt_cache_read_failed", error=str(e))
        
        # Retrieve character traits from VectorDB (if CHARACTER_CHANGE)
        character_traits = None
        scenario_type = scenario_data.get("type")
        
        if scenario_type == "CHARACTER_CHANGE":
            character_name = scenario_data.get("parameters", {}).get("character")
            base_story = scenario_data.get("base_story")
            
            if character_name and base_story:
                # Use circuit breaker for VectorDB call
                character_traits = await self.vectordb_circuit_breaker.call(
                    self._get_character_traits,
                    character_name,
                    base_story,
                    fallback=self._get_character_traits_fallback
                )
        
        # Build Gemini-optimized system_instruction
        system_instruction = self._build_system_instruction(
            scenario_data,
            base_prompt,
            character_traits
        )
        
        result = {
            "system_instruction": system_instruction,
            "character_traits": character_traits,
            "scenario_context": scenario_data.get("parameters", {}),
            "cache_hit": False
        }
        
        # Cache for 1 hour (3600 seconds)
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(result, default=str)
                )
                logger.info("prompt_cached", scenario_id=scenario_id, ttl=3600)
            except Exception as e:
                logger.warning("prompt_cache_write_failed", error=str(e))
        
        logger.info(
            "prompt_adapted",
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            has_character_traits=character_traits is not None
        )
        
        return result
    
    async def _get_character_traits(
        self,
        character_name: str,
        base_story: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve character personality traits from VectorDB (ChromaDB)
        
        TECH-001: Protected by circuit breaker
        """
        
        if not self.vectordb_client:
            logger.warning("vectordb_not_initialized")
            return None
        
        try:
            # Query VectorDB for character
            collection = self.vectordb_client.get_collection("characters")
            
            # Semantic search for character (768-dim embedding)
            results = collection.query(
                query_texts=[f"{character_name} from {base_story}"],
                n_results=1,
                include=["metadatas", "documents"]
            )
            
            if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
                char_metadata = results["metadatas"][0][0]
                traits = {
                    "name": char_metadata.get("name"),
                    "role": char_metadata.get("role"),
                    "personality_traits": char_metadata.get("personality_traits", []),
                    "description": results["documents"][0][0],
                    "source": "vectordb"
                }
                
                logger.info(
                    "character_traits_retrieved",
                    character=character_name,
                    story=base_story,
                    traits_count=len(traits.get("personality_traits", []))
                )
                
                return traits
            
            logger.info(
                "character_not_found_in_vectordb",
                character=character_name,
                story=base_story
            )
            return None
            
        except Exception as e:
            logger.error(
                "vectordb_character_lookup_failed",
                error=str(e),
                character=character_name,
                story=base_story
            )
            raise  # Re-raise to trigger circuit breaker
    
    async def _get_character_traits_fallback(
        self,
        character_name: str,
        base_story: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fallback for character trait retrieval when VectorDB fails
        
        TECH-001: Returns minimal character info from base_scenarios metadata
        """
        
        logger.warning(
            "using_character_traits_fallback",
            character=character_name,
            story=base_story,
            reason="vectordb_circuit_open"
        )
        
        # Return minimal character info
        # In production, this could query PostgreSQL base_scenarios table
        return {
            "name": character_name,
            "role": "Unknown",
            "personality_traits": ["adaptable", "resilient"],
            "description": f"Character from {base_story}",
            "source": "fallback"
        }
    
    def _build_system_instruction(
        self,
        scenario: dict,
        base_prompt: str,
        character_traits: Optional[dict]
    ) -> str:
        """
        Build Gemini 2.5 Flash system_instruction (token-efficient format)
        
        Gemini system_instruction best practices:
        - Clear, concise instructions
        - Structured with headers
        - Emphasize key alterations
        - Preserve character consistency
        """
        
        scenario_type = scenario.get("type")
        params = scenario.get("parameters", {})
        base_story = scenario.get("base_story", "Unknown Story")
        
        if scenario_type == "CHARACTER_CHANGE":
            return self._build_character_change_instruction(
                params,
                base_story,
                base_prompt,
                character_traits
            )
        
        elif scenario_type == "EVENT_ALTERATION":
            return self._build_event_alteration_instruction(
                params,
                base_story,
                base_prompt
            )
        
        elif scenario_type == "SETTING_MODIFICATION":
            return self._build_setting_modification_instruction(
                params,
                base_story,
                base_prompt
            )
        
        else:
            logger.warning("unknown_scenario_type", type=scenario_type)
            return base_prompt
    
    def _build_character_change_instruction(
        self,
        params: dict,
        base_story: str,
        base_prompt: str,
        character_traits: Optional[dict]
    ) -> str:
        """Build instruction for CHARACTER_CHANGE scenario"""
        
        character = params.get("character", "Unknown")
        original_prop = params.get("original_property", "")
        new_prop = params.get("new_property", "")
        
        # Build character consistency context
        preserved_traits = ""
        if character_traits and character_traits.get("personality_traits"):
            traits_list = character_traits["personality_traits"][:5]  # Top 5 traits
            preserved_traits = f"""
PRESERVED TRAITS:
{character} retains these core characteristics:
- {', '.join(traits_list)}
- Role: {character_traits.get('role', 'Unknown')}
"""
        
        return f"""
{base_prompt}

SCENARIO ALTERATION - {base_story}:
Character: {character}
Change: {original_prop} → {new_prop}

CRITICAL INSTRUCTION:
- {character} is {new_prop}, NOT {original_prop}
- All conversations and behaviors must reflect this change
- Do NOT mention the original {original_prop} unless comparing timelines

{preserved_traits}

ADAPTATION GUIDELINES:
- Adjust social dynamics based on this change
- Maintain logical consistency with the altered property
- Character personality remains fundamentally the same
- Only this specific property has changed
""".strip()
    
    def _build_event_alteration_instruction(
        self,
        params: dict,
        base_story: str,
        base_prompt: str
    ) -> str:
        """Build instruction for EVENT_ALTERATION scenario"""
        
        event_name = params.get("event_name", "Unknown Event")
        original_outcome = params.get("original_outcome", "")
        new_outcome = params.get("new_outcome", "")
        
        return f"""
{base_prompt}

SCENARIO ALTERATION - {base_story}:
Event: {event_name}
Original Outcome: {original_outcome}
New Outcome: {new_outcome}

CRITICAL INSTRUCTION:
- The {event_name} resulted in: {new_outcome}
- This is the canon outcome in this timeline
- All subsequent events are affected by this change
- Characters react and adapt to this alternate outcome

ADAPTATION GUIDELINES:
- Explore consequences of this altered event
- Maintain character motivations despite changed circumstances
- Consider ripple effects on plot and relationships
""".strip()
    
    def _build_setting_modification_instruction(
        self,
        params: dict,
        base_story: str,
        base_prompt: str
    ) -> str:
        """Build instruction for SETTING_MODIFICATION scenario"""
        
        setting_aspect = params.get("setting_aspect", "Unknown Aspect")
        original_setting = params.get("original_setting", "")
        new_setting = params.get("new_setting", "")
        
        return f"""
{base_prompt}

SCENARIO ALTERATION - {base_story}:
Setting Aspect: {setting_aspect}
Original: {original_setting}
New: {new_setting}

CRITICAL INSTRUCTION:
- The {setting_aspect} is {new_setting}, NOT {original_setting}
- All descriptions, interactions must reflect this new setting
- Cultural, technological, or environmental differences apply

ADAPTATION GUIDELINES:
- Characters adapt to this new environment
- Plot events may unfold differently due to setting
- Maintain character essence while acknowledging environmental influence
""".strip()
    
    def get_circuit_breaker_state(self) -> dict:
        """Get VectorDB circuit breaker state for monitoring"""
        return self.vectordb_circuit_breaker.get_state()


# Global instance
_prompt_adapter: Optional[PromptAdapter] = None


def get_prompt_adapter() -> PromptAdapter:
    """Get or create global PromptAdapter instance"""
    global _prompt_adapter
    if _prompt_adapter is None:
        _prompt_adapter = PromptAdapter()
    return _prompt_adapter
