"""
Unit Tests for Prompt Adapter Service

Story 2.1: Dynamic Scenario-to-Prompt Engine Tests
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.prompt_adapter import PromptAdapter


@pytest.fixture
def prompt_adapter():
    """Create PromptAdapter instance for testing"""
    with patch('app.services.prompt_adapter.get_vectordb_client'):
        adapter = PromptAdapter()
        adapter.redis_client = AsyncMock()
        return adapter


class TestPromptAdapter:
    """Test PromptAdapter service"""
    
    @pytest.mark.asyncio
    async def test_character_change_instruction_building(self, prompt_adapter):
        """Test CHARACTER_CHANGE instruction generation"""
        
        scenario_data = {
            "type": "CHARACTER_CHANGE",
            "base_story": "Harry Potter",
            "parameters": {
                "character": "Hermione Granger",
                "original_property": "Gryffindor student",
                "new_property": "Slytherin student"
            }
        }
        
        base_prompt = "You are a helpful AI assistant."
        
        instruction = prompt_adapter._build_system_instruction(
            scenario_data,
            base_prompt,
            character_traits=None
        )
        
        assert "Hermione Granger" in instruction
        assert "Slytherin student" in instruction
        assert "NOT Gryffindor student" in instruction
        assert base_prompt in instruction
    
    @pytest.mark.asyncio
    async def test_character_traits_included_when_available(self, prompt_adapter):
        """Test that character traits are included in instruction"""
        
        scenario_data = {
            "type": "CHARACTER_CHANGE",
            "base_story": "Harry Potter",
            "parameters": {
                "character": "Hermione Granger",
                "original_property": "Gryffindor",
                "new_property": "Slytherin"
            }
        }
        
        character_traits = {
            "name": "Hermione Granger",
            "role": "Student",
            "personality_traits": ["intelligent", "ambitious", "brave"]
        }
        
        instruction = prompt_adapter._build_system_instruction(
            scenario_data,
            "Base prompt",
            character_traits
        )
        
        assert "intelligent" in instruction
        assert "ambitious" in instruction
        assert "PRESERVED TRAITS" in instruction
    
    @pytest.mark.asyncio
    async def test_event_alteration_instruction_building(self, prompt_adapter):
        """Test EVENT_ALTERATION instruction generation"""
        
        scenario_data = {
            "type": "EVENT_ALTERATION",
            "base_story": "Harry Potter",
            "parameters": {
                "event_name": "Battle of Hogwarts",
                "original_outcome": "Voldemort defeated",
                "new_outcome": "Voldemort victorious"
            }
        }
        
        instruction = prompt_adapter._build_system_instruction(
            scenario_data,
            "Base prompt",
            None
        )
        
        assert "Battle of Hogwarts" in instruction
        assert "Voldemort victorious" in instruction
        assert "CRITICAL INSTRUCTION" in instruction
    
    @pytest.mark.asyncio
    async def test_setting_modification_instruction_building(self, prompt_adapter):
        """Test SETTING_MODIFICATION instruction generation"""
        
        scenario_data = {
            "type": "SETTING_MODIFICATION",
            "base_story": "Harry Potter",
            "parameters": {
                "setting_aspect": "time period",
                "original_setting": "1990s",
                "new_setting": "2020s"
            }
        }
        
        instruction = prompt_adapter._build_system_instruction(
            scenario_data,
            "Base prompt",
            None
        )
        
        assert "time period" in instruction
        assert "2020s" in instruction
        assert "NOT 1990s" in instruction
    
    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self, prompt_adapter):
        """Test that cached results are returned"""
        
        # Mock Redis cache hit
        cached_data = {
            "system_instruction": "Cached instruction",
            "character_traits": {"name": "Test"},
            "scenario_context": {},
            "cache_hit": False
        }
        prompt_adapter.redis_client.get.return_value = __import__('json').dumps(cached_data).encode()
        
        result = await prompt_adapter.adapt_prompt(
            scenario_id="test-123",
            base_prompt="Test prompt",
            scenario_data={"type": "CHARACTER_CHANGE", "parameters": {}}
        )
        
        assert result["cache_hit"] is True
        assert result["system_instruction"] == "Cached instruction"
    
    @pytest.mark.asyncio
    async def test_cache_miss_generates_new_instruction(self, prompt_adapter):
        """Test that cache miss generates new instruction"""
        
        # Mock Redis cache miss
        prompt_adapter.redis_client.get.return_value = None
        
        scenario_data = {
            "type": "CHARACTER_CHANGE",
            "base_story": "Test Story",
            "parameters": {
                "character": "Test Character",
                "original_property": "Original",
                "new_property": "New"
            }
        }
        
        # Mock circuit breaker to return None (no character traits)
        prompt_adapter.vectordb_circuit_breaker.call = AsyncMock(return_value=None)
        
        result = await prompt_adapter.adapt_prompt(
            scenario_id="test-123",
            base_prompt="Test prompt",
            scenario_data=scenario_data
        )
        
        assert result["cache_hit"] is False
        assert "Test Character" in result["system_instruction"]
        assert result["character_traits"] is None
    
    @pytest.mark.asyncio
    async def test_fallback_used_when_vectordb_fails(self, prompt_adapter):
        """Test that fallback is used when VectorDB circuit is open"""
        
        scenario_data = {
            "type": "CHARACTER_CHANGE",
            "base_story": "Test Story",
            "parameters": {
                "character": "Test Character",
                "original_property": "Original",
                "new_property": "New"
            }
        }
        
        # Mock Redis cache miss
        prompt_adapter.redis_client.get.return_value = None
        
        # Mock circuit breaker to use fallback
        fallback_traits = {
            "name": "Test Character",
            "source": "fallback",
            "personality_traits": ["adaptable"]
        }
        prompt_adapter.vectordb_circuit_breaker.call = AsyncMock(return_value=fallback_traits)
        
        result = await prompt_adapter.adapt_prompt(
            scenario_id="test-123",
            base_prompt="Test prompt",
            scenario_data=scenario_data
        )
        
        assert result["character_traits"]["source"] == "fallback"
    
    @pytest.mark.asyncio
    async def test_unknown_scenario_type_uses_base_prompt(self, prompt_adapter):
        """Test that unknown scenario types fall back to base prompt"""
        
        scenario_data = {
            "type": "UNKNOWN_TYPE",
            "base_story": "Test Story",
            "parameters": {}
        }
        
        instruction = prompt_adapter._build_system_instruction(
            scenario_data,
            "Base prompt only",
            None
        )
        
        assert instruction == "Base prompt only"
    
    def test_get_circuit_breaker_state(self, prompt_adapter):
        """Test getting circuit breaker state"""
        
        state = prompt_adapter.get_circuit_breaker_state()
        
        assert "state" in state
        assert "failure_count" in state
        assert "success_count" in state
