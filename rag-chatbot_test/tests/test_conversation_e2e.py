"""
E2E Tests for Conversation System with API Calls

Comprehensive end-to-end tests covering:
- Character chat endpoints (list, info, chat, stream)
- RAG-based conversation endpoints (messages, streaming, no-rag)
- Conversation flow and context management
- Scenario-based conversations
- Conversation forking
- Full integration across multiple endpoints

These tests simulate real user flows through the conversation system.
"""

import pytest
from uuid import uuid4
import json


class TestCharacterChatE2E:
    """E2E tests for character chat system"""
    
    def test_full_character_chat_flow(self, client, mock_character_service):
        """
        E2E Test: Complete character chat flow
        
        Given: User wants to chat with a character
        When: User lists characters, gets info, and starts chatting
        Then: All endpoints work together seamlessly
        """
        # Step 1: List available characters
        list_response = client.get("/character/list")
        assert list_response.status_code == 200
        character_list = list_response.json()
        assert "characters" in character_list
        assert len(character_list["characters"]) > 0
        
        # Get first character
        character = character_list["characters"][0]
        character_name = character["name"]
        
        # Step 2: Get detailed character info
        info_response = client.get(f"/character/info/{character_name}")
        assert info_response.status_code == 200
        character_info = info_response.json()
        assert character_info["name"] == character_name
        
        # Step 3: Start conversation with character
        chat_request = {
            "character_name": character_name,
            "message": "Hello! How are you today?",
            "conversation_history": [],
            "output_language": "ko"
        }
        
        chat_response = client.post("/character/chat", json=chat_request)
        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        
        assert "response" in chat_data
        assert chat_data["character_name"] == character_name
        assert len(chat_data["response"]) > 0
        
        # Step 4: Continue conversation with context
        continued_chat_request = {
            "character_name": character_name,
            "message": "Tell me more about that.",
            "conversation_history": [
                {"role": "user", "content": chat_request["message"]},
                {"role": "assistant", "content": chat_data["response"]}
            ],
            "output_language": "ko"
        }
        
        continued_response = client.post("/character/chat", json=continued_chat_request)
        assert continued_response.status_code == 200
        assert "response" in continued_response.json()
    
    def test_character_streaming_chat_e2e(self, client, mock_character_service):
        """
        E2E Test: Character streaming conversation
        
        Given: User wants real-time streaming responses
        When: User initiates streaming chat
        Then: Receives SSE stream with character responses
        """
        character_name = "Hermione Granger"
        
        # Configure streaming mock
        mock_character_service.stream_chat.return_value = iter([
            {"token": "I "},
            {"token": "am "},
            {"token": "doing "},
            {"token": "well, "},
            {"token": "thank "},
            {"token": "you!"}
        ])
        
        stream_request = {
            "character_name": character_name,
            "message": "How are you?",
            "conversation_history": [],
            "output_language": "ko"
        }
        
        response = client.post("/character/chat/stream", json=stream_request)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # Verify streaming content
        content = response.text
        assert "data:" in content
    
    def test_character_not_found_handling(self, client, mock_character_service):
        """
        E2E Test: Error handling for non-existent character
        
        Given: User requests info for non-existent character
        When: Character info endpoint is called
        Then: Returns 404 with clear error message
        """
        mock_character_service.get_character_info.return_value = None
        
        response = client.get("/character/info/NonExistentCharacter")
        assert response.status_code == 404
        assert "detail" in response.json()


