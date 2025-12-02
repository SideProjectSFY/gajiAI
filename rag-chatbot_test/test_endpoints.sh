#!/bin/bash

# gajiAI API Endpoint Test Script
# Tests all major endpoints with example requests

BASE_URL="http://localhost:8000"
CONVERSATION_ID=$(uuidgen)
SCENARIO_ID=$(uuidgen)
USER_ID=$(uuidgen)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print section header
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to print test result
print_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ $2${NC}"
        ((TESTS_FAILED++))
    fi
}

# Function to check if server is running
check_server() {
    if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}Error: Server is not running at $BASE_URL${NC}"
        echo "Please start the server with: uvicorn app.main:app --reload"
        exit 1
    fi
}

# Start tests
echo -e "${YELLOW}gajiAI API Endpoint Test Suite${NC}"
echo -e "${YELLOW}================================${NC}"

# Check if server is running
check_server
echo -e "${GREEN}Server is running at $BASE_URL${NC}"

# 1. Health Check Tests
print_header "1. Health Check Tests"

echo "Testing system health..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "System health check (GET /health)"

echo "Testing root endpoint..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Root endpoint (GET /)"

# 2. Character Chat Tests
print_header "2. Character Chat Tests"

echo "Testing list characters..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/character/list")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "List characters (GET /character/list)"

echo "Testing character info..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/character/info/Hermione%20Granger")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Get character info (GET /character/info/{name})"

echo "Testing character chat..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/character/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "Hermione Granger",
    "message": "Hello!",
    "conversation_history": [],
    "output_language": "en"
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Character chat (POST /character/chat)"

echo "Testing character chat stream..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/character/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "Hermione Granger",
    "message": "Tell me a short story",
    "conversation_history": [],
    "output_language": "en"
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Character chat stream (POST /character/chat/stream)"

echo "Testing character service health..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/character/health")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Character service health (GET /character/health)"

# 3. RAG Conversation Tests
print_header "3. RAG Conversation Tests"

echo "Testing RAG message..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ai/conversations/$CONVERSATION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tell me about Hermione",
    "scenario_id": "'"$SCENARIO_ID"'",
    "scenario_context": "Canon timeline",
    "book_id": "harry_potter_1",
    "conversation_history": []
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Send RAG message (POST /api/ai/conversations/{id}/messages)"

echo "Testing RAG stream..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ai/conversations/$CONVERSATION_ID/messages/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tell me more",
    "scenario_id": "'"$SCENARIO_ID"'",
    "scenario_context": "Canon timeline",
    "book_id": "harry_potter_1",
    "conversation_history": []
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Stream RAG message (POST /api/ai/conversations/{id}/messages/stream)"

echo "Testing no-RAG message..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ai/conversations/$CONVERSATION_ID/messages/no-rag" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Casual chat",
    "scenario_context": "Canon timeline",
    "conversation_history": []
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Send no-RAG message (POST /api/ai/conversations/{id}/messages/no-rag)"

echo "Testing passage search..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/ai/search/passages?query=Hermione&book_id=harry_potter_1&top_k=5")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Search passages (GET /api/ai/search/passages)"

echo "Testing conversation fork..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ai/conversations/fork" \
  -H "Content-Type: application/json" \
  -d '{
    "source_conversation_id": "'"$CONVERSATION_ID"'",
    "fork_point_message_id": "'"$CONVERSATION_ID"'",
    "new_scenario_id": "'"$SCENARIO_ID"'",
    "user_id": "'"$USER_ID"'",
    "scenario_context": "Alternate timeline",
    "source_depth": 0,
    "message_history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi there!"}
    ]
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Fork conversation (POST /api/ai/conversations/fork)"

# 4. Scenario Management Tests
print_header "4. Scenario Management Tests"

echo "Testing create scenario..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/scenario/create?creator_id=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "Test Scenario",
    "book_title": "Harry Potter",
    "character_name": "Hermione Granger",
    "is_private": false,
    "character_property_changes": {"house": "Slytherin"},
    "event_alterations": {},
    "setting_modifications": {}
  }')
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Create scenario (POST /scenario/create)"

echo "Testing get public scenarios..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/scenario/public")
print_test $([[ "$RESPONSE" == "200" ]] && echo 0 || echo 1) "Get public scenarios (GET /scenario/public)"

echo "Testing get scenario detail..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/scenario/$SCENARIO_ID")
print_test $([[ "$RESPONSE" == "200" || "$RESPONSE" == "404" ]] && echo 0 || echo 1) "Get scenario detail (GET /scenario/{id})"

echo "Testing first conversation..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/scenario/$SCENARIO_ID/first-conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_message": "Hello, how are you?"
  }')
print_test $([[ "$RESPONSE" == "200" || "$RESPONSE" == "404" ]] && echo 0 || echo 1) "First conversation (POST /scenario/{id}/first-conversation)"

echo "Testing fork scenario..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/scenario/$SCENARIO_ID/fork" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_message": "What if things were different?"
  }')
print_test $([[ "$RESPONSE" == "200" || "$RESPONSE" == "404" ]] && echo 0 || echo 1) "Fork scenario (POST /scenario/{id}/fork)"

# 5. Error Handling Tests
print_header "5. Error Handling Tests"

echo "Testing invalid UUID..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ai/conversations/not-a-uuid/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test",
    "scenario_id": "'"$SCENARIO_ID"'",
    "scenario_context": "Test",
    "book_id": "test",
    "conversation_history": []
  }')
print_test $([[ "$RESPONSE" == "422" ]] && echo 0 || echo 1) "Invalid UUID format (expects 422)"

echo "Testing missing required field..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/ai/conversations/$CONVERSATION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "'"$SCENARIO_ID"'",
    "book_id": "test"
  }')
print_test $([[ "$RESPONSE" == "422" ]] && echo 0 || echo 1) "Missing required field (expects 422)"

echo "Testing non-existent character..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/character/info/NonExistentCharacter")
print_test $([[ "$RESPONSE" == "404" ]] && echo 0 || echo 1) "Non-existent character (expects 404)"

# 6. Performance Tests
print_header "6. Performance Tests"

echo "Testing concurrent requests (5 parallel)..."
START_TIME=$(date +%s)
for i in {1..5}; do
  (curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/character/list") &
done
wait
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
print_test $([[ $DURATION -lt 10 ]] && echo 0 || echo 1) "Concurrent requests completed in ${DURATION}s (expects <10s)"

echo "Testing streaming response time..."
START_TIME=$(date +%s)
curl -s -o /dev/null -X POST "$BASE_URL/character/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "Hermione Granger",
    "message": "Quick question?",
    "conversation_history": [],
    "output_language": "en"
  }'
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
print_test $([[ $DURATION -lt 30 ]] && echo 0 || echo 1) "Streaming response time ${DURATION}s (expects <30s)"

# Summary
print_header "Test Summary"
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "${YELLOW}Total Tests: $TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed! 🎉${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
