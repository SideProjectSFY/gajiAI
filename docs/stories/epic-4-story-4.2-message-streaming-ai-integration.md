# Story 4.2: Message Streaming & AI Integration

**Epic**: Epic 4 - Conversation System  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 14 hours

## Description

Implement real-time message streaming from FastAPI AI service to Vue.js frontend using **Gemini 2.5 Flash Streaming API** with **Long Polling** for AI responses.

## Dependencies

**Blocks**:

- Story 4.3: Conversation Forking UI (needs working chat before fork UI)
- Epic 5 stories (tree visualization needs completed conversations)

**Requires**:

- Story 0.2: FastAPI AI Service Setup
- Story 0.5: Docker Configuration (inter-service communication)
- Story 4.1: Conversation Data Model (stores messages)
- Story 2.1: Scenario-to-Prompt Engine (generates adapted prompts)

## Acceptance Criteria

- [ ] POST /api/conversations/{id}/messages endpoint in Spring Boot accepts user message, returns 202 Accepted with task_id
- [ ] **Long Polling Architecture**:
  - Spring Boot creates async task, immediately returns task_id
  - Frontend polls GET /api/tasks/{task_id} every 2 seconds
  - Task returns: {status: "processing"|"completed"|"failed", chunks: [], final_message: null|Message}
- [ ] Spring Boot asynchronously calls FastAPI `/api/ai/generate-stream` endpoint with:
  - scenario_id (from Story 2.1: Scenario-to-Prompt Engine)
  - conversation_id (from Story 2.2: Context Window Manager)
  - user_message
- [ ] FastAPI uses **Gemini 2.5 Flash Streaming API** (generate_content_stream)
- [ ] FastAPI streams response chunks back to Spring Boot via HTTP chunked transfer
- [ ] Spring Boot stores chunks in **Redis** (task_id key, TTL 600s)
- [ ] Vue.js ChatInterface polls task endpoint, displays typing animation as chunks accumulate
- [ ] Final complete message saved to `messages` table after streaming completes
- [ ] **Error handling**:
  - Gemini API timeout: 60s limit (retry 3 times with exponential backoff)
  - Task cleanup: Redis TTL 600s (10 minutes)
  - Network failure: Frontend shows reconnection UI
- [ ] **Rate limiting**: 10 messages/min per user (Spring Boot tier)
- [ ] **Context window**: Uses Story 2.2 ContextWindowManager (1M token limit, full history)
- [ ] **Performance**:
  - First chunk < 3s
  - Complete response < 20s average
  - Polling interval: 2 seconds (reduces server load vs WebSocket)
- [ ] Integration tests for full message flow with Gemini API
- [ ] Unit tests >85% coverage

## Technical Notes

**Long Polling Architecture with Gemini 2.5 Flash**:

```
1. User sends message via Vue.js → Spring Boot POST /api/conversations/{id}/messages
2. Spring Boot:
   - Saves user message to DB
   - Creates async task (UUID)
   - Returns 202 Accepted: {task_id: "uuid", status: "processing"}
3. Frontend starts polling: GET /api/tasks/{task_id} every 2 seconds
4. Spring Boot (async worker):
   - Calls Story 2.2 ContextWindowManager to build context
   - Calls FastAPI POST /api/ai/generate-stream with:
     - scenario_id
     - conversation_id
     - user_message
5. FastAPI:
   - Uses Story 2.1 PromptAdapter for system_instruction
   - Uses Story 2.2 build_context for messages[]
   - Calls Gemini 2.5 Flash generate_content_stream()
   - Streams chunks back to Spring Boot via HTTP chunked transfer
6. Spring Boot (async worker):
   - Receives chunks from FastAPI
   - Stores chunks in Redis: SET task:{task_id} {chunks: [], status: "processing"} EX 600
   - Updates Redis on each chunk arrival
7. Frontend polling:
   - GET /api/tasks/{task_id} returns current chunks[]
   - Vue.js renders new chunks with typing animation
   - Polling continues until status: "completed" or "failed"
8. Spring Boot (on completion):
   - Saves final assistant message to DB
   - Updates Redis: {status: "completed", final_message: Message}
   - Deletes Redis key after 600s (cleanup)
```