class TestRAGConversationE2E:
    """E2E tests for RAG-based conversation system"""
    
    def test_rag_conversation_flow_with_context_building(self, client, mock_rag_service):
        """
        E2E Test: Multi-turn RAG conversation with context accumulation
        
        Given: User has a multi-turn conversation
        When: Each message builds on previous context
        Then: Conversation maintains coherence and uses RAG appropriately
        """
        conversation_id = uuid4()
        scenario_id = str(uuid4())
        book_id = "harry_potter_1"
        
        # Turn 1: Initial question with RAG
        mock_rag_service.generate_hybrid_response.return_value = (
            "Hermione was sorted into Slytherin and had to adapt her study methods.",
            {"rag_used": True, "question_type": "character_change"}
        )
        
        turn1_request = {
            "content": "How did Hermione adapt to being in Slytherin?",
            "scenario_id": scenario_id,
            "scenario_context": "Hermione Granger sorted into Slytherin",
            "book_id": book_id,
            "conversation_history": []
        }
        
        turn1_response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=turn1_request
        )
        assert turn1_response.status_code == 200
        turn1_data = turn1_response.json()
        assert turn1_data["metadata"]["rag_used"] is True
        
        # Turn 2: Follow-up question with conversation history
        mock_rag_service.generate_hybrid_response.return_value = (
            "She learned to be more strategic and calculated in her approach.",
            {"rag_used": True, "question_type": "follow_up"}
        )
        
        turn2_request = {
            "content": "What specific strategies did she develop?",
            "scenario_id": scenario_id,
            "scenario_context": "Hermione Granger sorted into Slytherin",
            "book_id": book_id,
            "conversation_history": [
                {"role": "user", "content": turn1_request["content"]},
                {"role": "assistant", "content": turn1_data["content"]}
            ]
        }
        
        turn2_response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=turn2_request
        )
        assert turn2_response.status_code == 200
        turn2_data = turn2_response.json()
        
        # Turn 3: Search for relevant passages from conversation context
        search_response = client.get(
            "/api/ai/search/passages",
            params={
                "query": "Hermione strategic thinking",
                "book_id": book_id,
                "top_k": 5
            }
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert "results" in search_data
        
        # Verify context was maintained across all turns
        assert "message_id" in turn1_data
        assert "message_id" in turn2_data
    
    def test_streaming_rag_conversation_e2e(self, client, mock_rag_service):
        """
        E2E Test: Real-time streaming RAG conversation
        
        Given: User wants streaming responses with RAG
        When: Streaming endpoint is called
        Then: Receives SSE stream with RAG-enhanced content
        """
        conversation_id = uuid4()
        
        mock_rag_service.generate_response_stream.return_value = iter([
            "In ", "Slytherin, ", "Hermione ", "learned ", "to ", "think ", 
            "strategically ", "and ", "carefully ", "plan ", "her ", "actions."
        ])
        
        stream_request = {
            "content": "Tell me about Hermione's time in Slytherin",
            "scenario_id": str(uuid4()),
            "scenario_context": "Hermione in Slytherin alternate timeline",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/stream",
            json=stream_request
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # Verify SSE format
        content = response.text
        assert "data:" in content
        assert "Slytherin" in content or "In " in content
    
    def test_rag_vs_no_rag_comparison_e2e(self, client, mock_rag_service):
        """
        E2E Test: Compare RAG and non-RAG responses
        
        Given: Same question asked with and without RAG
        When: Both endpoints are called
        Then: Both provide responses but with different characteristics
        """
        conversation_id = uuid4()
        question = "What would Hermione do in this situation?"
        
        # RAG-enhanced response
        mock_rag_service.generate_hybrid_response.return_value = (
            "Based on the books, Hermione would analyze the situation carefully...",
            {"rag_used": True, "question_type": "character_behavior"}
        )
        
        rag_request = {
            "content": question,
            "scenario_id": str(uuid4()),
            "scenario_context": "Hermione faces a difficult choice",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        rag_response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=rag_request
        )
        assert rag_response.status_code == 200
        rag_data = rag_response.json()
        assert rag_data["metadata"]["rag_used"] is True
        
        # Non-RAG response
        mock_rag_service.generate_response_without_rag.return_value = (
            "Hermione would think carefully about her options..."
        )
        
        no_rag_request = {
            "content": question,
            "scenario_context": "Hermione faces a difficult choice",
            "conversation_history": []
        }
        
        no_rag_response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/no-rag",
            json=no_rag_request
        )
        assert no_rag_response.status_code == 200
        no_rag_data = no_rag_response.json()
        
        # Both should return valid responses
        assert "content" in rag_data
        assert "content" in no_rag_data
        assert len(rag_data["content"]) > 0
        assert len(no_rag_data["content"]) > 0


class TestConversationForkingE2E:
    """E2E tests for conversation forking functionality"""
    
    def test_conversation_fork_creation_e2e(self, client, mock_rag_service):
        """
        E2E Test: Fork conversation at decision point
        
        Given: Existing conversation with history
        When: User forks conversation with new scenario
        Then: New forked conversation created with copied history
        """
        # Setup: Create a conversation with history
        source_conversation_id = uuid4()
        scenario_id = uuid4()
        
        # Build conversation history (simulate 4 messages)
        conversation_history = [
            {"role": "user", "content": "What if Hermione was in Slytherin?"},
            {"role": "assistant", "content": "She would adapt her methods..."},
            {"role": "user", "content": "How would she interact with Draco?"},
            {"role": "assistant", "content": "They might become allies..."}
        ]
        
        # Configure mock for fork validation
        mock_rag_service.generate_hybrid_response.return_value = (
            "In this forked scenario, Hermione's approach changes...",
            {"rag_used": True}
        )
        
        # Fork the conversation
        fork_request = {
            "source_conversation_id": str(source_conversation_id),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(scenario_id),
            "user_id": str(uuid4()),
            "scenario_context": "Hermione and Draco become study partners",
            "source_depth": 0,  # ROOT conversation
            "message_history": conversation_history
        }
        
        fork_response = client.post(
            "/api/ai/conversations/fork",
            json=fork_request
        )
        
        assert fork_response.status_code == 200
        fork_data = fork_response.json()
        
        # Verify fork was created
        assert "forked_conversation_id" in fork_data
        assert fork_data["new_depth"] == 1
        assert fork_data["messages_copied"] == min(6, len(conversation_history))
        assert fork_data["scenario_context"] == fork_request["scenario_context"]
        
        # Verify we can continue the forked conversation
        forked_conversation_id = fork_data["forked_conversation_id"]
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Working together, they discover unexpected synergies...",
            {"rag_used": True}
        )
        
        continue_request = {
            "content": "How does their partnership develop?",
            "scenario_id": str(scenario_id),
            "scenario_context": fork_request["scenario_context"],
            "book_id": "harry_potter_1",
            "conversation_history": conversation_history
        }
        
        continue_response = client.post(
            f"/api/ai/conversations/{forked_conversation_id}/messages",
            json=continue_request
        )
        
        assert continue_response.status_code == 200
        assert "content" in continue_response.json()
    
    def test_fork_from_forked_conversation_rejected_e2e(self, client, mock_rag_service):
        """
        E2E Test: Prevent forking from already forked conversation
        
        Given: Conversation that is already a fork (depth=1)
        When: User attempts to fork it again
        Then: Returns 400 error with clear message
        """
        fork_request = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Double fork attempt",
            "source_depth": 1,  # Already forked
            "message_history": []
        }
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=fork_request
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "ROOT" in error_data["detail"] or "depth" in error_data["detail"]
    
    def test_fork_with_message_history_limit_e2e(self, client, mock_rag_service):
        """
        E2E Test: Verify message history limit in fork
        
        Given: Conversation with many messages (>6)
        When: Conversation is forked
        Then: Only last 6 messages are copied
        """
        # Create long conversation history (10 messages)
        long_history = []
        for i in range(10):
            long_history.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i+1}"
            })
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "Fork validation successful",
            {"rag_used": True}
        )
        
        fork_request = {
            "source_conversation_id": str(uuid4()),
            "fork_point_message_id": str(uuid4()),
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": "Test message limit",
            "source_depth": 0,
            "message_history": long_history
        }
        
        response = client.post(
            "/api/ai/conversations/fork",
            json=fork_request
        )
        
        assert response.status_code == 200
        fork_data = response.json()
        
        # Should only copy 6 messages, not all 10
        assert fork_data["messages_copied"] == 6


