# Epic 4: Conversation System with Gemini 2.5 Flash

## Epic Goal

Build a **real-time AI conversation system** where users can chat with literary characters adapted to alternate "What If" timelines using **Gemini 2.5 Flash via FastAPI**, with support for **Long Polling** for async message generation, conversation forking (ROOT-only, max depth 1), and VectorDB-powered context management.

## User Value

Users can engage in meaningful conversations with AI characters who authentically embody their alternate timeline selves. The Long Polling interface provides smooth async feedback (2-second polls), conversation forking enables exploration of different dialogue paths with **min(6, total) message copy**, and the system maintains character consistency across complex scenario contexts using VectorDB.

## Architecture Context

- **LLM**: **Gemini 2.5 Flash** (1M input tokens, 8K output tokens) via FastAPI (Port 8000)
- **Backend**: Spring Boot (Port 8080) for CRUD operations, FastAPI (Port 8000) for AI/LLM operations
- **Communication Pattern**: **Long Polling** (2-second intervals) for async AI message generation
  - Frontend: `POST /api/conversations/{id}/messages` → returns task_id immediately
  - Frontend polls: `GET /api/conversations/{id}/messages/{taskId}/status` every 2 seconds
  - Response: `{status: "PENDING"|"COMPLETED"|"FAILED", progress: 0-100, message: {...}}`
