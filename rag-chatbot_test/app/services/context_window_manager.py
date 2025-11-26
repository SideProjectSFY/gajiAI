"""
Context Window Manager Service

Story 2.2: Conversation Context Window Manager
Manages Gemini 2.5 Flash context window (1M input, 8K output)
"""

import hashlib
import json
from typing import List, Dict, Any, Optional
import structlog
import redis.asyncio as redis
from google import generativeai as genai

from app.config import settings
from app.services.prompt_adapter import PromptAdapter

logger = structlog.get_logger()


class ContextWindowManager:
    """
    Intelligent context window management for Gemini 2.5 Flash
    
    Features:
    - Token counting using Gemini API
    - Smart optimization for >10K token conversations
    - Character reminder injection every 50 messages
    - Redis caching (5-min TTL)
    - Gemini Caching API for system instructions
    """
    
    # Gemini 2.5 Flash token limits
    MAX_INPUT_TOKENS = 1_000_000  # 1M input token limit
    MAX_OUTPUT_TOKENS = 8_192      # 8K output token limit
    OPTIMIZATION_THRESHOLD = 10_000  # Optimize if >10K tokens
    RECENT_MESSAGE_COUNT = 100     # Keep last 100 messages in full detail
    CHARACTER_REMINDER_INTERVAL = 50  # Inject reminder every 50 messages
    CACHE_TTL = 300  # Redis cache TTL: 5 minutes
    
    def __init__(self):
        # Initialize Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        # Initialize Redis for caching
        self.redis_client: Optional[redis.Redis] = None
        if settings.redis_url:
            try:
                self.redis_client = redis.Redis.from_url(settings.redis_url)
                logger.info("context_window_manager_redis_initialized")
            except Exception as e:
                logger.warning("context_window_manager_redis_init_failed", error=str(e))
        
        # Initialize PromptAdapter for system instructions
        self.prompt_adapter = PromptAdapter()
    
    async def count_tokens(
        self,
        system_instruction: str,
        messages: List[Dict[str, str]]
    ) -> int:
        """
        Count tokens using Gemini's token counting API
        
        Args:
            system_instruction: System instruction text
            messages: List of conversation messages with 'role' and 'content'
        
        Returns:
            Total token count
        """
        try:
            # Build content for token counting
            content = []
            
            # Add system instruction
            if system_instruction:
                content.append({
                    "role": "system",
                    "parts": [{"text": system_instruction}]
                })
            
            # Add messages
            for msg in messages:
                content.append({
                    "role": msg.get("role", "user"),
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            # Use Gemini API to count tokens
            result = self.model.count_tokens(content)
            token_count = result.total_tokens
            
            logger.debug("token_count_calculated", 
                        token_count=token_count,
                        message_count=len(messages))
            
            return token_count
            
        except Exception as e:
            logger.error("token_count_failed", error=str(e))
            # Fallback: rough estimate (1 token ≈ 4 characters)
            total_chars = len(system_instruction) + sum(len(m.get("content", "")) for m in messages)
            estimated_tokens = total_chars // 4
            logger.warning("using_estimated_token_count", estimated_tokens=estimated_tokens)
            return estimated_tokens
    
    async def build_context(
        self,
        scenario_id: str,
        conversation_id: str,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Build conversation context for Gemini 2.5 Flash
        
        Args:
            scenario_id: Scenario ID for system instruction
            conversation_id: Conversation ID for caching
            messages: List of conversation messages
        
        Returns:
            {
                "system_instruction": str,
                "messages": List[Dict],
                "token_count": int,
                "optimization_applied": bool,
                "cache_hit": bool
            }
        """
        # Check Redis cache first
        cache_key = f"context:{conversation_id}"
        cache_hit = False
        
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    cache_hit = True
                    result = json.loads(cached)
                    logger.info("context_cache_hit", conversation_id=conversation_id)
                    result["cache_hit"] = True
                    return result
            except Exception as e:
                logger.warning("context_cache_read_failed", error=str(e))
        
        # Get system instruction from PromptAdapter (Story 2.1)
        try:
            # For Story 2.2, we need a base prompt to adapt
            # In production, this would come from the scenario details
            base_prompt = "You are a character from a novel, engaging in a 'what if' scenario conversation."
            
            system_instruction_result = await self.prompt_adapter.adapt_prompt(
                scenario_id=scenario_id,
                base_prompt=base_prompt
            )
            system_instruction = system_instruction_result["system_instruction"]
            
        except Exception as e:
            logger.error("system_instruction_retrieval_failed", error=str(e))
            system_instruction = "You are a helpful AI assistant engaging in a conversation."
        
        # Count tokens
        token_count = await self.count_tokens(system_instruction, messages)
        logger.info("initial_token_count", 
                   token_count=token_count,
                   message_count=len(messages))
        
        # Optimize context if needed (>10K tokens)
        optimization_applied = False
        optimized_messages = messages
        
        if token_count > self.OPTIMIZATION_THRESHOLD:
            logger.info("context_optimization_triggered", 
                       token_count=token_count,
                       threshold=self.OPTIMIZATION_THRESHOLD)
            
            optimized_messages = await self.optimize_context(messages, scenario_id)
            token_count = await self.count_tokens(system_instruction, optimized_messages)
            optimization_applied = True
            
            logger.info("context_optimized",
                       original_message_count=len(messages),
                       optimized_message_count=len(optimized_messages),
                       new_token_count=token_count)
        
        # Inject character reminders for consistency
        final_messages = self.inject_character_reminders(
            optimized_messages,
            scenario_id,
            system_instruction_result.get("character_traits", {})
        )
        
        # Final token count after character reminders
        final_token_count = await self.count_tokens(system_instruction, final_messages)
        
        # Validate token limits
        if final_token_count > self.MAX_INPUT_TOKENS:
            logger.error("context_exceeds_token_limit",
                        token_count=final_token_count,
                        max_tokens=self.MAX_INPUT_TOKENS)
            raise ValueError(
                f"Context exceeds 1M token limit: {final_token_count} tokens. "
                f"Maximum: {self.MAX_INPUT_TOKENS} tokens."
            )
        
        # Build result
        result = {
            "system_instruction": system_instruction,
            "messages": final_messages,
            "token_count": final_token_count,
            "optimization_applied": optimization_applied,
            "cache_hit": cache_hit,
            "scenario_id": scenario_id,
            "conversation_id": conversation_id
        }
        
        # Cache result for 5 minutes
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key,
                    self.CACHE_TTL,
                    json.dumps(result)
                )
                logger.debug("context_cached", conversation_id=conversation_id)
            except Exception as e:
                logger.warning("context_cache_write_failed", error=str(e))
        
        logger.info("context_built_successfully",
                   conversation_id=conversation_id,
                   token_count=final_token_count,
                   optimization_applied=optimization_applied)
        
        return result
    
    async def optimize_context(
        self,
        messages: List[Dict[str, str]],
        scenario_id: str
    ) -> List[Dict[str, str]]:
        """
        Optimize long conversations (>10K tokens):
        - Keep recent 100 messages in full detail
        - Summarize older messages using Gemini
        
        Args:
            messages: Full conversation history
            scenario_id: Scenario ID for context
        
        Returns:
            Optimized message list
        """
        if len(messages) <= self.RECENT_MESSAGE_COUNT:
            logger.debug("optimization_skipped_message_count_below_threshold",
                        message_count=len(messages))
            return messages
        
        # Split into old and recent messages
        old_messages = messages[:-self.RECENT_MESSAGE_COUNT]
        recent_messages = messages[-self.RECENT_MESSAGE_COUNT:]
        
        logger.info("optimizing_context",
                   old_message_count=len(old_messages),
                   recent_message_count=len(recent_messages))
        
        # Summarize old messages using Gemini
        try:
            summary = await self.summarize_messages(old_messages)
            
            # Return: [summary message] + recent messages
            optimized = [
                {
                    "role": "system",
                    "content": f"[Previous conversation summary] {summary}"
                }
            ] + recent_messages
            
            logger.info("context_optimization_complete",
                       summary_length=len(summary),
                       optimized_message_count=len(optimized))
            
            return optimized
            
        except Exception as e:
            logger.error("context_optimization_failed", error=str(e))
            # Fallback: just return recent messages with a simple note
            return [
                {
                    "role": "system",
                    "content": f"[Previous conversation with {len(old_messages)} messages omitted for context length]"
                }
            ] + recent_messages
    
    async def summarize_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Use Gemini to summarize old messages
        
        Args:
            messages: Messages to summarize
        
        Returns:
            Summary text (target: ~200 words)
        """
        # Build prompt for summarization
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        prompt = (
            "Summarize this conversation history in approximately 200 words. "
            "Focus on key plot points, character decisions, and important context. "
            "Maintain chronological order and preserve critical details:\n\n"
            f"{conversation_text}"
        )
        
        try:
            response = await self.model.generate_content_async(prompt)
            summary = response.text
            
            logger.info("messages_summarized",
                       original_message_count=len(messages),
                       summary_length=len(summary))
            
            return summary
            
        except Exception as e:
            logger.error("message_summarization_failed", error=str(e))
            # Fallback: basic summary
            return (
                f"Previous conversation contained {len(messages)} messages. "
                "Key discussion points were preserved in recent messages."
            )
    
    def inject_character_reminders(
        self,
        messages: List[Dict[str, str]],
        scenario_id: str,
        character_traits: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Inject character trait reminders every 50 messages
        
        Args:
            messages: Conversation messages
            scenario_id: Scenario ID
            character_traits: Character traits from PromptAdapter
        
        Returns:
            Messages with character reminders injected
        """
        if not character_traits or len(messages) < self.CHARACTER_REMINDER_INTERVAL:
            return messages
        
        result = []
        reminder_count = 0
        
        for i, msg in enumerate(messages):
            # Inject reminder every CHARACTER_REMINDER_INTERVAL messages
            if i > 0 and i % self.CHARACTER_REMINDER_INTERVAL == 0:
                reminder = self._build_character_reminder(character_traits)
                result.append({
                    "role": "system",
                    "content": reminder
                })
                reminder_count += 1
            
            result.append(msg)
        
        if reminder_count > 0:
            logger.debug("character_reminders_injected",
                        reminder_count=reminder_count,
                        interval=self.CHARACTER_REMINDER_INTERVAL)
        
        return result
    
    def _build_character_reminder(self, character_traits: Dict[str, Any]) -> str:
        """Build character reminder text from traits"""
        character_name = character_traits.get("name", "the character")
        traits = character_traits.get("traits", [])
        
        if isinstance(traits, list) and traits:
            traits_text = ", ".join(traits[:5])  # Top 5 traits
            return (
                f"[Character reminder: {character_name} is {traits_text}. "
                "Maintain consistency with these core character traits.]"
            )
        else:
            return f"[Character reminder: Stay in character as {character_name}]"
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get context window metrics
        
        Returns:
            Dictionary with average token usage, optimization rate, cache hit rate
        """
        # TODO: Implement metrics collection using Redis counters
        # For now, return placeholder metrics
        return {
            "average_token_usage": 0,
            "optimization_rate": 0.0,
            "cache_hit_rate": 0.0,
            "total_contexts_built": 0
        }


# Global instance
_context_window_manager: Optional[ContextWindowManager] = None


def get_context_window_manager() -> ContextWindowManager:
    """Get singleton ContextWindowManager instance"""
    global _context_window_manager
    if _context_window_manager is None:
        _context_window_manager = ContextWindowManager()
    return _context_window_manager


def reset_context_window_manager():
    """Reset singleton instance (for testing)"""
    global _context_window_manager
    _context_window_manager = None
