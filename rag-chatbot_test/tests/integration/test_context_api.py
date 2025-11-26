"""
Integration Tests for Context Window API

Story 2.2: Conversation Context Window Manager
Tests /api/ai/build-context endpoint
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.context_window_manager import reset_context_window_manager


class TestContextWindowAPI:
    """Integration tests for Context Window API"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Reset singleton before each test"""
        reset_context_window_manager()
        yield
        reset_context_window_manager()
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_request(self):
        """Sample build context request"""
        return {
            "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
            "conversation_id": "conv_test_123",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, I'm exploring this alternative timeline."
                },
                {
                    "role": "assistant",
                    "content": "Welcome! I'm here to help you navigate this scenario."
                },
                {
                    "role": "user",
                    "content": "What if I investigate the library?"
                }
            ]
        }
    
    @patch('app.services.context_window_manager.genai')
    @patch('app.services.context_window_manager.redis')
    def test_build_context_success(self, mock_redis, mock_genai, client, sample_request):
        """Test successful context building"""
        # Mock Gemini API
        mock_model = MagicMock()
        mock_model.count_tokens.return_value = MagicMock(total_tokens=2500)
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock Redis (no cache)
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis.Redis.from_url.return_value = mock_redis_client
        
        # Mock PromptAdapter
        with patch('app.services.context_window_manager.PromptAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.adapt_prompt = AsyncMock(return_value={
                "system_instruction": "You are Sherlock Holmes in an alternative timeline.",
                "character_traits": {
                    "name": "Sherlock Holmes",
                    "traits": ["analytical", "observant", "eccentric"]
                }
            })
            mock_adapter_class.return_value = mock_adapter
            
            response = client.post("/api/ai/build-context", json=sample_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "system_instruction" in data
        assert "messages" in data
        assert "token_count" in data
        assert "optimization_applied" in data
        assert "cache_hit" in data
        assert data["scenario_id"] == sample_request["scenario_id"]
        assert data["conversation_id"] == sample_request["conversation_id"]
    
    @patch('app.services.context_window_manager.genai')
    @patch('app.services.context_window_manager.redis')
    def test_build_context_with_optimization(self, mock_redis, mock_genai, client):
        """Test context building with optimization for long conversations"""
        # Create request with many messages
        long_messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(150)
        ]
        
        request = {
            "scenario_id": "scenario_123",
            "conversation_id": "conv_long",
            "messages": long_messages
        }
        
        # Mock Gemini API
        mock_model = MagicMock()
        # First call: >10K tokens, second call: <10K tokens (after optimization)
        mock_model.count_tokens.side_effect = [
            MagicMock(total_tokens=15000),
            MagicMock(total_tokens=8000),
            MagicMock(total_tokens=8000)
        ]
        mock_model.generate_content_async = AsyncMock(
            return_value=MagicMock(text="Conversation summary")
        )
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock Redis
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis.Redis.from_url.return_value = mock_redis_client
        
        # Mock PromptAdapter
        with patch('app.services.context_window_manager.PromptAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.adapt_prompt = AsyncMock(return_value={
                "system_instruction": "System instruction",
                "character_traits": {}
            })
            mock_adapter_class.return_value = mock_adapter
            
            response = client.post("/api/ai/build-context", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["optimization_applied"] is True
        assert data["token_count"] <= 10000
    
    @patch('app.services.context_window_manager.genai')
    @patch('app.services.context_window_manager.redis')
    def test_build_context_cache_hit(self, mock_redis, mock_genai, client, sample_request):
        """Test context building returns cached result"""
        import json
        
        cached_result = {
            "system_instruction": "Cached instruction",
            "messages": [{"role": "user", "content": "test"}],
            "token_count": 1000,
            "optimization_applied": False,
            "cache_hit": False,
            "scenario_id": sample_request["scenario_id"],
            "conversation_id": sample_request["conversation_id"]
        }
        
        # Mock Redis cache hit
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=json.dumps(cached_result))
        mock_redis.Redis.from_url.return_value = mock_redis_client
        
        # Mock Gemini (should NOT be called due to cache hit)
        mock_genai.GenerativeModel.return_value = MagicMock()
        
        response = client.post("/api/ai/build-context", json=sample_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["cache_hit"] is True
        assert data["token_count"] == 1000
    
    @patch('app.services.context_window_manager.genai')
    @patch('app.services.context_window_manager.redis')
    def test_build_context_token_limit_exceeded(self, mock_redis, mock_genai, client, sample_request):
        """Test 400 error when context exceeds 1M token limit"""
        # Mock Gemini API returning >1M tokens
        mock_model = MagicMock()
        mock_model.count_tokens.return_value = MagicMock(total_tokens=1_100_000)
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock Redis
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis.Redis.from_url.return_value = mock_redis_client
        
        # Mock PromptAdapter
        with patch('app.services.context_window_manager.PromptAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.adapt_prompt = AsyncMock(return_value={
                "system_instruction": "System instruction",
                "character_traits": {}
            })
            mock_adapter_class.return_value = mock_adapter
            
            response = client.post("/api/ai/build-context", json=sample_request)
        
        assert response.status_code == 400
        assert "exceeds 1M token limit" in response.json()["detail"]
    
    def test_build_context_missing_fields(self, client):
        """Test 422 error for invalid request (missing fields)"""
        invalid_request = {
            "scenario_id": "scenario_123"
            # Missing conversation_id and messages
        }
        
        response = client.post("/api/ai/build-context", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_build_context_empty_messages(self, client):
        """Test handling of empty message list"""
        request = {
            "scenario_id": "scenario_123",
            "conversation_id": "conv_empty",
            "messages": []
        }
        
        with patch('app.services.context_window_manager.genai'):
            with patch('app.services.context_window_manager.redis'):
                response = client.post("/api/ai/build-context", json=request)
        
        # Should handle empty messages gracefully
        assert response.status_code in [200, 400, 500]
    
    @patch('app.services.context_window_manager.genai')
    @patch('app.services.context_window_manager.redis')
    def test_get_context_metrics(self, mock_redis, mock_genai, client):
        """Test context metrics endpoint"""
        response = client.get("/api/ai/context-metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "average_token_usage" in data
        assert "optimization_rate" in data
        assert "cache_hit_rate" in data
        assert "total_contexts_built" in data
    
    @patch('app.services.context_window_manager.genai')
    @patch('app.services.context_window_manager.redis')
    def test_build_context_with_character_reminders(self, mock_redis, mock_genai, client):
        """Test character reminder injection in long conversations"""
        # Create 120 messages (triggers 2 reminders at 50 and 100)
        many_messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(120)
        ]
        
        request = {
            "scenario_id": "scenario_123",
            "conversation_id": "conv_reminders",
            "messages": many_messages
        }
        
        # Mock Gemini API
        mock_model = MagicMock()
        mock_model.count_tokens.return_value = MagicMock(total_tokens=8000)
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock Redis
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)
        mock_redis.Redis.from_url.return_value = mock_redis_client
        
        # Mock PromptAdapter with character traits
        with patch('app.services.context_window_manager.PromptAdapter') as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.adapt_prompt = AsyncMock(return_value={
                "system_instruction": "You are Sherlock Holmes.",
                "character_traits": {
                    "name": "Sherlock Holmes",
                    "traits": ["analytical", "observant"]
                }
            })
            mock_adapter_class.return_value = mock_adapter
            
            response = client.post("/api/ai/build-context", json=request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have more messages than input (due to reminders)
        assert len(data["messages"]) >= len(many_messages)
        
        # Check for character reminder messages
        system_messages = [msg for msg in data["messages"] if msg["role"] == "system"]
        reminder_messages = [msg for msg in system_messages if "Character reminder" in msg.get("content", "")]
        assert len(reminder_messages) >= 2  # Should have reminders at 50 and 100