- **Browser Notifications**: WebSocket/SSE for task completion alerts (user doesn't need to stay on page)
- **Database**: PostgreSQL for conversation/message metadata, VectorDB for character/passage context
- **Message Streaming**: NOT used in MVP (Long Polling for simplicity, SSE/WebSocket in Phase 2)

## Timeline

**Week 2, Day 3 - Week 3, Day 1 of MVP development**

## Stories

### Story 4.1: Conversation Data Model & CRUD API with Fork Constraints

**Priority: P0 - Critical**

**Description**: Implement PostgreSQL schema for conversations and messages, with REST API for creating conversations, retrieving message history, and managing conversation metadata. **Enforce ROOT-only forking with max depth 1 and min(6, total) message copy rule.**

**Acceptance Criteria**:

- [ ] Conversation and Message entities created (see ERD.md for schema)
  - conversations table: `id, scenario_id, user_id, character_name, parent_conversation_id, is_root, has_been_forked, like_count, created_at, updated_at, deleted_at`
  - messages table: `id, conversation_id, role, content, token_count, created_at`
- [ ] ConversationRepository with methods:
  - `findById(UUID id)`
  - `findByUserId(UUID userId, Pageable)`
  - `findByScenarioId(UUID scenarioId, Pageable)`
  - `findByUserIdAndScenarioId(UUID userId, UUID scenarioId, Pageable)`
  - `countByScenarioId(UUID scenarioId)` (for scenario.conversation_count)
  - `findPopularConversations(Pageable)` (order by like_count DESC)
  - **`findRootConversations(UUID scenarioId, Pageable)`** (WHERE is_root = TRUE)
  - **`countForksByParentId(UUID parentId)`** (verify has_been_forked accuracy)
- [ ] MessageRepository with methods:
  - `findByConversationId(UUID conversationId, Pageable)`
  - `countByConversationId(UUID conversationId)` (message count)
  - `sumTokenCountByConversationId(UUID conversationId)` (total tokens used)
  - **`findLastNMessages(UUID conversationId, int n)`** (for fork message copy)
- [ ] ConversationService with methods:
  - `createConversation(UUID userId, UUID scenarioId, String characterName) → ConversationResponse`
  - `getConversation(UUID conversationId) → ConversationResponse`
  - `getConversationMessages(UUID conversationId, int page, int size) → Page<MessageResponse>`
  - `getUserConversations(UUID userId, int page, int size) → Page<ConversationResponse>`
  - `getScenarioConversations(UUID scenarioId, int page, int size) → Page<ConversationResponse>`
  - **`forkConversation(UUID conversationId, UUID userId, UUID targetScenarioId) → ConversationResponse`** (Story 4.4)
  - `deleteConversation(UUID conversationId)` (soft delete)
- [ ] REST API endpoints:
  - POST /api/v1/conversations (requires authentication)
  - GET /api/v1/conversations/{id}
  - GET /api/v1/conversations/{id}/messages?page=0&size=50
  - GET /api/v1/users/{userId}/conversations?page=0&size=20
  - GET /api/v1/scenarios/{scenarioId}/conversations?page=0&size=20
  - **POST /api/v1/conversations/{id}/fork** (Story 4.4, requires authentication)
  - DELETE /api/v1/conversations/{id} (requires authentication, owner only)
- [ ] Conversation metadata:
  - scenario_id (which scenario this conversation explores, FK to base_scenarios or root/leaf_user_scenarios)
  - **parent_conversation_id** (UUID, nullable, FK to conversations.id)
  - **is_root** (BOOLEAN, DEFAULT TRUE) - TRUE if parent_conversation_id IS NULL
  - character_name (which character user is talking to, matches VectorDB character_vectordb_id reference)
  - **has_been_forked** (BOOLEAN, DEFAULT FALSE) - prevents multiple forks per ROOT conversation
  - like_count (denormalized, updated by Epic 6)
  - created_at, updated_at, deleted_at (soft delete)
- [ ] Message metadata:
  - role: "user" or "assistant"
  - content: message text (max 10,000 chars for Gemini responses)
  - token_count: for cost tracking and context window management (from Gemini Tokenizer API)
  - created_at timestamp
- [ ] Validation rules:
  - Character name: max 100 chars, required, must exist in VectorDB character collection
  - User message: max 2,000 chars (increased from 1,000 for Gemini 2.5 Flash)
  - Scenario must exist and not be deleted
  - User can only delete their own conversations
  - **Fork validation**: conversation must be ROOT (is_root = TRUE), not already forked (has_been_forked = FALSE)
- [ ] Business rules:
  - Creating conversation increments scenario.conversation_count atomically
  - Soft deleting conversation decrements scenario.conversation_count
  - Messages ordered by created_at ASC (oldest first)
  - Conversation list ordered by updated_at DESC (most recent first)
  - User must send first message (no AI-initiated conversations)
  - **CRITICAL FORK CONSTRAINTS** (enforced in database + application):
    - **Only ROOT conversations can be forked** (parent_conversation_id IS NULL, is_root = TRUE)
    - **Root conversations can be forked ONLY ONCE** (has_been_forked flag set to TRUE after fork)
    - **Forked conversations CANNOT be re-forked** (is_root = FALSE, no fork button in UI)
    - Attempting to fork a forked conversation → **403 Forbidden** "Cannot fork: only ROOT conversations can be forked"
    - Attempting to re-fork a root → **409 Conflict** "Cannot fork: conversation has already been forked"
  - **Message Copy on Fork**: Copy **min(6, total_message_count)** messages
    - If parent has ≥6 messages → copy **last 6 messages** (most recent context)
    - If parent has <6 messages → copy **ALL messages**
    - Example: 8 messages → copy messages #3-8 (last 6), 3 messages → copy all 3
    - Copied messages: same role, content, token_count, new created_at (fork timestamp)
- [ ] Unit tests for ConversationService and MessageRepository
- [ ] Integration tests for all conversation endpoints, **including fork validation tests**

**API Examples**:

**POST /api/v1/conversations**

```json
Request:
{
  "scenario_id": "uuid",
  "character_name": "Hermione Granger"
}

Response (201 Created):
{
  "id": "uuid",
  "scenario_id": "uuid",
  "scenario_title": "What if Hermione was sorted into Slytherin?",
  "user_id": "uuid",
  "character_name": "Hermione Granger",
  "character_vectordb_id": "hermione_slytherin_123",
  "parent_conversation_id": null,
  "is_root": true,
  "has_been_forked": false,
  "message_count": 0,
  "like_count": 0,
  "created_at": "2025-11-13T10:00:00Z",
  "updated_at": "2025-11-13T10:00:00Z"
}
```

**GET /api/v1/conversations/{id}/messages?page=0&size=50**

```json
Response (200 OK):
{
  "content": [
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "role": "user",
      "content": "How do you feel about being in Slytherin?",
      "token_count": 12,
      "created_at": "2025-11-13T10:01:00Z"
    },
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "role": "assistant",
      "content": "At first, I was shocked—Slytherin? Me? But I've come to appreciate the strategic thinking and ambition that Slytherin values. It's challenged me to see that intelligence isn't just about memorizing facts...",
      "token_count": 487,
      "created_at": "2025-11-13T10:01:08Z"
    }
  ],
  "page": 0,
  "size": 50,
  "total_elements": 10,
  "total_pages": 1
}
```

**Technical Notes**:

- Use database transactions for conversation creation + scenario.conversation_count increment
- Index on (user_id, created_at DESC) for fast user conversation queries
- Index on (scenario_id, created_at DESC) for scenario conversation list
- Index on (parent_conversation_id) for fork queries
- **Composite index** on (is_root, has_been_forked) for fork validation queries
- Store token_count for each message (use **Gemini Tokenizer API** via FastAPI for accurate counting)
- Soft delete: set deleted_at timestamp, filter out in queries with `WHERE deleted_at IS NULL`
- **Character validation**: Query VectorDB via FastAPI `POST /api/ai/vectordb/characters/validate` to ensure character_name exists

**Estimated Effort**: 10 hours (increased from 8h for fork constraint implementation)

---

### Story 4.2: Gemini 2.5 Flash Integration via FastAPI with Long Polling

**Priority: P0 - Critical**

**Description**: Integrate **Gemini 2.5 Flash via FastAPI** for generating AI character responses with **Long Polling** for async message delivery. Spring Boot submits task to FastAPI, returns task_id immediately, frontend polls for completion every 2 seconds.

**Acceptance Criteria**:

- [ ] **AI Service Integration (Spring Boot → FastAPI → Gemini 2.5 Flash)**
  - Spring Boot calls FastAPI endpoint: **`POST /api/ai/chat/generate`** (not streaming, single response)
  - FastAPI handles **Gemini 2.5 Flash** LLM inference with generation config (temperature, top_p, top_k, max_output_tokens)
  - FastAPI returns task_id immediately to Spring Boot
  - FastAPI processes generation in background (Celery worker + Redis/RabbitMQ)
  - FastAPI stores result in Redis with TTL=600 seconds (10 minutes)
  - Configurable model, temperature, max_output_tokens per scenario type (from Epic 2, Story 2.3)
  - Retry logic for Gemini API call failures (3 retries with exponential backoff)
  - Error handling: API errors, timeout (30-second max), inference failures
  - Performance tracking: log token generation speed, Gemini API latency per request
- [ ] **Long Polling Endpoint** (Spring Boot)
  - **POST /api/v1/conversations/{id}/messages** endpoint (requires authentication)
  - Accept user message in request body: `{content: "...", scenario_id: "uuid"}`
  - **Return task_id immediately** (201 Created, no waiting for AI response)
  - Response: `{task_id: "uuid", status: "PENDING", conversation_id: "uuid"}`
- [ ] **Polling Status Endpoint** (Spring Boot → FastAPI)
  - **GET /api/v1/conversations/{id}/messages/status/{taskId}** endpoint
  - Spring Boot queries FastAPI: **`GET /api/ai/chat/status/{taskId}`**
  - FastAPI checks Redis for task status
  - Response: `{status: "PENDING"|"COMPLETED"|"FAILED", progress: 0-100, message: {...}|null, error: "..."|null}`
  - **PENDING**: Task still processing, progress indicates % completion (0-100)
  - **COMPLETED**: AI message ready, includes full message object with content + token_count
  - **FAILED**: Error occurred, includes error message for user-friendly display
- [ ] **Message Flow with Long Polling**:
  1. **User submits message**: Frontend → `POST /api/v1/conversations/{id}/messages` → Spring Boot
  2. **Validate user message**: max 2,000 chars, conversation exists, user owns conversation
  3. **Save user message** to PostgreSQL with role="user", token_count (from Gemini Tokenizer API)
  4. **Retrieve conversation context**: scenario + last **50 messages** (Gemini 2.5 Flash supports large context)
  5. **Query VectorDB for character context** via FastAPI: `POST /api/ai/vectordb/characters/{characterName}/context`
  - Returns: character personality, traits, relationships (from VectorDB character collection)
  6. **Generate system prompt** from scenario (Epic 2, Story 2.1) + VectorDB character context
  7. **Build Gemini messages array**: `[{role: "user", parts: [{text: system_prompt}]}, {role: "model", parts: [{text: "Acknowledged"}]}, ...conversation_history, {role: "user", parts: [{text: user_message}]}]`
  8. **Spring Boot calls FastAPI**: `POST /api/ai/chat/generate` with conversation context + generation config
  9. **FastAPI queues task** in Celery, returns task_id to Spring Boot
  10. **Spring Boot returns task_id** to frontend (201 Created)
  11. **Frontend starts polling**: `GET /api/v1/conversations/{id}/messages/status/{taskId}` every **2 seconds**
  12. **Spring Boot proxies poll** to FastAPI: `GET /api/ai/chat/status/{taskId}`
  13. **FastAPI checks Redis** for task status, returns current state
  14. **When COMPLETED**: Spring Boot saves assistant message to PostgreSQL with role="assistant", token_count (from Gemini response)
  15. **Update conversation.updated_at** timestamp
  16. **Frontend stops polling**, displays AI message
  17. **Browser notification** (if user navigated away): "Your conversation with {character} is ready!" (via WebSocket/SSE from Spring Boot)
- [ ] **Token counting**:
  - Count user message tokens using **Gemini Tokenizer API** via FastAPI `POST /api/ai/tokenize`
  - Count assistant response tokens from Gemini generation metadata
  - Store both in messages table
  - Track cumulative tokens per conversation for cost tracking
- [ ] **Rate limiting** (per user, Spring Boot + Redis):
  - Max **50 messages per hour** (MVP, increased from 30 for better UX)
  - Return **429 Too Many Requests** if exceeded
  - Include Retry-After header with seconds until limit resets
  - Store rate limit counters in Redis with 1-hour TTL
- [ ] **Error handling**:
  - FastAPI/Gemini API errors: Celery retries 3 times with exponential backoff (1s, 2s, 4s)
  - Timeout: 30-second max for Gemini API call, return FAILED status if exceeded
  - Network errors: Circuit breaker pattern (Resilience4j) for FastAPI calls, fallback to error message
  - Token limit exceeded: Truncate context window (remove oldest messages), retry generation
  - Invalid scenario_id: Return 400 Bad Request
  - User not authenticated: Return 401 Unauthorized
  - Conversation not found: Return 404 Not Found
- [ ] **Browser Notification Integration**:
  - Spring Boot WebSocket/SSE endpoint: `GET /api/v1/notifications/stream/{userId}`
  - When task COMPLETED, send notification: `{type: "message_ready", conversation_id: "uuid", character_name: "..."}`
  - Frontend displays browser notification (if permission granted)
  - User clicks notification → navigate to conversation page
- [ ] Unit tests for MessageService with FastAPI client mocking
- [ ] Integration tests:
  - Submit message → poll status → verify PENDING → wait for COMPLETED → verify message saved
  - Submit message → FastAPI returns error → verify FAILED status with error message
  - Rate limit: submit 51 messages → verify 429 on 51st request

**API Examples**:

**POST /api/v1/conversations/{id}/messages**

```json
Request:
{
  "content": "How did being in Slytherin change your approach to studying?",
  "scenario_id": "uuid"
}

Response (201 Created):
{
  "task_id": "uuid",
  "status": "PENDING",
  "conversation_id": "uuid",
  "poll_url": "/api/v1/conversations/{id}/messages/status/{taskId}"
}
```

**GET /api/v1/conversations/{id}/messages/status/{taskId}** (poll every 2 seconds)

```json
Response (200 OK) - PENDING:
{
  "status": "PENDING",
  "progress": 45,
  "message": null,
  "error": null
}

Response (200 OK) - COMPLETED:
{
  "status": "COMPLETED",
  "progress": 100,
  "message": {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "In Slytherin, I learned that studying isn't just about absorbing knowledge—it's about using it strategically. My housemates taught me to think several steps ahead, to see how each piece of information could be leveraged. While Gryffindor valued courage in learning, Slytherin values cunning application of knowledge.",
    "token_count": 512,
    "created_at": "2025-11-13T10:05:23Z"
  },
  "error": null
}

Response (200 OK) - FAILED:
{
  "status": "FAILED",
  "progress": 0,
  "message": null,
  "error": "Gemini API timeout after 30 seconds. Please try again."
}
```

**Technical Notes**:

- **Long Polling Interval**: Frontend polls every **2 seconds** (balance between responsiveness and server load)
- **Exponential Backoff for Errors**: If poll fails, increase interval: 2s → 4s → 8s → max 30s
- **Cancel Polling**: Frontend cancels polling if user navigates away (cleanup on component unmount)
- **Task TTL**: Redis stores task status for 10 minutes (600 seconds), auto-expire after
- **Browser Notification**: Use Web Notification API with permission request on first conversation
- **Gemini Generation Config** (from Epic 2, Story 2.3):
  - CHARACTER_CHANGE: `{temperature: 0.7, top_p: 0.9, top_k: 40, max_output_tokens: 2048}`
  - EVENT_ALTERATION: `{temperature: 0.6, top_p: 0.85, top_k: 30, max_output_tokens: 2048}`
  - SETTING_MODIFICATION: `{temperature: 0.8, top_p: 0.95, top_k: 50, max_output_tokens: 2048}`
- **Context Window**: Last 50 messages (~10,000-15,000 tokens) + system prompt (2,000 tokens) + VectorDB context (3,000-5,000 tokens) = ~20,000 tokens total (far below Gemini's 1M limit)
- **VectorDB Context Query**: FastAPI `POST /api/ai/vectordb/characters/{characterName}/context` with scenario_id parameter
  - Returns: character personality JSON, passage content, relationships
- **Circuit Breaker**: Use Resilience4j with thresholds: 5 failures in 10 seconds → OPEN for 30 seconds
- **Cost Tracking**: Store Gemini API costs in Redis: `conversation:{id}:cost` = (input_tokens × $0.075 / 1M) + (output_tokens × $0.30 / 1M)

**Estimated Effort**: 12 hours (increased from 10h for Long Polling + browser notification implementation)

---

- LLM timeout: return error event via SSE
- Invalid scenario: return 404 Not Found
- User not owner: return 403 Forbidden
- [ ] Unit tests for AI service integration (mock FastAPI calls)
- [ ] Integration tests for message streaming endpoint

**API Example**:

**POST /api/v1/conversations/{id}/messages**

```json
Request:
{
  "content": "How do you feel about being in Slytherin?"
}

Response (SSE stream):
event: message
data: {"content": "At", "done": false}

event: message
data: {"content": " first,", "done": false}

event: message
data: {"content": " I", "done": false}

event: message
data: {"content": " was", "done": false}

...

event: message
data: {"content": " appreciate...", "done": false}

event: done
data: {"done": true, "token_count": 85, "message_id": "uuid"}
```

**Technical Notes**:

- **API Gateway Pattern**: Frontend → Spring Boot → FastAPI (for LLM inference)
- **Spring Boot WebFlux**: Use `Flux<ServerSentEvent<String>>` for SSE streaming
- **FastAPI Streaming**: FastAPI calls Gemini API with `stream=true` parameter
- **Spring Boot Proxy Flow**:
  ```java
  // Spring Boot proxies streaming from FastAPI to Frontend
  @PostMapping(value = "/api/v1/conversations/{id}/messages",
               produces = MediaType.TEXT_EVENT_STREAM_VALUE)
  public Flux<ServerSentEvent<String>> streamMessage(
      @PathVariable UUID id,
      @RequestBody MessageRequest request
  ) {
      return fastApiClient.post()
          .uri("/api/ai/chat/stream")
          .bodyValue(buildChatRequest(id, request))
          .retrieve()
          .bodyToFlux(String.class)
          .map(token -> ServerSentEvent.<String>builder().data(token).build());
  }
  ```
- **Token Counting**: Use tiktoken library (in FastAPI) for accurate token counting
- **Gemini API Key**: Stored in FastAPI environment only (never in Spring Boot)
- Log all inference requests in FastAPI for debugging and performance analysis
- Temperature settings from Epic 2, Story 2.3: 0.6-0.8 based on scenario type
- Enforce user-first message rule: reject POST if conversation has 0 messages and role != "user"
- Context window: keep last 6 messages only to maintain focus and reduce token costs

**Estimated Effort**: 10 hours

---

### Story 4.3: Real-Time Chat Interface UI with Long Polling

**Priority: P0 - Critical**

**Description**: Build responsive chat interface with **Long Polling** for async message delivery, typing indicators, browser notifications, and optimized mobile/desktop layouts.

**Acceptance Criteria**:

- [ ] ChatView component (`/conversations/{id}` route)
  - Full-height layout (fills viewport, no scrolling except message list)
  - Chat header:
    - Scenario title (clickable, links to scenario detail)
    - Character name badge with VectorDB character reference
    - Like button (from Epic 6)
    - Memo button (from Epic 6)
    - **Fork conversation button** (Story 4.4) - **ONLY visible for ROOT conversations** (is_root = TRUE, has_been_forked = FALSE)
    - Options menu (delete conversation)
  - Message list:
    - Auto-scroll to bottom on new messages
    - Scroll to load older messages (pagination, load 50 per page)
    - User messages: right-aligned, blue background
    - Assistant messages: left-aligned, gray background
    - Timestamps (relative: "2 minutes ago")
    - Avatar icons (user vs. character avatar from VectorDB)
  - Message input area:
    - Textarea with auto-expand (max 5 lines)
    - Character counter (**2,000 max** for Gemini 2.5 Flash)
    - Send button (Enter to send, Shift+Enter for newline)
    - **Disabled during polling** (shows "Generating..." status)
    - Rate limit indicator: "X messages left this hour (max 50/hour)"
- [ ] MessageBubble component
  - Props: `message` (role, content, timestamp, token_count), `isPending`
  - Markdown rendering for assistant messages (bold, italic, lists via marked.js)
  - Code block syntax highlighting (highlight.js, nice-to-have)
  - Copy message button (on hover)
  - User messages: plain text only
  - **Token count display** (hover tooltip): "Used X tokens" for cost transparency
- [ ] **PendingMessage component** (for Long Polling UX)
  - Display "Generating..." message while polling
  - Progress indicator (0-100% from poll response)
  - Animated ellipsis: "Thinking..." → "Still thinking..." → "Almost there..."
  - Cancel button (abort polling, discard pending message)
  - Smooth transition to actual message when COMPLETED
- [ ] **Long Polling Integration**:

  ```javascript
  // 1. Submit message
  const response = await fetch(`/api/v1/conversations/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ content: userMessage, scenario_id: scenarioId }),
  });
  const { task_id, status } = await response.json();

  // 2. Poll for completion every 2 seconds
  const pollInterval = setInterval(async () => {
    const pollResponse = await fetch(
      `/api/v1/conversations/${id}/messages/status/${task_id}`
    );
    const { status, progress, message, error } = await pollResponse.json();

    if (status === "COMPLETED") {
      clearInterval(pollInterval);
      // Add message to conversation, enable input
      messages.value.push(message);
      enableInput();
      showBrowserNotification(`${characterName} replied!`);
    } else if (status === "FAILED") {
      clearInterval(pollInterval);
      // Show error toast, re-enable input
      showError(error);
      enableInput();
    } else {
      // Update progress indicator
      updateProgress(progress);
    }
  }, 2000);
  ```

- [ ] **Browser Notification Integration**:
  - Request notification permission on first message send
  - WebSocket connection to `/api/v1/notifications/stream/{userId}` for real-time alerts
  - Show notification when task COMPLETED and user is not on conversation page
  - Notification text: "{character_name} replied to your message!"
  - Click notification → navigate to conversation page
  - Clear notification when user returns to page
- [ ] ConversationStore (Pinia) actions:
  - `loadConversation(conversationId)`
  - `loadMessages(conversationId, page)`
  - **`sendMessageAsync(conversationId, content)`** → returns task_id, starts polling
  - **`pollMessageStatus(conversationId, taskId)`** → polls every 2 seconds, updates UI
  - **`cancelPendingMessage(taskId)`** → stops polling, discards pending message
  - `deleteConversation(conversationId)`
  - **`connectNotificationStream(userId)`** → WebSocket connection for browser notifications
- [ ] Loading states:
  - Skeleton loader for initial conversation load
  - "Loading older messages..." for pagination (scroll to top)
  - **"Generating... (45%)"** progress indicator during polling
  - **Exponential backoff** for failed polls: 2s → 4s → 8s → max 30s
- [ ] Empty state (new conversation):
  - "Start your conversation with {character_name} from VectorDB"
  - Reminder: "You always send the first message"
  - **If this is a forked conversation**: "Continuing from original conversation (**{copied_message_count} messages** copied)"
    - Example: "Continuing from original conversation (6 messages copied)" if parent had 8 messages
    - Example: "Continuing from original conversation (3 messages copied)" if parent had 3 messages
  - Suggested opening questions (3-5 examples from VectorDB character traits)
- [ ] Error handling:
  - Show error toast if message send fails (network error, validation error)
  - **Show error toast if poll fails** (timeout, FAILED status from FastAPI)
  - Retry button for failed messages (re-submit POST request)
  - **Auto-retry polling** 3 times with exponential backoff before showing error
  - **Reconnect WebSocket** notification stream if connection drops
- [ ] Responsive design:
  - Mobile: full-screen chat, fixed header/input
  - Desktop: max-width 900px, centered layout (wider for Gemini's longer responses)
  - Tablet: similar to desktop
- [ ] Accessibility:
  - Keyboard navigation (Tab, Enter)
  - Screen reader support for new messages (aria-live="polite")
  - Focus management (input auto-focus after message sent)
  - Progress indicator announced to screen readers

**Chat Layout with Long Polling**:

```
┌────────────────────────────────────────┐
│ [Back] Hermione in Slytherin  [♥ 5]  │ ← Header
│ Character: Hermione Granger   [📝]    │
│ [🔀 Fork] (only if is_root & !forked) │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────┐     │
│  │ How do you feel about being  │     │ ← User message
│  │ in Slytherin?          (12t) │     │   (token count)
│  └──────────────────────────────┘     │
│                                        │
│     ┌────────────────────────────────┐│
│     │ Generating... (68%)    [Cancel]││ ← Polling indicator
│     │ ⠋ Still thinking...            ││
│     └────────────────────────────────┘│
│                                        │
│     ┌────────────────────────────────┐│
│     │ At first, I was shocked—       ││ ← Assistant
│     │ Slytherin? Me? But I've come   ││   message (prev)
│     │ to appreciate the strategic... ││   (487t)
│     └────────────────────────────────┘│
│                                        │
│  [Loading older messages...]          │ ← Pagination
│                                        │
├────────────────────────────────────────┤
│ ┌────────────────────────────────────┐│
│ │ Type your message...        1850  ││ ← Input area
│ └────────────────────────────────────┘│   (char count)
│ 45 messages left this hour      [Send]│   (rate limit)
└────────────────────────────────────────┘
```

**Technical Notes**:

- Use **setInterval** for Long Polling (2-second intervals)
- **Exponential backoff** for failed polls: 2s → 4s → 8s → max 30s, then show error
- **Clear interval** when component unmounts (prevent memory leaks)
- **WebSocket connection** for browser notifications: `/api/v1/notifications/stream/{userId}`
  - Receive events: `{type: "message_ready", conversation_id: "uuid", character_name: "..."}`
  - Use Reconnecting WebSocket library for auto-reconnect
- **Progress calculation**: Backend returns progress (0-100), frontend displays as percentage
- **Cancel polling**: Send DELETE request to FastAPI `/api/ai/chat/cancel/{taskId}` (optional, nice-to-have)
- **Debounce scroll events** for pagination (load when 100px from top)
- Use `IntersectionObserver` for efficient scroll detection
- **Message ordering**: Sort by created_at ASC (oldest first), append new messages to bottom
- **Character avatar**: Fetch from VectorDB character collection via FastAPI (cache in localStorage)
- **Fork button visibility**: Check conversation.is_root && !conversation.has_been_forked (from API response)
- **Suggested questions**: Query VectorDB via FastAPI for character-specific conversation starters

**Estimated Effort**: 12 hours (increased from 10h for Long Polling + browser notification implementation)

---

## Epic-Level Acceptance Criteria

- [ ] Users can create conversations with AI characters based on scenarios
- [ ] **Long Polling works smoothly** (2-second polling interval, progress indicator 0-100%)
- [ ] Messages persist correctly in database with token counts
- [ ] Mobile responsive design (375px+ width)
- [ ] No message loss (all messages saved even if client disconnects during polling)
- [ ] **Long Polling reconnection works seamlessly** (exponential backoff on errors: 2s → 4s → 8s → max 30s)
- [ ] Token usage tracked accurately for cost monitoring (Gemini 2.5 Flash API via FastAPI)
- [ ] **Browser notifications work** when task COMPLETED and user not on page (WebSocket/SSE integration)

## Dependencies

**Blocks**:

- Epic 5: Scenario Tree Visualization (needs conversation data to visualize)
- Post-MVP analytics (needs conversation metrics)

**Requires**:

- **Epic 0**: Project Setup & Infrastructure (PostgreSQL, VectorDB, Spring Boot, FastAPI, Redis)
- [ ] **Backend: Fork Conversation Endpoint**
  - **POST /api/v1/conversations/{id}/fork** (requires authentication, owner only)
  - Request body: `{target_scenario_id: "uuid"}` (optional, defaults to same scenario)
  - **Validation**:
    - Conversation must be ROOT (is_root = TRUE, parent_conversation_id IS NULL)
    - Conversation must NOT have been forked yet (has_been_forked = FALSE)
    - User must own the conversation (user_id matches authenticated user)
    - Target scenario must exist and not be deleted
  - **Fork Logic**:
    1. Check conversation.is_root && !conversation.has_been_forked
    - If is_root = FALSE → return **403 Forbidden** "Cannot fork: only ROOT conversations can be forked"
    - If has_been_forked = TRUE → return **409 Conflict** "Cannot fork: conversation has already been forked"
    2. Create new conversation:
    - parent_conversation_id = {source conversation id}
    - is_root = FALSE (forked conversations are NOT root)
    - has_been_forked = FALSE (new conversation, not forked yet)
    - scenario_id = {target_scenario_id} (same or different scenario)
    - character_name = {same as source conversation}
    - user_id = {authenticated user}
    3. **Copy messages: min(6, total_message_count)**:
    - Query: `SELECT * FROM messages WHERE conversation_id = {source_id} ORDER BY created_at DESC LIMIT 6`
    - If total < 6: copy ALL messages (e.g., 3 messages → copy all 3)
    - If total ≥ 6: copy last 6 messages (e.g., 8 messages → copy #3-8)
    - Insert copied messages with new conversation_id, same role/content/token_count, new created_at (fork timestamp)
    4. **Update source conversation**:
    - SET has_been_forked = TRUE (prevent re-forking)
    5. Return new conversation with copied_message_count
  - Response (201 Created):
    ```json
    {
      "id": "uuid",
      "scenario_id": "uuid",
      "scenario_title": "...",
      "parent_conversation_id": "uuid",
      "is_root": false,
      "has_been_forked": false,
      "character_name": "Hermione Granger",
      "copied_message_count": 6, // or 3, depending on source
      "message_count": 6,
      "created_at": "2025-11-13T12:00:00Z"
    }
    ```
- [ ] **Frontend: Fork Conversation UI**
  - ForkConversationModal component
  - **Trigger conditions**:
    - Button labeled "🔀 Fork Conversation" in chat header
    - **ONLY visible if** conversation.is_root = TRUE AND conversation.has_been_forked = FALSE
    - **Button disabled** if conversation.is_root = FALSE (with tooltip: "Only ROOT conversations can be forked")
    - **Button disabled** if conversation.has_been_forked = TRUE (with tooltip: "Conversation already forked")
  - Modal content:
    - Header: "Fork this conversation to explore a different path"
    - Message copy preview:
      - "**{copied_count} messages** will be copied to the new conversation"
      - Show actual copied message count: min(6, total)
      - Example: "Total messages: 8 → **6 messages** will be copied (last 6)"
      - Example: "Total messages: 3 → **3 messages** will be copied (all)"
    - Scenario selector (optional):
      - Dropdown: "Continue in same scenario" (default) OR "Switch to different scenario"
      - If different scenario selected: show scenario picker (from Epic 3, Story 3.1)
    - Confirmation text:
      - "Create a fork to continue this conversation from a specific point"
      - "The original conversation will remain unchanged and cannot be forked again"
    - Buttons: "Cancel" | "Fork Conversation" (primary CTA)
  - **API integration**: POST /api/v1/conversations/{id}/fork
  - Success state:
    - Close modal
    - Show success toast: "Conversation forked! {copied_count} messages copied."
    - Navigate to new conversation page (`/conversations/{new_id}`)
  - Error handling:
    - 403 Forbidden → show error toast "Cannot fork: only ROOT conversations can be forked"
    - 409 Conflict → show error toast "Cannot fork: conversation has already been forked"
    - 404 Not Found → show error toast "Conversation not found"
    - 401 Unauthorized → redirect to login
- [ ] **Frontend: Forked Conversation Indicators**
  - In chat header: "🔀 Forked from original" badge (if is_root = FALSE)
  - Click badge → navigate to parent conversation (`/conversations/{parent_conversation_id}`)
  - In conversation list: "🔀 Forked" badge next to forked conversations
  - In empty state: "Continuing from original conversation ({copied_message_count} messages copied)"
  - **Fork button state management**:
    - Check conversation.is_root && !conversation.has_been_forked on page load
    - Disable fork button immediately after successful fork (optimistic update)
    - Update conversation.has_been_forked = TRUE in local state
- [ ] **Backend: Unit Tests**
  - Test fork with 3 messages → verify all 3 copied
  - Test fork with 8 messages → verify last 6 copied
  - Test fork non-ROOT conversation → verify 403 error
  - Test fork already-forked conversation → verify 409 error
  - Test fork with different scenario → verify scenario_id updated
  - Test parent conversation → verify has_been_forked = TRUE
  - Test forked conversation → verify is_root = FALSE, parent_conversation_id set
- [ ] **Frontend: Integration Tests**
  - Fork ROOT conversation → verify navigation to new conversation
  - Attempt to fork forked conversation → verify button disabled
  - Attempt to re-fork ROOT conversation → verify 409 error toast
  - Verify copied message count matches min(6, total) rule

**Fork Flow Example**:

```
Original Conversation (ROOT):
- id: conv-123
- is_root: TRUE
- has_been_forked: FALSE
- message_count: 8
- messages: [msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8]