**Why Long Polling instead of WebSocket/SSE?**:

- Simpler implementation (no persistent connection management)
- Better compatibility (works through firewalls/proxies)
- Easier to scale horizontally (stateless, Redis-backed)
- Lower server resource usage (2-second intervals vs constant connections)
- Spring Boot WebFlux not required (can use standard Spring MVC)

**Spring Boot Implementation**:

```java
@RestController
@RequestMapping("/api/conversations")
public class ConversationController {

    @Autowired
    private AsyncTaskService asyncTaskService;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @PostMapping("/{conversationId}/messages")
    public ResponseEntity<TaskResponse> sendMessage(
        @PathVariable String conversationId,
        @RequestBody SendMessageRequest request,
        @AuthenticationPrincipal User user
    ) {
        // Save user message to DB
        Message userMessage = messageRepository.save(
            Message.builder()
                .conversationId(conversationId)
                .userId(user.getId())
                .role("user")
                .content(request.getContent())
                .build()
        );

        // Create async task
        String taskId = UUID.randomUUID().toString();

        // Store initial task state in Redis
        TaskState initialState = TaskState.builder()
            .status("processing")
            .chunks(new ArrayList<>())
            .build();
        redisTemplate.opsForValue().set(
            "task:" + taskId,
            initialState,
            Duration.ofSeconds(600)  // 10 min TTL
        );

        // Submit async task
        asyncTaskService.processAIResponse(
            taskId,
            conversationId,
            userMessage.getId()
        );

        return ResponseEntity.accepted()
            .body(TaskResponse.builder()
                .taskId(taskId)
                .status("processing")
                .build()
            );
    }

    @GetMapping("/tasks/{taskId}")
    public ResponseEntity<TaskState> getTaskState(@PathVariable String taskId) {
        String redisKey = "task:" + taskId;
        TaskState state = (TaskState) redisTemplate.opsForValue().get(redisKey);

        if (state == null) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok(state);
    }
}
```

**AsyncTaskService (Spring Boot)**:

```java
@Service
public class AsyncTaskService {

    @Autowired
    private WebClient fastApiClient;  // WebClient to FastAPI

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private MessageRepository messageRepository;

    @Async("taskExecutor")
    public CompletableFuture<Void> processAIResponse(
        String taskId,
        String conversationId,
        String userMessageId
    ) {
        String redisKey = "task:" + taskId;

        try {
            // Call FastAPI stream endpoint
            Flux<String> chunks = fastApiClient.post()
                .uri("/api/ai/generate-stream")
                .bodyValue(Map.of(
                    "conversation_id", conversationId,
                    "user_message_id", userMessageId
                ))
                .retrieve()
                .bodyToFlux(String.class);  // Receives chunked HTTP response

            StringBuilder fullResponse = new StringBuilder();

            // Process chunks as they arrive
            chunks.doOnNext(chunk -> {
                fullResponse.append(chunk);

                // Update Redis with new chunk
                TaskState state = (TaskState) redisTemplate.opsForValue().get(redisKey);
                state.getChunks().add(chunk);
                redisTemplate.opsForValue().set(redisKey, state, Duration.ofSeconds(600));
            })
            .doOnComplete(() -> {
                // Save final message to DB
                Message assistantMessage = messageRepository.save(
                    Message.builder()
                        .conversationId(conversationId)
                        .role("assistant")
                        .content(fullResponse.toString())
                        .build()
                );

                // Mark task as completed
                TaskState finalState = TaskState.builder()
                    .status("completed")
                    .chunks(new ArrayList<>())  // Clear chunks to save Redis memory
                    .finalMessage(assistantMessage)
                    .build();
                redisTemplate.opsForValue().set(redisKey, finalState, Duration.ofSeconds(600));
            })
            .doOnError(error -> {
                // Mark task as failed
                TaskState errorState = TaskState.builder()
                    .status("failed")
                    .error(error.getMessage())
                    .build();
                redisTemplate.opsForValue().set(redisKey, errorState, Duration.ofSeconds(600));
            })
            .blockLast();  // Block until stream completes

        } catch (Exception e) {
            // Handle errors
            TaskState errorState = TaskState.builder()
                .status("failed")
                .error(e.getMessage())
                .build();
            redisTemplate.opsForValue().set(redisKey, errorState, Duration.ofSeconds(600));
        }

        return CompletableFuture.completedFuture(null);
    }
}
```

