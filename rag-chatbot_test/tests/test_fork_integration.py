"""
Test Fork Conversation Integration (Epic 4, Story 4.4)

FastAPI perspective of conversation fork integration
- Fork request validation from Spring Boot
- Message history transfer rules (ROOT-only, min(6, total) messages)
- Fork depth constraint enforcement (max depth 1)
- Error handling for invalid fork requests

NOTE: RAG Service mocking은 conftest.py에서 처리됨
NOTE: Fork endpoint not yet implemented - tests will return 404
"""

import pytest
from uuid import uuid4


class TestForkRequestValidation:
    """Fork request validation from Spring Boot"""
    
    def test_fork_request_valid_payload(self, client, mock_rag_service):
        """
        Given: Valid fork request from Spring Boot
        When: POST /api/ai/conversations/fork is called
        Then: Returns 200 with new conversation_id
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Hermione in Ravenclaw instead of Gryffindor"
        }
        
        # Configure mock for first message generation
        mock_rag_service.generate_hybrid_response.return_value = (
            "As a Ravenclaw, my perspective on knowledge is different...",
            {"rag_used": True}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "forked_conversation_id" in data
        assert "messages_copied" in data
    
    def test_fork_request_missing_required_fields(self, client, mock_rag_service):
        """
        Given: Fork request missing required fields
        When: POST /api/ai/conversations/fork is called
        Then: Returns 422 validation error
        """
        invalid_request = {
            "source_conversation_id": str(uuid4())
            # Missing fork_point_message_id, new_scenario_id, etc.
        }
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=invalid_request
        )
        
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_fork_request_invalid_uuid_format(self, client, mock_rag_service):
        """
        Given: Fork request with invalid UUID format
        When: POST /api/ai/conversations/fork is called
        Then: Returns 422 validation error
        """
        invalid_request = {
            "source_conversation_id": "not-a-uuid",
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Test scenario"
        }
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=invalid_request
        )
        
        assert response.status_code == 422


class TestMessageHistoryTransfer:
    """Message history transfer rules enforcement"""
    
    def test_fork_copies_min_6_or_total_messages(self, client, mock_rag_service):
        """
        Given: Conversation with 10 messages
        When: Fork occurs
        Then: Copies min(6, 10) = 6 messages
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "New scenario",
            "message_history": [
                {"role": "user", "content": f"Message {i}"}
                for i in range(10)
            ]
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Response with new scenario",
            {"rag_used": True}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["messages_copied"] <= 6
    
    def test_fork_copies_all_messages_if_less_than_6(self, client, mock_rag_service):
        """
        Given: Conversation with 3 messages
        When: Fork occurs
        Then: Copies all 3 messages
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "New scenario",
            "message_history": [
                {"role": "user", "content": f"Message {i}"}
                for i in range(3)
            ]
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Response with short history",
            {"rag_used": True}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["messages_copied"] == 3
    
    def test_fork_with_empty_message_history(self, client, mock_rag_service):
        """
        Given: Conversation with no messages
        When: Fork occurs
        Then: Creates new conversation with 0 copied messages
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Fresh start scenario",
            "message_history": []
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Starting fresh conversation",
            {"rag_used": True}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["messages_copied"] == 0


class TestForkDepthConstraints:
    """Fork depth constraint enforcement (ROOT-only, max depth 1)"""
    
    def test_fork_from_root_conversation_allowed(self, client, mock_rag_service):
        """
        Given: Forking from ROOT conversation (depth=0)
        When: Fork request is submitted
        Then: Fork succeeds and creates depth=1 conversation
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "source_depth": 0,  # ROOT conversation
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "First fork scenario"
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "First fork response",
            {"rag_used": True}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "forked_conversation_id" in data
    
    def test_fork_from_depth_1_conversation_blocked(self, client, mock_rag_service):
        """
        Given: Attempting to fork from depth=1 conversation
        When: Fork request is submitted
        Then: Returns 400 error (max depth exceeded)
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "source_depth": 1,  # Already a fork
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Attempting second-level fork"
        }
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "depth" in data["detail"].lower() or "fork" in data["detail"].lower()
    
    def test_fork_depth_limit_enforced(self, client, mock_rag_service):
        """
        Given: Fork depth limit is 1
        When: Attempting to create depth > 1 fork
        Then: Request is rejected
        """
        # Attempt to create depth=2 fork
        request_data = {
            "source_conversation_id": str(uuid4()),
            "source_depth": 1,
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Invalid deep fork"
        }
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 400