User clicks "Fork Conversation":
1. POST /api/v1/conversations/conv-123/fork
2. Backend checks: is_root = TRUE ✓, has_been_forked = FALSE ✓
3. Backend creates new conversation:
  - id: conv-456
  - parent_conversation_id: conv-123
  - is_root: FALSE
  - has_been_forked: FALSE
4. Backend copies last 6 messages: msg3, msg4, msg5, msg6, msg7, msg8
5. Backend updates conv-123: has_been_forked = TRUE
6. Response: {id: "conv-456", copied_message_count: 6, ...}
7. Frontend navigates to /conversations/conv-456
8. Empty state shows: "Continuing from original conversation (6 messages copied)"
9. User sees msg3-msg8 in conversation history
10. User can continue conversation from this fork point
11. Original conversation (conv-123) fork button is now DISABLED

Attempt to fork conv-123 again:
- POST /api/v1/conversations/conv-123/fork
- Backend checks: has_been_forked = TRUE ✗
- Response: 409 Conflict "Cannot fork: conversation has already been forked"

Attempt to fork conv-456 (forked conversation):
- POST /api/v1/conversations/conv-456/fork
- Backend checks: is_root = FALSE ✗
- Response: 403 Forbidden "Cannot fork: only ROOT conversations can be forked"
```

**Technical Notes**:

- **Database transaction**: Ensure fork creation + message copy + parent update are atomic
- **Message copy query**: `INSERT INTO messages (conversation_id, role, content, token_count, created_at) SELECT $1, role, content, token_count, NOW() FROM (SELECT * FROM messages WHERE conversation_id = $2 ORDER BY created_at DESC LIMIT 6) AS last_messages ORDER BY created_at ASC;`
- **Frontend state sync**: After fork, update parent conversation in ConversationStore to set has_been_forked = TRUE (optimistic update)
- **Scenario switching**: If user selects different scenario, verify character_name exists in new scenario's VectorDB character collection
- **Fork button visibility**: Use computed property in Vue: `canFork = conversation.is_root && !conversation.has_been_forked`
- **Error messages**: Clear, user-friendly explanations for 403/409 errors

**Estimated Effort**: 10 hours

---

- Markdown rendering: use `marked.js` or `markdown-it`
- Store draft message in localStorage (prevent data loss on refresh)

**Estimated Effort**: 12 hours

---

## Story Summary

- [ ] Fork conversation backend logic
  - POST /api/v1/conversations/{id}/fork endpoint (requires authentication)
  - **Validation 1**: Check conversation.parent_conversation_id IS NULL (return 403 Forbidden if trying to fork a forked conversation)
  - **Validation 2**: Check conversation.has_been_forked = false (return 409 Conflict if root already forked)
  - Request body: Empty `{}` (no message selection - always copies most recent messages)
  - Create new conversation with:
    - parent_conversation_id = original conversation ID
    - scenario_id = same as parent
    - character_name = same as parent
    - **Message Copy Logic**: Copy min(6, total_message_count) most recent messages
      - If original has ≥6 messages → copy last 6 messages
      - If original has <6 messages → copy ALL messages
      - Example: Original has 3 messages → copy all 3
      - Example: Original has 10 messages → copy last 6 (messages #5-10)
    - fork_message_count = number of messages actually copied
  - Update parent conversation: set has_been_forked = true (atomic operation)
  - Return new conversation ID with copied message count
- [ ] ForkConversationButton in conversation header
  - **Only show if**: conversation.parent_conversation_id IS NULL (root conversations only)
  - Show "Fork Conversation" button if conversation.has_been_forked = false
  - Disabled state if conversation.has_been_forked = true (tooltip: "This conversation has already been forked")
  - If conversation is a fork (parent_conversation_id IS NOT NULL): hide button entirely (show badge: "Forked conversation - cannot fork again")
  - Click → opens ForkConversationModal
  - Button placement in header next to like/memo buttons
- [ ] ForkConversationModal component
  - Shows preview of messages that will be copied:
    - If conversation has ≥6 messages: "Last 6 messages will be preserved"
    - If conversation has <6 messages: "All {count} messages will be preserved"
  - Display the exact messages that will be copied (scrollable preview)
  - No message selection - copy logic is automatic (most recent 6 or all if fewer)
  - Input: optional "Fork description" (why you're forking)
  - Warning: "Original conversations can only be forked once. Forked conversations cannot be forked again."
  - "Create Fork" button (disabled if parent already forked)
  - On success: navigate to new conversation showing "{count} messages copied from original conversation"
- [ ] Conversation breadcrumb navigation
  - If conversation has parent_conversation_id (is a fork):
    - Show breadcrumb: "Forked from [Parent Conversation Title]"
    - Show badge: "This is a forked conversation (cannot be forked again)"
    - Click breadcrumb → navigate to parent conversation
  - If conversation is root (parent_conversation_id IS NULL):
    - If has_been_forked = true: Show "Forked" badge, click → navigate to child
    - If has_been_forked = false: Show "Fork" button (can be forked once)
- [ ] ConversationForkTree component (simple version for MVP)
  - Display parent conversation link at top
  - Display child forks below current conversation
  - Each fork shows: first user message after fork, message count, created date
  - Click fork → navigate to that conversation
- [ ] ConversationStore actions:
  - `forkConversation(conversationId, forkAtMessageId, description)`
  - `getConversationForks(conversationId)` (get child forks)
- [ ] Analytics:
  - Track fork count per conversation (denormalized column)
  - Track which messages are most forked (future feature)
- [ ] Unit tests for fork logic
- [ ] Integration test for fork endpoint

**Fork Flow**:

```
User reading ROOT conversation (parent_conversation_id IS NULL):
1. Sees "Fork Conversation" button in header (if not already forked)
2. Clicks button
3. Modal opens showing: "The most recent 6 messages will be preserved"
4. User sees preview of 6 messages that will be copied
5. User optionally adds fork description
6. User clicks "Create Fork"
7. Backend validates:
   - Check parent.parent_conversation_id IS NULL ✓ (is root)
   - Check parent.has_been_forked = false ✓ (not forked yet)
