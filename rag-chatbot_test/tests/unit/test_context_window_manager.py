"""
Unit Tests for ContextWindowManager

Story 2.2: Conversation Context Window Manager
Tests token counting, optimization, character reminders, and caching
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict

from app.services.context_window_manager import ContextWindowManager


class TestContextWindowManager:
    """Test suite for ContextWindowManager"""
    
    @pytest.fixture
    def manager(self):
        """Create ContextWindowManager instance with mocked dependencies"""
        with patch('app.services.context_window_manager.genai'):
            with patch('app.services.context_window_manager.redis'):
                manager = ContextWindowManager()
                manager.redis_client = AsyncMock()
                manager.model = MagicMock()
                manager.prompt_adapter = AsyncMock()
                return manager
    
    @pytest.fixture
    def sample_messages(self) -> List[Dict[str, str]]:
        """Sample conversation messages"""
        return [
            {"role": "user", "content": "Hello, I'm exploring this timeline."},
            {"role": "assistant", "content": "Welcome! I'm here to help."},
            {"role": "user", "content": "What if I investigate the library?"},
            {"role": "assistant", "content": "The library holds many secrets..."}
        ]
    
    @pytest.mark.asyncio
    async def test_count_tokens_success(self, manager):
        """Test token counting using Gemini API"""
        # Mock Gemini token counting response
        manager.model.count_tokens.return_value = MagicMock(total_tokens=1250)
        
        system_instruction = "You are a character from a novel."
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        token_count = await manager.count_tokens(system_instruction, messages)
        
        assert token_count == 1250
        manager.model.count_tokens.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_tokens_fallback_on_error(self, manager):
        """Test fallback token estimation when API fails"""
        # Mock Gemini API failure
        manager.model.count_tokens.side_effect = Exception("API error")
        
        system_instruction = "Test instruction"
        messages = [{"role": "user", "content": "Hello"}]
        
        token_count = await manager.count_tokens(system_instruction, messages)
        
        # Should return estimated count (not raise exception)
        assert token_count > 0
        assert isinstance(token_count, int)
    
    @pytest.mark.asyncio
    async def test_build_context_no_optimization_needed(self, manager, sample_messages):
        """Test context building with <10K tokens (no optimization)"""
        # Mock dependencies
        manager.redis_client.get.return_value = None  # No cache
        manager.prompt_adapter.adapt_prompt = AsyncMock(return_value={
            "system_instruction": "You are Sherlock Holmes.",
            "character_traits": {"name": "Sherlock", "traits": ["analytical", "observant"]}
        })
        manager.model.count_tokens.return_value = MagicMock(total_tokens=5000)
        
        result = await manager.build_context(
            scenario_id="scenario_123",
            conversation_id="conv_456",
            messages=sample_messages
        )
        
        assert result["token_count"] == 5000
        assert result["optimization_applied"] is False
        assert result["cache_hit"] is False
        assert len(result["messages"]) >= len(sample_messages)
        assert result["system_instruction"] == "You are Sherlock Holmes."
    
    @pytest.mark.asyncio
    async def test_build_context_with_optimization(self, manager):
        """Test context building with >10K tokens triggers optimization"""
        # Create 150 messages (exceeds RECENT_MESSAGE_COUNT of 100)
        long_messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(150)
        ]
        
        # Mock dependencies
        manager.redis_client.get.return_value = None
        manager.prompt_adapter.adapt_prompt = AsyncMock(return_value={
            "system_instruction": "System instruction",
            "character_traits": {}
        })
        
        # First count: >10K tokens (trigger optimization)
        # Second count: <10K tokens (after optimization)
        manager.model.count_tokens.side_effect = [
            MagicMock(total_tokens=15000),  # Initial count
            MagicMock(total_tokens=8000),   # After optimization
            MagicMock(total_tokens=8000)    # Final count
        ]
        
        # Mock summarization
        manager.model.generate_content_async = AsyncMock(
            return_value=MagicMock(text="Summary of previous conversation")
        )
        
        result = await manager.build_context(
            scenario_id="scenario_123",
            conversation_id="conv_456",
            messages=long_messages
        )
        
        assert result["optimization_applied"] is True
        assert result["token_count"] == 8000
        # Should have summary + recent 100 messages
        assert len(result["messages"]) <= 101  # 1 summary + 100 recent
    
    @pytest.mark.asyncio
    async def test_build_context_cache_hit(self, manager, sample_messages):
        """Test context building returns cached result"""
        import json
        
        cached_result = {
            "system_instruction": "Cached instruction",
            "messages": sample_messages,
            "token_count": 3000,
            "optimization_applied": False,
            "cache_hit": False,
            "scenario_id": "scenario_123",
            "conversation_id": "conv_456"
        }
        
        # Mock cache hit
        manager.redis_client.get.return_value = json.dumps(cached_result)
        
        result = await manager.build_context(
            scenario_id="scenario_123",
            conversation_id="conv_456",
            messages=sample_messages
        )
        
        assert result["cache_hit"] is True
        assert result["token_count"] == 3000
        # Should NOT call prompt_adapter or model (cache hit)
        manager.prompt_adapter.adapt_prompt.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_build_context_exceeds_token_limit(self, manager):
        """Test context building raises error when exceeding 1M token limit"""
        # Mock dependencies
        manager.redis_client.get.return_value = None
        manager.prompt_adapter.adapt_prompt = AsyncMock(return_value={
            "system_instruction": "System instruction",
            "character_traits": {}
        })
        
        # Mock token count exceeding limit
        manager.model.count_tokens.return_value = MagicMock(
            total_tokens=1_100_000  # Exceeds MAX_INPUT_TOKENS
        )
        
        with pytest.raises(ValueError, match="Context exceeds 1M token limit"):
            await manager.build_context(
                scenario_id="scenario_123",
                conversation_id="conv_456",
                messages=[{"role": "user", "content": "test"}]
            )
    
    @pytest.mark.asyncio
    async def test_optimize_context_keeps_recent_100(self, manager):
        """Test optimization keeps recent 100 messages"""
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(150)
        ]
        
        # Mock summarization
        manager.model.generate_content_async = AsyncMock(
            return_value=MagicMock(text="Summary")
        )
        
        optimized = await manager.optimize_context(messages, "scenario_123")
        
        # Should have 1 summary + 100 recent messages
        assert len(optimized) == 101
        assert optimized[0]["role"] == "system"
        assert "Summary" in optimized[0]["content"]
        # Verify last message is preserved
        assert optimized[-1]["content"] == "Message 149"
    
    @pytest.mark.asyncio
    async def test_optimize_context_no_optimization_for_short_history(self, manager):
        """Test optimization skipped for messages < RECENT_MESSAGE_COUNT"""
        messages = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(50)  # Less than RECENT_MESSAGE_COUNT (100)
        ]
        
        optimized = await manager.optimize_context(messages, "scenario_123")
        
        # Should return original messages unchanged
        assert optimized == messages
        # Summarization should NOT be called
        manager.model.generate_content_async.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_summarize_messages_success(self, manager):
        """Test message summarization using Gemini"""
        messages = [
            {"role": "user", "content": "What if I explore the cave?"},
            {"role": "assistant", "content": "The cave is dark and mysterious."},
            {"role": "user", "content": "I light a torch."}
        ]
        
        # Mock Gemini response
        manager.model.generate_content_async = AsyncMock(
            return_value=MagicMock(text="User explored a dark cave with a torch.")
        )
        
        summary = await manager.summarize_messages(messages)
        
        assert "User explored a dark cave" in summary
        manager.model.generate_content_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_summarize_messages_fallback_on_error(self, manager):
        """Test summarization fallback when Gemini fails"""
        messages = [{"role": "user", "content": "test"}]
        
        # Mock Gemini failure
        manager.model.generate_content_async = AsyncMock(
            side_effect=Exception("API error")
        )
        
        summary = await manager.summarize_messages(messages)
        
        # Should return fallback summary (not raise exception)
        assert "Previous conversation contained" in summary
        assert isinstance(summary, str)
    
    def test_inject_character_reminders(self, manager):
        """Test character reminder injection every 50 messages"""
        # Create 120 messages
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(120)
        ]
        
        character_traits = {
            "name": "Sherlock Holmes",
            "traits": ["analytical", "observant", "eccentric"]
        }
        
        result = manager.inject_character_reminders(
            messages,
            "scenario_123",
            character_traits
        )
        
        # Should have reminders at positions 50 and 100
        # Total: 120 original + 2 reminders = 122 messages
        assert len(result) > len(messages)
        
        # Find reminder messages
        reminders = [msg for msg in result if msg["role"] == "system" and "Character reminder" in msg["content"]]
        assert len(reminders) == 2
        assert "Sherlock Holmes" in reminders[0]["content"]
    
    def test_inject_character_reminders_no_traits(self, manager):
        """Test no reminders injected when character_traits is None"""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(60)]
        
        result = manager.inject_character_reminders(messages, "scenario_123", None)
        
        # Should return original messages unchanged
        assert result == messages
    
    def test_inject_character_reminders_short_conversation(self, manager):
        """Test no reminders for conversations < CHARACTER_REMINDER_INTERVAL"""
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(30)]
        character_traits = {"name": "Test", "traits": ["test"]}
        
        result = manager.inject_character_reminders(
            messages,
            "scenario_123",
            character_traits
        )
        
        # No reminders for conversations < 50 messages
        assert result == messages
    
    @pytest.mark.asyncio
    async def test_get_metrics_placeholder(self, manager):
        """Test metrics endpoint returns placeholder data"""
        metrics = await manager.get_metrics()
        
        assert "average_token_usage" in metrics
        assert "optimization_rate" in metrics
        assert "cache_hit_rate" in metrics
        assert "total_contexts_built" in metrics