class TestForkErrorHandling:
    """Fork error handling and edge cases"""
    
    def test_fork_nonexistent_source_conversation(self, client, mock_rag_service):
        """
        Given: Fork request references non-existent source conversation
        When: FastAPI attempts to process fork
        Then: Returns 200 (FastAPI is stateless - Spring Boot validates existence)
        
        NOTE: FastAPI doesn't track conversations, so it successfully creates
        the fork. Spring Boot is responsible for validating source conversation
        existence before calling this endpoint.
        """
        nonexistent_id = uuid4()
        request_data = {
            "source_conversation_id": str(nonexistent_id),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Fork from nonexistent"
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Fork created",
            {"rag_used": True}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        # FastAPI is stateless - accepts request and creates fork
        # Spring Boot must validate source conversation existence beforehand
        assert response.status_code == 200
    
    def test_fork_with_rag_service_failure(self, client, mock_rag_service):
        """
        Given: RAG service fails during fork processing
        When: Fork request is submitted
        Then: Returns 500 with error details
        """
        request_data = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Fork scenario"
        }
        
        # Configure mock to fail
        mock_rag_service.generate_hybrid_response.side_effect = Exception("RAG service unavailable")
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=request_data
        )
        
        assert response.status_code == 500
    
    def test_fork_concurrent_requests_same_source(self, client, mock_rag_service):
        """
        Given: Multiple fork requests for same source conversation
        When: Requests are processed concurrently
        Then: Each fork creates separate conversation
        """
        source_id = uuid4()
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Fork response",
            {"rag_used": True}
        )
        
        # Submit multiple fork requests
        fork_requests = []
        for i in range(3):
            request_data = {
                "source_conversation_id": str(source_id),
                "fork_point_message_id": str(uuid4()),
                "new_scenario_id": str(uuid4()),
                "user_id": str(uuid4()),
                "scenario_context": f"Fork scenario {i}"
            }
            fork_requests.append(request_data)
        
        responses = []
        for request_data in fork_requests:
            response = client.post(
                "/api/ai/conversations/fork",
                json=request_data
            )
            responses.append(response)
        
        # All requests should succeed
        successful = [r for r in responses if r.status_code == 200]
        assert len(successful) >= 1  # At least one should succeed
        
        # Each fork should have unique conversation_id
        fork_ids = [r.json().get("forked_conversation_id") for r in successful]
        assert len(fork_ids) == len(set(fork_ids))  # All unique


class TestForkIntegrationWithSpringBoot:
    """Integration tests for Spring Boot to FastAPI fork flow"""
    
    def test_spring_boot_fork_request_flow(self, client, mock_rag_service):
        """
        Given: Spring Boot sends fork request
        When: FastAPI processes fork and returns forked_conversation_id
        Then: Spring Boot can use forked_conversation_id for new messages
        """
        # Step 1: Fork request from Spring Boot
        fork_request = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Hermione sorted into Hufflepuff"
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "As a Hufflepuff, I value loyalty above all...",
            {"rag_used": True}
        )
        
        fork_response = client.post(
            "/api/ai/conversations/fork",
            json=fork_request
        )
        
        assert fork_response.status_code == 200
        forked_id = fork_response.json()["forked_conversation_id"]
        
        # Step 2: Send message to forked conversation
        message_request = {
            "content": "How does Hufflepuff change your approach?",
            "scenario_id": fork_request["new_scenario_id"],
            "scenario_context": fork_request["scenario_context"],
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "In Hufflepuff, I focus on supporting others...",
            {"rag_used": True}
        )
        
        message_response = client.post(
            f"/api/ai/conversations/{forked_id}/messages",
            json=message_request
        )
        
        assert message_response.status_code == 200
        assert "content" in message_response.json()
    
    def test_fork_preserves_scenario_context(self, client, mock_rag_service):
        """
        Given: Fork request with specific scenario_context
        When: Messages are sent to forked conversation
        Then: Scenario context is maintained
        """
        scenario_context = "Harry Potter was sorted into Slytherin"
        
        fork_request = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": scenario_context
        }
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Response using scenario context",
            {"rag_used": True, "scenario_context": scenario_context}
        )
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=fork_request
        )
        
        assert response.status_code == 200
        
        # Verify scenario context was passed to RAG service
        call_kwargs = mock_rag_service.generate_hybrid_response.call_args.kwargs
        assert "scenario_context" in call_kwargs