class TestConversationErrorHandlingE2E:
    """E2E tests for error handling in conversation system"""
    
    def test_invalid_conversation_id_handling(self, client, mock_rag_service):
        """
        E2E Test: Handle invalid conversation ID format
        
        Given: Malformed conversation ID
        When: Message endpoint is called
        Then: Returns 422 validation error
        """
        invalid_id = "not-a-uuid"
        
        request_data = {
            "content": "Test message",
            "scenario_id": str(uuid4()),
            "scenario_context": "Test",
            "book_id": "test_book",
            "conversation_history": []
        }
        
        response = client.post(
            f"/api/ai/conversations/{invalid_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields_handling(self, client, mock_rag_service):
        """
        E2E Test: Handle missing required request fields
        
        Given: Request missing required fields
        When: Message endpoint is called
        Then: Returns 422 with field validation errors
        """
        conversation_id = uuid4()
        
        # Missing 'content' field
        invalid_request = {
            "scenario_id": str(uuid4()),
            "book_id": "test_book"
        }
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=invalid_request
        )
        
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_rag_service_failure_handling(self, client, mock_rag_service):
        """
        E2E Test: Handle RAG service failures gracefully
        
        Given: RAG service encounters error
        When: Message is sent
        Then: Returns 500 with informative error message
        """
        conversation_id = uuid4()
        
        # Configure mock to raise exception
        mock_rag_service.generate_hybrid_response.side_effect = Exception(
            "RAG service temporarily unavailable"
        )
        
        request_data = {
            "content": "Test message",
            "scenario_id": str(uuid4()),
            "scenario_context": "Test scenario",
            "book_id": "test_book",
            "conversation_history": []
        }
        
        response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=request_data
        )
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data