**FastAPI Streaming Endpoint**:

```python
from google import generativeai as genai
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

@router.post("/api/ai/generate-stream")
async def generate_stream(request: GenerateStreamRequest):
    """
    Stream Gemini 2.5 Flash response chunks
    Returns: HTTP chunked transfer encoding
    """
    # Get context from Story 2.2
    context_manager = ContextWindowManager()
    context = await context_manager.build_context(
        request.scenario_id,
        request.conversation_id
    )

    # Configure Gemini model
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        system_instruction=context['system_instruction']
    )

    # Build Gemini contents array (message history + user message)
    contents = [
        {"role": msg["role"], "parts": [msg["content"]]}
        for msg in context["messages"]
    ]
    contents.append({
        "role": "user",
        "parts": [request.user_message]
    })

    async def stream_generator():
        """Generator for HTTP chunked response"""
        try:
            # Gemini streaming with retry logic
            for attempt in range(3):
                try:
                    response = model.generate_content(
                        contents,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.8,
                            max_output_tokens=8192
                        ),
                        stream=True  # Enable streaming
                    )

                    # Yield chunks as they arrive
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text

                    break  # Success, exit retry loop

                except Exception as e:
                    if attempt < 2:  # Retry
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                        continue
                    else:
                        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain"
    )
```

**Vue.js Frontend (Long Polling)**:

```vue
<script setup>
import { ref, onUnmounted } from "vue";

const messages = ref([]);
const currentTyping = ref("");
const isTyping = ref(false);

let pollingInterval = null;

async function sendMessage(content) {
  // Add user message to UI immediately
  messages.value.push({
    role: "user",
    content: content,
  });

  // Send to backend
  const response = await fetch(
    `/api/conversations/${conversationId}/messages`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    }
  );

  const { task_id } = await response.json();

  // Start polling
  startPolling(task_id);
}

function startPolling(taskId) {
  isTyping.value = true;
  currentTyping.value = "";
  let lastChunkCount = 0;

  pollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`);
      const taskState = await response.json();

      // Render new chunks
      if (taskState.chunks.length > lastChunkCount) {
        const newChunks = taskState.chunks.slice(lastChunkCount);
        newChunks.forEach((chunk) => {
          currentTyping.value += chunk;
        });
        lastChunkCount = taskState.chunks.length;
      }

      // Check completion
      if (taskState.status === "completed") {
        isTyping.value = false;
        messages.value.push({
          role: "assistant",
          content: taskState.final_message.content,
        });
        currentTyping.value = "";
        clearInterval(pollingInterval);
      } else if (taskState.status === "failed") {
        isTyping.value = false;
        alert("AI response failed: " + taskState.error);
        clearInterval(pollingInterval);
      }
    } catch (error) {
      console.error("Polling error:", error);
    }
  }, 2000); // Poll every 2 seconds
}

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
});
</script>

<template>
  <div class="chat-interface">
    <div v-for="msg in messages" :key="msg.id" class="message">
      <div :class="msg.role">{{ msg.content }}</div>
    </div>
    <div v-if="isTyping" class="typing-indicator">
      {{ currentTyping }}<span class="cursor">|</span>
    </div>
  </div>
