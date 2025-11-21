"""
Test Conversation Endpoints (Epic 4, Story 4.2)

FastAPI conversation message generation endpoints 테스트
- POST /api/ai/conversations/{id}/messages (standard response)
- POST /api/ai/conversations/{id}/messages/stream (SSE streaming)
- POST /api/ai/conversations/{id}/messages/no-rag (without RAG)
- GET /api/ai/search/passages (passage search)

NOTE: RAG Service mocking은 conftest.py의 client fixture에서 
dependency override로 처리됨
"""

import pytest
from uuid import uuid4


class TestConversationMessageEndpoints:
    """Conversation message generation endpoint tests"""
    
    def test_send_message_success(self, client, mock_rag_service):
        """
        Given: Valid user message and conversation context
        When: POST /api/ai/conversations/{id}/messages is called
        Then: Returns AI-generated message with relevant passages
        """
        conversation_id = uuid4()
        request_data = {
            "content": "How did being in Slytherin change your approach to studying?",
            "scenario_id": str(uuid4()),
            "scenario_context": "Hermione Granger was sorted into Slytherin",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        # Configure mock for this specific test
        mock_rag_service.generate_hybrid_response.return_value = (
            "In Slytherin, I learned strategic thinking...",
            {"rag_used": True, "question_type": "character_change"}
        )
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message_id" in data
        assert "content" in data
        assert "metadata" in data
        assert data["content"] == "In Slytherin, I learned strategic thinking..."
        assert data["metadata"]["rag_used"] is True
        
        # Verify RAG service called with correct params
        mock_rag_service.generate_hybrid_response.assert_called_once()
        call_kwargs = mock_rag_service.generate_hybrid_response.call_args.kwargs
        assert call_kwargs["user_message"] == request_data["content"]
        assert call_kwargs["scenario_context"] == request_data["scenario_context"]
    
    def test_send_message_validation_error(self, client, mock_rag_service):
        """
        Given: Invalid request (missing content field)
        When: POST /api/ai/conversations/{id}/messages is called
        Then: Returns 422 validation error
        """
        conversation_id = uuid4()
        invalid_request = {}  # Missing required 'content' field
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=invalid_request
        )
        
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_send_message_with_conversation_history(self, client, mock_rag_service):
        """
        Given: User message with existing conversation history
        When: POST /api/ai/conversations/{id}/messages is called
        Then: Returns AI message considering conversation context
        """
        conversation_id = uuid4()
        request_data = {
            "content": "Can you elaborate on that?",
            "scenario_id": str(uuid4()),
            "scenario_context": "Hermione in Slytherin",
            "book_id": "harry_potter_1",
            "conversation_history": [
                {"role": "user", "content": "How did you adjust?"},
                {"role": "assistant", "content": "I learned to be strategic..."}
            ]
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Strategic thinking became my strongest asset...",
            {"rag_used": True, "question_type": "follow_up"}
        )
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Strategic thinking became my strongest asset..."
        
        # Verify conversation history was passed
        call_kwargs = mock_rag_service.generate_hybrid_response.call_args.kwargs
        assert "conversation_history" in call_kwargs
        assert len(call_kwargs["conversation_history"]) == 2
    
    def test_send_message_rag_not_used(self, client, mock_rag_service):
        """
        Given: User message where RAG is not beneficial
        When: POST /api/ai/conversations/{id}/messages is called
        Then: Returns AI message with metadata indicating RAG was not used
        """
        conversation_id = uuid4()
        request_data = {
            "content": "What do you think about the weather?",
            "scenario_id": str(uuid4()),
            "scenario_context": "Hermione in Slytherin",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "I'd rather focus on our conversation...",
            {"rag_used": False, "question_type": "off_topic"}
        )
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["rag_used"] is False
    
    def test_send_message_rag_service_error(self, client, mock_rag_service):
        """
        Given: RAG service encounters an error
        When: POST /api/ai/conversations/{id}/messages is called
        Then: Returns 500 with error details
        """
        conversation_id = uuid4()
        request_data = {
            "content": "Test message",
            "scenario_id": str(uuid4()),
            "scenario_context": "Test scenario",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        mock_rag_service.generate_hybrid_response.side_effect = Exception("RAG service unavailable")
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        # Korean error message: "응답 생성 실패"
        assert "실패" in data["detail"] or "fail" in data["detail"].lower()
    
    def test_send_message_invalid_conversation_id(self, client, mock_rag_service):
        """
        Given: Invalid conversation ID format
        When: POST /api/ai/conversations/{id}/messages is called
        Then: Returns 422 validation error
        """
        invalid_id = "not-a-uuid"
        request_data = {
            "content": "Test message",
            "scenario_id": str(uuid4()),
            "scenario_context": "Test scenario",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        response = client.post(
            f"/api/ai/conversations/{invalid_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 422


class TestStreamingMessageEndpoint:
    """Streaming message endpoint tests"""
    
    def test_stream_message_success(self, client, mock_rag_service):
        """
        Given: Valid streaming message request
        When: POST /api/ai/conversations/{id}/messages/stream is called
        Then: Returns SSE stream with AI message chunks
        """
        conversation_id = uuid4()
        request_data = {
            "content": "Tell me about your time in Slytherin",
            "scenario_id": str(uuid4()),
            "scenario_context": "Hermione in Slytherin",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        # Configure streaming response
        mock_rag_service.generate_response_stream.return_value = iter([
            "In ", "Slytherin, ", "I learned ", "strategic ", "thinking..."
        ])
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/stream",
            json=request_data
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify streaming content
        content = response.text
        assert "data:" in content  # SSE format
        assert "In Slytherin" in content or "In " in content
    
    def test_stream_message_validation_error(self, client, mock_rag_service):
        """
        Given: Invalid streaming request (missing content)
        When: POST /api/ai/conversations/{id}/messages/stream is called
        Then: Returns 422 validation error
        """
        conversation_id = uuid4()
        invalid_request = {}  # Missing required 'content' field
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/stream",
            json=invalid_request
        )
        
        assert response.status_code == 422


class TestNoRagMessageEndpoint:
    """No-RAG message endpoint tests"""
    
    def test_no_rag_message_success(self, client, mock_rag_service):
        """
        Given: Valid message request without RAG
        When: POST /api/ai/conversations/{id}/messages/no-rag is called
        Then: Returns AI message without RAG augmentation
        """
        conversation_id = uuid4()
        request_data = {
            "content": "Let's have a casual chat",
            "scenario_context": "Hermione in Slytherin",
            "conversation_history": []
        }
        
        mock_rag_service.generate_response_without_rag.return_value = "I'd be happy to chat casually!"
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/no-rag",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "content" in data
        assert data["content"] == "I'd be happy to chat casually!"
        
        # Verify no-RAG method was called
        mock_rag_service.generate_response_without_rag.assert_called_once()
    
    def test_no_rag_message_with_history(self, client, mock_rag_service):
        """
        Given: No-RAG request with conversation history
        When: POST /api/ai/conversations/{id}/messages/no-rag is called
        Then: Returns AI message considering conversation context
        """
        conversation_id = uuid4()
        request_data = {
            "content": "Continue our discussion",
            "scenario_context": "Hermione in Slytherin",
            "conversation_history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"}
            ]
        }
        
        mock_rag_service.generate_response_without_rag.return_value = "Of course, let's continue..."
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/no-rag",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify conversation history was passed
        call_kwargs = mock_rag_service.generate_response_without_rag.call_args.kwargs
        assert "conversation_history" in call_kwargs


class TestPassageSearchEndpoint:
    """Passage search endpoint tests"""
    
    def test_search_passages_success(self, client, mock_rag_service):
        """
        Given: Valid passage search query
        When: GET /api/ai/search/passages is called
        Then: Returns relevant passages with similarity scores
        """
        mock_rag_service.search_relevant_passages.return_value = [
            {
                "text": "Hermione studied diligently in the library...",
                "metadata": {"book": "harry_potter_1", "chapter": 5},
                "similarity": 0.92
            },
            {
                "text": "Her intelligence was unmatched...",
                "metadata": {"book": "harry_potter_1", "chapter": 7},
                "similarity": 0.87
            }
        ]
        
        response = client.get(
            "/api/ai/search/passages",
            params={
                "query": "Hermione's study habits",
                "book_id": "harry_potter_1",
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # API returns 'results' not 'passages'
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["similarity"] >= data["results"][1]["similarity"]
        
        # Verify search was called with correct params
        call_kwargs = mock_rag_service.search_relevant_passages.call_args.kwargs
        assert call_kwargs["query"] == "Hermione's study habits"
        assert call_kwargs["book_id"] == "harry_potter_1"
        assert call_kwargs["top_k"] == 5
    
    def test_search_passages_no_results(self, client, mock_rag_service):
        """
        Given: Search query with no matching passages
        When: GET /api/ai/search/passages is called
        Then: Returns empty results list
        """
        mock_rag_service.search_relevant_passages.return_value = []
        
        response = client.get(
            "/api/ai/search/passages",
            params={
                "query": "Nonexistent topic",
                "book_id": "harry_potter_1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # API returns 'results' not 'passages'
        assert "results" in data
        assert len(data["results"]) == 0
    
    def test_search_passages_missing_query(self, client, mock_rag_service):
        """
        Given: Search request without query parameter
        When: GET /api/ai/search/passages is called
        Then: Returns 422 validation error
        """
        response = client.get(
            "/api/ai/search/passages",
            params={"book_id": "harry_potter_1"}
        )
        
        assert response.status_code == 422
    
    def test_search_passages_with_default_limit(self, client, mock_rag_service):
        """
        Given: Search request without explicit top_k
        When: GET /api/ai/search/passages is called
        Then: Uses default top_k value
        """
        mock_rag_service.search_relevant_passages.return_value = []
        
        response = client.get(
            "/api/ai/search/passages",
            params={
                "query": "Test query",
                "book_id": "harry_potter_1"
            }
        )
        
        assert response.status_code == 200
        
        # Verify default top_k was used (API uses 'top_k' parameter, default 5)
        call_kwargs = mock_rag_service.search_relevant_passages.call_args.kwargs
        assert "top_k" in call_kwargs
        assert call_kwargs["top_k"] == 5  # Default value


class TestConversationEndpointIntegration:
    """Integration tests combining multiple conversation endpoints"""
    
    def test_full_conversation_flow(self, client, mock_rag_service):
        """
        Given: Series of conversation interactions
        When: Multiple message endpoints are called in sequence
        Then: Conversation maintains context throughout
        """
        conversation_id = uuid4()
        scenario_id = str(uuid4())
        
        # First message - standard response
        mock_rag_service.generate_hybrid_response.return_value = (
            "I adapted by using strategic thinking...",
            {"rag_used": True}
        )
        
        response1 = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json={
                "content": "How did you adapt to Slytherin?",
                "scenario_id": scenario_id,
                "scenario_context": "Hermione in Slytherin",
                "book_id": "harry_potter_1",
                "conversation_history": []
            }
        )
        
        assert response1.status_code == 200
        first_message = response1.json()
        
        # Second message - with history
        mock_rag_service.generate_hybrid_response.return_value = (
            "My focus on strategic planning helped...",
            {"rag_used": True}
        )
        
        response2 = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json={
                "content": "Tell me more about that",
                "scenario_id": scenario_id,
                "scenario_context": "Hermione in Slytherin",
                "book_id": "harry_potter_1",
                "conversation_history": [
                    {"role": "user", "content": "How did you adapt to Slytherin?"},
                    {"role": "assistant", "content": first_message["content"]}
                ]
            }
        )
        
        assert response2.status_code == 200
        
        # Verify both messages maintain context
        assert "message_id" in first_message
        assert "message_id" in response2.json()
    
    def test_mixed_endpoint_usage(self, client, mock_rag_service):
        """
        Given: Alternating between RAG and no-RAG endpoints
        When: Different message types are sent
        Then: Each endpoint functions correctly
        """
        conversation_id = uuid4()
        
        # RAG message
        mock_rag_service.generate_hybrid_response.return_value = (
            "Based on the books, Hermione...",
            {"rag_used": True}
        )
        
        response1 = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json={
                "content": "What did Hermione do in the books?",
                "scenario_id": str(uuid4()),
                "scenario_context": "Canon Hermione",
                "book_id": "harry_potter_1",
                "conversation_history": []
            }
        )
        
        assert response1.status_code == 200
        
        # No-RAG message
        mock_rag_service.generate_response_without_rag.return_value = "Let's chat casually..."
        
        response2 = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/no-rag",
            json={
                "content": "Let's talk about something else",
                "scenario_context": "Canon Hermione",
                "conversation_history": []
            }
        )
        
        assert response2.status_code == 200
        
        # Verify both endpoints returned valid responses
        assert "message_id" in response1.json()
        assert "message_id" in response2.json()