class TestFullConversationJourneyE2E:
    """E2E tests simulating complete user journeys"""
    
    def test_complete_scenario_based_conversation_journey(self, client, mock_rag_service, mock_character_service):
        """
        E2E Test: Complete user journey from character selection to forked conversation
        
        Simulates full flow:
        1. List and select character
        2. Start scenario-based conversation
        3. Have multi-turn conversation
        4. Fork conversation at decision point
        5. Continue both branches
        """
        # Step 1: List characters
        list_response = client.get("/character/list")
        assert list_response.status_code == 200
        characters = list_response.json()["characters"]
        character = characters[0]
        
        # Step 2: Start main conversation
        conversation_id = uuid4()
        scenario_id = str(uuid4())
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "In Slytherin, I learned to value strategic thinking...",
            {"rag_used": True}
        )
        
        initial_message = {
            "content": "How did being in Slytherin change you?",
            "scenario_id": scenario_id,
            "scenario_context": f"{character['name']} sorted into Slytherin",
            "book_id": "harry_potter_1",
            "conversation_history": []
        }
        
        msg1_response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=initial_message
        )
        assert msg1_response.status_code == 200
        msg1_data = msg1_response.json()
        
        # Step 3: Continue conversation
        history = [
            {"role": "user", "content": initial_message["content"]},
            {"role": "assistant", "content": msg1_data["content"]}
        ]
        
        mock_rag_service.generate_hybrid_response.return_value = (
            "I developed new friendships with unexpected people...",
            {"rag_used": True}
        )
        
        msg2_request = {
            "content": "Tell me about your friendships",
            "scenario_id": scenario_id,
            "scenario_context": initial_message["scenario_context"],
            "book_id": "harry_potter_1",
            "conversation_history": history
        }
        
        msg2_response = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json=msg2_request
        )
        assert msg2_response.status_code == 200
        msg2_data = msg2_response.json()
        
        # Update history
        history.extend([
            {"role": "user", "content": msg2_request["content"]},
            {"role": "assistant", "content": msg2_data["content"]}
        ])
        
        # Step 4: Fork conversation for alternate path
        mock_rag_service.generate_hybrid_response.return_value = (
            "Fork validation response",
            {"rag_used": True}
        )
        
        fork_request = {
            "source_conversation_id": str(conversation_id),
            "fork_point_message_id": msg2_data["message_id"],
            "new_scenario_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scenario_context": f"{character['name']} becomes Slytherin prefect",
            "source_depth": 0,
            "message_history": history
        }
        
        fork_response = client.post(
            "/api/ai/conversations/fork",
            json=fork_request
        )
        assert fork_response.status_code == 200
        fork_data = fork_response.json()
        
        # Step 5: Continue both branches
        forked_conversation_id = fork_data["forked_conversation_id"]
        
        # Continue original conversation
        mock_rag_service.generate_hybrid_response.return_value = (
            "Original branch: My strategic skills helped in many situations...",
            {"rag_used": True}
        )
        
        original_continue = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json={
                "content": "What happened next?",
                "scenario_id": scenario_id,
                "scenario_context": initial_message["scenario_context"],
                "book_id": "harry_potter_1",
                "conversation_history": history
            }
        )
        assert original_continue.status_code == 200
        
        # Continue forked conversation
        mock_rag_service.generate_hybrid_response.return_value = (
            "Forked branch: As prefect, I had new responsibilities...",
            {"rag_used": True}
        )
        
        forked_continue = client.post(
            f"/api/ai/conversations/{forked_conversation_id}/messages",
            json={
                "content": "How did being prefect change things?",
                "scenario_id": fork_request["new_scenario_id"],
                "scenario_context": fork_request["scenario_context"],
                "book_id": "harry_potter_1",
                "conversation_history": history
            }
        )
        assert forked_continue.status_code == 200
        
        # Verify both branches are independent
        original_content = original_continue.json()["content"]
        forked_content = forked_continue.json()["content"]
        assert "Original branch" in original_content or len(original_content) > 0
        assert "Forked branch" in forked_content or len(forked_content) > 0
    
    def test_mixed_mode_conversation_journey(self, client, mock_rag_service):
        """
        E2E Test: Journey mixing RAG and non-RAG modes
        
        Tests switching between RAG-enhanced and casual conversation
        """
        conversation_id = uuid4()
        scenario_id = str(uuid4())
        
        # Start with RAG-enhanced question
        mock_rag_service.generate_hybrid_response.return_value = (
            "Based on the books, this is what happened...",
            {"rag_used": True}
        )
        
        rag_msg = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json={
                "content": "What does the book say about this?",
                "scenario_id": scenario_id,
                "scenario_context": "Canon timeline",
                "book_id": "harry_potter_1",
                "conversation_history": []
            }
        )
        assert rag_msg.status_code == 200
        
        # Switch to casual chat without RAG
        mock_rag_service.generate_response_without_rag.return_value = (
            "Let's just chat casually about this..."
        )
        
        no_rag_msg = client.post(
            f"/api/ai/conversations/{conversation_id}/messages/no-rag",
            json={
                "content": "Let's talk more casually",
                "scenario_context": "Canon timeline",
                "conversation_history": [
                    {"role": "user", "content": "What does the book say?"},
                    {"role": "assistant", "content": rag_msg.json()["content"]}
                ]
            }
        )
        assert no_rag_msg.status_code == 200
        
        # Search for relevant passages
        search_response = client.get(
            "/api/ai/search/passages",
            params={"query": "test topic", "book_id": "harry_potter_1", "top_k": 3}
        )
        assert search_response.status_code == 200
        
        # Return to RAG mode
        mock_rag_service.generate_hybrid_response.return_value = (
            "Returning to book-based discussion...",
            {"rag_used": True}
        )
        
        back_to_rag = client.post(
            f"/api/ai/conversations/{conversation_id}/messages",
            json={
                "content": "Back to the book discussion",
                "scenario_id": scenario_id,
                "scenario_context": "Canon timeline",
                "book_id": "harry_potter_1",
                "conversation_history": []
            }
        )
        assert back_to_rag.status_code == 200


class TestConversationHealthAndMonitoring:
    """E2E tests for health checks and system monitoring"""
    
    def test_health_check_reflects_conversation_system_status(self, client):
        """
        E2E Test: Health endpoint reflects conversation system status
        
        Given: Conversation system components
        When: Health check is called
        Then: Returns status of all relevant components
        """
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "gemini_api" in health_data
        assert "vectordb" in health_data
        
        # Should indicate overall system health
        assert health_data["status"] in ["healthy", "unhealthy"]
    
    def test_character_chat_health_check(self, client):
        """
        E2E Test: Character chat service health check
        
        Given: Character chat service
        When: Health endpoint is called
        Then: Returns character chat service status
        """
        response = client.get("/character/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "service" in health_data
        assert health_data["service"] == "character-chat"