</template>
```

**Redis Task State Schema**:

```json
{
  "status": "processing" | "completed" | "failed",
  "chunks": ["chunk1", "chunk2", "..."],
  "final_message": {
    "id": "msg-uuid",
    "role": "assistant",
    "content": "full response text",
    "created_at": "2025-11-15T10:30:00Z"
  },
  "error": null | "error message"
}
```

**Performance Optimization**:

- **Redis TTL**: 600s (10 minutes) - auto-cleanup old tasks
- **Polling Interval**: 2 seconds - balance between responsiveness and server load
- **Chunk Batching**: Frontend renders all accumulated chunks on each poll (smooth animation)
- **Task Cleanup**: Redis auto-expires, no manual cleanup needed

**Cost Analysis** (Gemini 2.5 Flash):

- Average conversation: 5K input tokens + 1K output tokens
- Cost per message: (5K × $0.075/1M) + (1K × $0.30/1M) = $0.000675
- Monthly cost (10,000 messages): $6.75
- With Story 2.2 context optimization: ~$3.38/month (50% reduction)

## QA Checklist

### Functional Testing

- [ ] Send user message → receives task_id in 202 Accepted response
- [ ] Polling GET /api/tasks/{task_id} returns chunks[] as they accumulate
- [ ] Full conversation context included via Story 2.2 ContextWindowManager
- [ ] Typing animation displays smoothly in UI as chunks arrive
- [ ] Final message saved to database correctly after completion
- [ ] Error message shown if Gemini API timeout (after 3 retries)
- [ ] Task state cleaned up after 600s (Redis TTL)

### Streaming Quality

- [ ] First chunk arrives < 3s
- [ ] Complete response < 20s average
- [ ] No duplicate chunks in Redis task state
- [ ] Chunks render smoothly without visual glitches
- [ ] Polling continues until status: "completed" or "failed"

### Long Polling Performance

- [ ] Polling interval 2 seconds (not faster, to reduce server load)
- [ ] Frontend handles task not found (404) gracefully
- [ ] Multiple concurrent polling clients supported (10+ users)
- [ ] Redis memory usage reasonable (<1MB per active task)
- [ ] Task cleanup after completion (Redis auto-expire)

### Context Window Validation (Story 2.2)

- [ ] Context built using Story 2.2 ContextWindowManager
- [ ] Full conversation history included (up to 1M tokens)
- [ ] Optimization applied for >10K token conversations
- [ ] Character reminders injected every 50 messages
- [ ] Token count stays within 1M input limit

### Performance

- [ ] Concurrent streaming for 10 users simultaneously
- [ ] Rate limiting enforced (11th message/min rejected with 429)
- [ ] No memory leaks in long-running async tasks
- [ ] Database write after streaming < 100ms
- [ ] Redis operations < 10ms per poll

### Error Handling

- [ ] Gemini API timeout: Retry 3 times with exponential backoff (1s, 2s, 4s)
- [ ] FastAPI connection error: Task marked as "failed" with error message
- [ ] Redis connection error: Graceful degradation (return 503)
- [ ] Frontend handles polling timeout (>60s no response)
- [ ] Task state persists through Spring Boot restart (Redis-backed)

### Security

- [ ] Only conversation owner can send messages (JWT verification)
- [ ] Message content sanitized before DB storage (XSS prevention)
- [ ] AI response sanitized before frontend display
- [ ] Rate limiting per user enforced (10 messages/min)
- [ ] Task_id is UUID (not guessable)

### Integration with Story 2.1 & 2.2

- [ ] Story 2.1 PromptAdapter used for system_instruction
- [ ] Story 2.2 ContextWindowManager used for context building
- [ ] VectorDB character traits included in context
- [ ] Gemini system_instruction format used correctly
- [ ] Context caching from Story 2.2 reduces API calls

## Estimated Effort

14 hours
