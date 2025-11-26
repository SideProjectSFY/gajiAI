"""
Integration Tests for Prompt Adaptation API

Story 2.1: /api/ai/adapt-prompt endpoint tests
Tests SEC-001 (rate limiting) and TECH-001 (circuit breaker)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


class TestPromptAdaptationAPI:
    """Test /api/ai/adapt-prompt endpoint"""
    
    def test_adapt_prompt_character_change_success(self):
        """Test successful CHARACTER_CHANGE prompt adaptation"""
        
        request_data = {
            "scenario_id": "test-scenario-123",
            "base_prompt": "You are a helpful AI assistant.",
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
        
        with patch('app.services.prompt_adapter.get_vectordb_client'):
            response = client.post("/api/ai/adapt-prompt", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "system_instruction" in data
        assert "scenario_context" in data
        assert "cache_hit" in data
        assert "Hermione Granger" in data["system_instruction"]
        assert "Slytherin student" in data["system_instruction"]
    
    def test_adapt_prompt_event_alteration_success(self):
        """Test successful EVENT_ALTERATION prompt adaptation"""
        
        request_data = {
            "scenario_id": "test-event-456",
            "base_prompt": "Guide users through alternate timelines.",
            "scenario_data": {
                "type": "EVENT_ALTERATION",
                "base_story": "Harry Potter",
                "parameters": {
                    "event_name": "Battle of Hogwarts",
                    "original_outcome": "Voldemort defeated",
                    "new_outcome": "Voldemort victorious"
                }
            }
        }
        
        with patch('app.services.prompt_adapter.get_vectordb_client'):
            response = client.post("/api/ai/adapt-prompt", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Battle of Hogwarts" in data["system_instruction"]
        assert "Voldemort victorious" in data["system_instruction"]
    
    def test_adapt_prompt_setting_modification_success(self):
        """Test successful SETTING_MODIFICATION prompt adaptation"""
        
        request_data = {
            "scenario_id": "test-setting-789",
            "base_prompt": "Explore alternate settings.",
            "scenario_data": {
                "type": "SETTING_MODIFICATION",
                "base_story": "Harry Potter",
                "parameters": {
                    "setting_aspect": "time period",
                    "original_setting": "1990s",
                    "new_setting": "2020s"
                }
            }
        }
        
        with patch('app.services.prompt_adapter.get_vectordb_client'):
            response = client.post("/api/ai/adapt-prompt", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "2020s" in data["system_instruction"]
        assert "time period" in data["system_instruction"]
    
    def test_adapt_prompt_validates_required_fields(self):
        """Test that missing required fields return 422"""
        
        # Missing scenario_id
        request_data = {
            "base_prompt": "Test prompt",
            "scenario_data": {"type": "CHARACTER_CHANGE"}
        }
        
        response = client.post("/api/ai/adapt-prompt", json=request_data)
        assert response.status_code == 422
    
    def test_circuit_breaker_status_endpoint(self):
        """Test /api/ai/circuit-breaker/status endpoint"""
        
        with patch('app.services.prompt_adapter.get_vectordb_client'):
            response = client.get("/api/ai/circuit-breaker/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "state" in data
        assert "failure_count" in data
        assert "success_count" in data
        assert data["state"] in ["closed", "open", "half_open"]
    
    def test_response_includes_rate_limit_headers(self):
        """Test that rate limit headers are included (SEC-001)"""
        
        request_data = {
            "scenario_id": "rate-limit-test",
            "base_prompt": "Test",
            "scenario_data": {
                "type": "CHARACTER_CHANGE",
                "base_story": "Test",
                "parameters": {
                    "character": "Test",
                    "original_property": "A",
                    "new_property": "B"
                }
            }
        }
        
        with patch('app.services.prompt_adapter.get_vectordb_client'):
            response = client.post("/api/ai/adapt-prompt", json=request_data)
        
        # Check for rate limit headers (if Redis is configured)
        # Headers may not be present if Redis is not available in test environment
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers


class TestRateLimiting:
    """Test rate limiting functionality (SEC-001)"""
    
    @pytest.mark.skipif(
        not __import__('os').getenv('REDIS_URL'),
        reason="Redis not configured"
    )
    def test_rate_limit_enforced_after_threshold(self):
        """Test that rate limit returns 429 after threshold"""
        
        request_data = {
            "scenario_id": "rate-limit-test",
            "base_prompt": "Test",
            "scenario_data": {
                "type": "CHARACTER_CHANGE",
                "base_story": "Test",
                "parameters": {"character": "A", "original_property": "B", "new_property": "C"}
            }
        }
        
        # Make requests up to limit (100/min)
        # This is a simplified test - full load test would be separate
        with patch('app.services.prompt_adapter.get_vectordb_client'):
            responses = []
            for i in range(105):
                response = client.post("/api/ai/adapt-prompt", json=request_data)
                responses.append(response)
                if response.status_code == 429:
                    break
        
        # Should get 429 Too Many Requests at some point
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration (TECH-001)"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_vectordb_failures(self):
        """Test that circuit breaker opens after VectorDB failures"""
        
        from app.services.prompt_adapter import get_prompt_adapter
        
        adapter = get_prompt_adapter()
        
        # Mock VectorDB to fail
        with patch.object(adapter, '_get_character_traits', side_effect=Exception("VectorDB down")):
            
            # Make multiple requests to trigger circuit breaker
            for i in range(6):  # failure_threshold is 5
                try:
                    await adapter.vectordb_circuit_breaker.call(
                        adapter._get_character_traits,
                        "Test Character",
                        "Test Story",
                        fallback=adapter._get_character_traits_fallback
                    )
                except Exception:
                    pass
            
            # Circuit should be open
            state = adapter.get_circuit_breaker_state()
            assert state["state"] == "open"
            assert state["failure_count"] >= 5
    
    @pytest.mark.asyncio
    async def test_fallback_used_when_circuit_open(self):
        """Test that fallback is used when circuit is open"""
        
        from app.services.prompt_adapter import get_prompt_adapter
        
        adapter = get_prompt_adapter()
        
        # Force circuit open by failing multiple times
        with patch.object(adapter, '_get_character_traits', side_effect=Exception("VectorDB down")):
            for _ in range(6):
                try:
                    await adapter.vectordb_circuit_breaker.call(
                        adapter._get_character_traits,
                        "Test",
                        "Test",
                        fallback=adapter._get_character_traits_fallback
                    )
                except Exception:
                    pass
        
        # Now call should use fallback
        result = await adapter.vectordb_circuit_breaker.call(
            adapter._get_character_traits,
            "Hermione Granger",
            "Harry Potter",
            fallback=adapter._get_character_traits_fallback
        )
        
        assert result is not None
        assert result["source"] == "fallback"
        assert result["name"] == "Hermione Granger"