8. New conversation created with most recent 6 messages
9. Parent conversation marked as has_been_forked = true
10. User redirected to new FORKED conversation
11. Forked conversation shows "Forked from [Parent]" badge
12. Forked conversation has NO fork button (cannot fork again)
```

**Attempting to Fork a FORKED conversation**:

```
User on forked conversation (parent_conversation_id IS NOT NULL):
1. No "Fork Conversation" button visible
2. Badge shows: "This is a forked conversation"
3. Message: "Only original conversations can be forked"
```

**API Example**:

**POST /api/v1/conversations/{id}/fork**

```json
Request:
{
  "description": "Explore cunning vs. ambition distinction"
}

Response (201 Created):
{
  "id": "new-uuid",
  "parent_conversation_id": "original-uuid",
  "scenario_id": "uuid",
  "character_name": "Hermione Granger",
  "message_count": 6,
  "fork_description": "Explore cunning vs. ambition distinction",
  "created_at": "2025-11-13T11:00:00Z",
  "can_be_forked": false  // Forked conversations cannot be forked again
}

Error Response (403 Forbidden - trying to fork a forked conversation):
{
  "error": "Cannot fork a forked conversation",
  "message": "Only original conversations can be forked. This conversation was already forked from another conversation.",
  "parent_conversation_id": "parent-uuid"
}

Error Response (409 Conflict - root already forked):
{
  "error": "Conversation has already been forked",
  "message": "This original conversation has already been forked once",
  "forked_conversation_id": "existing-fork-uuid"
}
```

**Technical Notes**:

- Fork operation is transactional: copy 6 messages + create conversation + update parent flag
- Only copy most recent 6 messages (or all if conversation has <6 messages)
- Use bulk insert for message copying (efficient operation)
- Add index on parent_conversation_id for fast child fork queries
- Add index on has_been_forked for fast fork validation
- **Database constraint**: `CHECK (parent_conversation_id IS NULL OR has_been_forked = FALSE)` (forked conversations cannot be re-forked)
- **Application validation order**:
  1. Check if conversation.parent_conversation_id IS NOT NULL → 403 Forbidden
  2. Check if conversation.has_been_forked = true → 409 Conflict
  3. Proceed with fork creation

**Estimated Effort**: 8 hours

---

## Epic-Level Acceptance Criteria

- [ ] Users can create conversations with AI characters based on scenarios
- [ ] **Long Polling works smoothly** (2-second polling interval, progress indicator 0-100%)
- [ ] Messages persist correctly in database with token counts
- [ ] Mobile responsive design (375px+ width)
- [ ] No message loss (all messages saved even if client disconnects during polling)
- [ ] **Long Polling reconnection works seamlessly** (exponential backoff on errors: 2s → 4s → 8s → max 30s)
- [ ] Token usage tracked accurately for cost monitoring (Gemini 2.5 Flash API via FastAPI)
- [ ] **Browser notifications work** when task COMPLETED and user not on page (WebSocket/SSE integration)

## Dependencies

**Blocks**:

- Epic 5: Scenario Tree Visualization (needs conversation data to visualize)
- Post-MVP analytics (needs conversation metrics)

**Requires**:

- **Epic 0**: Project Setup & Infrastructure (PostgreSQL, VectorDB, Spring Boot, FastAPI, Redis)
- **Epic 1**: What If Scenario Foundation (scenarios must exist with vectordb_passage_ids[])
- **Epic 2**: AI Character Adaptation (prompt generation, context window management via FastAPI + Gemini)
- **Epic 6**: User Authentication (JWT for authenticated endpoints)
- **FastAPI AI Service**: Must be deployed and accessible at Port 8000
- **Gemini 2.5 Flash API**: API key configured in FastAPI environment variables
- **VectorDB (ChromaDB dev / Pinecone prod)**: Seeded with character, passage, event, location, theme collections
- **Redis**: For Long Polling task storage (600-second TTL) and conversation caching (5-minute TTL)

## Success Metrics

**Technical Metrics**:

- **Long Polling task status check latency** < 50ms (p95) - fast status polling
- Message persistence success rate > 99.9%
- **Average conversation length** > 20 messages (increased from 10 for Gemini's larger context window)
- Token counting accuracy > 99% (Gemini Tokenizer API via FastAPI)
- Search response time < 200ms (p95)
- **Long Polling reconnection success rate** > 95% (exponential backoff handles transient failures)
- **Gemini API p95 latency** < 3 seconds (FastAPI → Gemini call)

**User Metrics** (Phase 1 - 3 months):

- **90%+ users** who create scenario start at least one conversation (increased from 80% for Gemini)
- **70%+ conversations** exceed 20 messages (increased from 60% for Gemini's better quality)
- **40%+ conversations** get forked at least once (increased from 30% due to ROOT-only constraint clarity)
- 40%+ users browse public conversations before creating their own
- **30%+ conversation completion rate** (user says goodbye or clear ending, increased from 20% for Gemini)

## Cost Monitoring

**Gemini API Cost Estimation** (via FastAPI):

- Gemini 2.5 Flash Input: $0.075 per 1M tokens (prompt tokens)
- Gemini 2.5 Flash Output: $0.30 per 1M tokens (completion tokens)

**Example Conversation Cost** (updated for Gemini 2.5 Flash):

- Average conversation: **50 messages** (25 user, 25 assistant) - longer due to Gemini quality
- Average context per request:
  - Scenario prompt (VectorDB passage context): 1,500 tokens (increased from 800 for richer context)
  - Last 50 messages (from Story 2.2): ~10,000 tokens (Gemini can handle 1M input)
  - VectorDB character/event context: 2,000 tokens
  - **Total input per request**: ~13,500 tokens
- Average assistant response: 400 output tokens (increased from 150 for Gemini's richer responses)
- Cost per assistant message:
  - Input: 13,500 tokens × $0.075 / 1M = $0.0010125
  - Output: 400 tokens × $0.30 / 1M = $0.00012
  - Total: ~$0.001133 per message
- Cost per 50-message conversation: $0.001133 × 25 = **$0.0283** (~$0.03)

**Monthly Cost Projection** (MVP - 1,000 active users):

- Assume 5 conversations per user per month
- Total conversations: 5,000
- Total cost: 5,000 × $0.03 = **$150/month** (Gemini API costs only)
- Additional costs:
  - Railway hosting (Spring Boot + FastAPI + PostgreSQL + Redis): ~$50/month
  - VectorDB (Pinecone free tier): $0/month (dev), ~$70/month (prod with 100K vectors)
  - **Total infrastructure cost**: ~$220-270/month for 1,000 users

**Cost Optimization Strategies**:

- Cache common scenario prompts in FastAPI Redis (reduce duplicate Gemini API calls)
- Keep conversation context to **last 50 messages** (leverages Gemini's 1M context window efficiently)
- Implement **rate limiting: 50 messages/hour per user** (prevents abuse, increased from 30)
- Monitor token usage per user and implement soft limits (flag users >1,000 messages/month)
- Use Gemini 2.5 Flash (cheapest Gemini model) for MVP, consider Gemini Pro only if needed
- VectorDB caching: Cache character/passage embeddings in FastAPI memory (reduce VectorDB queries)

## Risk Mitigation

**Risk 1: Gemini API latency (network overhead to Google Cloud)**

- Mitigation: Use **Long Polling with progress indicators** (user sees 0-100% progress during Gemini call)
- Mitigation: Use Gemini 2.5 Flash (fastest model in Gemini family, ~2-3s response time)
- Mitigation: Show user "AI is thinking..." indicator during FastAPI task processing
- Mitigation: FastAPI Redis caching layer for common prompts (reduce API calls by ~30%)
- Mitigation: **Background task processing** (Celery workers) ensures Spring Boot doesn't block during Gemini calls

**Risk 2: Message loss during Long Polling disconnect**

- Mitigation: Save user message immediately in Spring Boot (before calling FastAPI) - user message always persists
- Mitigation: Use database transaction (user message + assistant response) - atomic save
- Mitigation: Client-side **exponential backoff retry logic** (2s → 4s → 8s → max 30s) handles transient network failures
- Mitigation: Store partial assistant response in Redis task (if Gemini returns partial result, save it for later retrieval)
- Mitigation: **Browser notification** alerts user when task COMPLETED even if they navigate away

**Risk 3: Conversation context explosion (>1M tokens)**

- Mitigation: Hard limit to **last 50 messages** (from Story 2.2) prevents context explosion (~10-15K tokens)
- Mitigation: Re-inject scenario context with each request (always fresh, no stale context)
- Mitigation: 50-message context provides ~10,000 token history (well under Gemini's 1M limit)
- Mitigation: No summarization needed until conversations exceed ~70 messages (rare in MVP)
- Mitigation: **Gemini Tokenizer API** provides accurate token counting before submission

**Risk 4: Spam/abuse (users sending excessive messages)**

- Mitigation: **Rate limiting: 50 messages/hour per user** (increased from 30 for Gemini's better quality)
- Mitigation: Token cost tracking per user (flag users with >$10/month API usage)
- Mitigation: Conversation cooldown (30s between messages - Phase 2)
- Mitigation: Anomaly detection (flag users sending >100 messages/day, auto-suspend >200/day)
- Mitigation: **Long Polling task queue** (max 10 concurrent tasks per user) prevents queue flooding

**Risk 5: Poor character consistency across long conversations (50+ messages)**

- Mitigation: Periodic scenario context re-injection every 20 turns (Story 2.2) - keeps character grounded
- Mitigation: **VectorDB character refresh** every 20 turns (fetch latest character traits/relationships)
- Mitigation: Temperature optimization per scenario type (Story 2.3) - 0.6-0.8 for consistent characters
- Mitigation: User feedback mechanism ("Character broke timeline" report button) - collect quality data
- Mitigation: Test with 50+ message conversations before launch (validate character consistency)

**Risk 6: VectorDB query failures (ChromaDB/Pinecone downtime)**

- Mitigation: **Circuit breaker pattern** in FastAPI (fail after 3 consecutive VectorDB errors)
- Mitigation: Fallback to basic character data from PostgreSQL (character_name from conversations table)
- Mitigation: Cache VectorDB results in FastAPI Redis (5-minute TTL) - reduce dependency on VectorDB uptime
- Mitigation: Monitor VectorDB health endpoint (Pinecone status page)

**Risk 7: Gemini API rate limits (quota exhaustion)**

- Mitigation: Implement **exponential backoff + retry** in FastAPI (429 Too Many Requests → wait 60s → retry)
- Mitigation: Monitor Gemini API quota usage (Google Cloud Console alerts)
- Mitigation: Request quota increase before launch (Google Cloud support ticket)
- Mitigation: Implement user-facing "API quota exceeded" error with retry button

## Technical Debt Decisions

**Accepted Debt** (to be addressed post-MVP):

- **No conversation summarization** (send last 50 messages until Gemini context limit reached at ~70 messages)
- **No multi-character conversations** (1-on-1 only for MVP, multi-character in Phase 2)
- No conversation templates (pre-filled opening messages)
- No conversation sharing with custom URLs (use generic share)
- No conversation export (download as text/JSON)
- No voice input/output (text only, voice in Phase 2)
- Simple rate limiting (no sophisticated abuse detection beyond basic limits)
- **No conversation depth > 1** (ROOT → fork only, no re-forking chains)

**Won't Build** (architectural decisions):

- **WebSocket instead of Long Polling** (Long Polling simpler, HTTP/2 compatible, easier error handling)
- **SSE instead of Long Polling** (Long Polling chosen for simplicity and predictable polling intervals)
- Conversation threading (one linear conversation per fork)
- Conversation merging (only forking, no merging branches)
- Real-time collaborative editing (multiple users editing same conversation)

## Testing Strategy

**Unit Tests** (Spring Boot + FastAPI):

- **ConversationService** (Spring Boot):
  - createConversation(), getConversation(), deleteConversation()
  - forkConversation() - validate ROOT-only, min(6, total) message copy, is_root flag updates
  - findRootConversations(), findLastNMessages()
- **MessageService** (Spring Boot):
  - saveMessage(), retrieveMessages(), countTokens()
  - saveUserAndAssistantMessages() - atomic transaction
- **FastAPIClient** (Spring Boot):
  - callFastAPIGenerateChat() - mock FastAPI responses
  - retry logic on 500/503 errors
  - error handling (404, 429, 500)
- **AIService** (FastAPI):
  - generate_chat() - mock Gemini API responses
  - build_prompt() - validate scenario context injection
  - count_tokens() - test Gemini Tokenizer API
- **VectorDBService** (FastAPI):
  - query_characters(), query_passages(), query_events()
  - circuit breaker pattern (fail after 3 errors)
- Fork logic: copy messages, create child conversation, update parent.has_been_forked flag

**Integration Tests** (Spring Boot + H2 in-memory + mock FastAPI):

- POST /api/v1/conversations → creates conversation + increments scenario.conversation_count
- POST /api/v1/conversations/{id}/messages → saves user message + calls FastAPI + polls task status + saves assistant message
- **Long Polling flow**: submit message → get task_id → poll /status/{taskId} every 2s → PENDING → COMPLETED → message saved
- Fork endpoint: POST /conversations/{id}/fork → creates child with parent messages copied (min(6, total) rule)
- Browser notification: WebSocket sends alert when task COMPLETED

**E2E Tests** (Playwright + real FastAPI + Gemini API mocked):

- User journey: create scenario → start conversation → send 5 messages → messages persist → verify Long Polling progress indicators
- **Long Polling**: send message → poll every 2s → receive COMPLETED status → full message saved
- Fork: create conversation → send 8 messages → fork at ROOT → verify child has min(6, 8) = 6 messages copied
- **ROOT-only fork validation**: create conversation → fork → try to fork child → verify 403 Forbidden error
- Browse: create 10 conversations → visit /conversations → see all 10 → filter by character → see subset
- **Browser notification**: send message → navigate away → verify notification alert when task COMPLETED

**Load Tests** (k6):

- Concurrent Long Polling (100 simultaneous task status polls)
- FastAPI/Gemini API capacity (max 50 concurrent Gemini requests before rate limit)
- Database transaction throughput (message save performance: >1,000 messages/sec)
- Redis task storage (600-second TTL, 10,000 tasks stored)
- VectorDB query load (100 concurrent character searches)

**Security Tests**:

- User can only delete their own conversations (403 on other user's conversation)
- Invalid conversation ID returns 404
- Message content XSS prevention (sanitization in Spring Boot)
- **Fork validation**: non-ROOT conversation fork returns 403, already-forked conversation returns 409
- Rate limit enforcement: 51st message/hour returns 429 Too Many Requests

## Open Questions

1. **Q**: Should conversations be public by default or private?
   **A**: Public by default (like Twitter). Privacy settings in Phase 2.

2. **Q**: Can users edit/delete their messages after sending?
   **A**: No editing (preserves conversation integrity). Deletion soft-deletes message (shows "[deleted]").

3. **Q**: Maximum conversation length (number of messages)?
   **A**: **No hard limit for MVP**. Context window uses **last 50 messages** (Gemini can handle 1M tokens), so conversations can grow to ~70 messages before context summarization needed (Phase 2). Add soft limit (100 messages) in Phase 2 for UX.

4. **Q**: Should we show "Character is typing..." indicator?
   **A**: Yes, show during **Long Polling task processing** (progress indicator 0-100%) for better UX.

5. **Q**: Can users fork other users' conversations?
   **A**: Yes, **public ROOT conversations are forkable** (is_root = TRUE, has_been_forked = FALSE). Each ROOT conversation can only be forked **one time** (max depth 1).

6. **Q**: Should forked conversations inherit likes from parent?
   **A**: No, each conversation has independent like count.

7. **Q**: What happens if Gemini API fails during message generation?
   **A**: FastAPI sets task status to FAILED with error message. User sees error in UI, can retry. User message is already saved in PostgreSQL (no data loss).

8. **Q**: How long are Long Polling task statuses stored in Redis?
   **A**: **600 seconds (10 minutes)** TTL. After 10 minutes, task_id expires. User sees "Task expired" error if they poll after 10 minutes.

## Definition of Done

- [ ] All 5 stories completed with acceptance criteria met
- [ ] Users can create conversations and chat with AI characters via **Gemini 2.5 Flash** (FastAPI integration)
- [ ] **Long Polling works smoothly** (2-second polling interval, progress indicator, exponential backoff on errors)
- [ ] Messages persist in database with accurate token counts (Gemini Tokenizer API)
- [ ] **Conversation forking creates independent branches** (ROOT-only, max depth 1, min(6, total) message copy rule enforced)
- [ ] Browse page displays and filters conversations correctly (VectorDB character search via FastAPI)
- [ ] Unit tests >80% coverage on services (Spring Boot + FastAPI)
- [ ] Integration tests passing for all conversation endpoints (Long Polling flow validated)
- [ ] E2E test: complete conversation flow (create → chat → Long Polling → fork → ROOT-only validation)
- [ ] Load test: **100 concurrent Long Polling task status checks** without errors
- [ ] **FastAPI/Gemini API capacity handling tested** (rate limits work, 50 concurrent requests, 429 error handling)
- [ ] Mobile responsive design verified on 375px+ width
- [ ] **Long Polling reconnection tested** (disconnect → exponential backoff → reconnect → resume polling)
- [ ] **Cost monitoring dashboard shows Gemini token usage** per conversation (Spring Boot Admin or custom dashboard)
- [ ] Code review completed, no P0/P1 security issues
- [ ] Deployed to Railway staging, smoke tested with real Gemini conversations (5+ messages each)
- [ ] **Browser notification tested** (WebSocket/SSE connection works, alerts on task COMPLETED)
- [ ] **VectorDB integration tested** (character/passage queries via FastAPI, circuit breaker works)

---

**Epic Owner**: Backend Lead + Frontend Lead (joint ownership)

**Start Date**: Week 2, Day 3 of MVP development

**Target Completion**: Week 2, Day 5 (2 working days)

**Estimated Total Effort**: **34 hours**

**Breakdown**:

- Story 4.1: 10 hours (data model + fork constraints)
- Story 4.2: 12 hours (Long Polling + Gemini integration + browser notifications)
- Story 4.3: 12 hours (Long Polling UI + progress indicators + notifications)

**Priority**: CRITICAL - Core user value, enables meaningful exploration of What If scenarios with Gemini 2.5 Flash
