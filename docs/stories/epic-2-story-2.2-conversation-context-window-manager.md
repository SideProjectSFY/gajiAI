# Story 2.2: Conversation Context Window Manager

**Epic**: Epic 2 - AI Adaptation Layer  
**Priority**: P0 - Critical  
**Status**: Not Started  
**Estimated Effort**: 10 hours

## Description

Implement intelligent context window management to include relevant message history, scenario parameters, and character consistency rules within **Gemini 2.5 Flash token limits** (1M input, 8K output).

## Dependencies

**Blocks**:

- Story 4.2: Message Streaming (needs context management for multi-turn conversations)

**Requires**:

- Story 2.1: Scenario-to-Prompt Engine (builds on prompt generation)
- Story 4.1: Conversation Data Model (reads message history)

## Acceptance Criteria

- [ ] `ContextWindowManager` service calculates token count for messages using **Gemini token counting API**
- [ ] **Gemini 2.5 Flash token limits**:
  - Input: 1,000,000 tokens (1M context window)
  - Output: 8,192 tokens max
  - Cost: $0.075 per 1M input tokens, $0.30 per 1M output tokens
- [ ] Context strategy: System instruction + **Full conversation history** (no sliding window needed with 1M limit)
- [ ] **Smart context optimization** for long conversations (>10K tokens):
  - Summarize messages older than 100 messages using Gemini
  - Keep recent 100 messages in full detail
  - System instruction + character traits always included
- [ ] Character consistency injection: Adds character traits summary every 50 messages (reduced frequency due to large context)
- [ ] `/api/ai/build-context` endpoint returns: system_instruction, messages[], token_count, optimization_applied
- [ ] Token count validation before Gemini API call (reject if > 1M input or expect > 8K output)
- [ ] Context caching: Redis cache for repeated conversation_id queries (TTL 5 minutes)
- [ ] **Gemini Caching API** for system instructions (reduces cost for repeated contexts)
- [ ] Metrics: Average token usage, optimization rate, cache hit rate, Gemini API cost per conversation
- [ ] Unit tests >85% coverage

## Technical Notes

**Token Counting with Gemini API**:

```python
from google import generativeai as genai
from typing import List, Dict
import redis.asyncio as redis
import os

class ContextWindowManager:
    # Gemini 2.5 Flash token limits
    MAX_INPUT_TOKENS = 1_000_000  # 1M input token limit
    MAX_OUTPUT_TOKENS = 8_192      # 8K output token limit
    OPTIMIZATION_THRESHOLD = 10_000  # Optimize if >10K tokens
    RECENT_MESSAGE_COUNT = 100     # Keep last 100 messages in full detail
    CHARACTER_REMINDER_INTERVAL = 50  # Inject reminder every 50 messages

    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.redis = redis.from_url(os.getenv("REDIS_URL"))

    async def count_tokens(
        self,
        system_instruction: str,
        messages: List[Dict]
    ) -> int:
        """Count tokens using Gemini's token counting API"""
        # Gemini provides count_tokens() method
        content = [{"role": "system", "parts": [system_instruction]}]
        content.extend([
            {"role": msg["role"], "parts": [msg["content"]]}
            for msg in messages
        ])

        result = self.model.count_tokens(content)
        return result.total_tokens

    async def build_context(
        self,
        scenario_id: str,
        conversation_id: str
    ) -> Dict:
        """
        Build conversation context for Gemini 2.5 Flash
        Returns: system_instruction, messages[], token_count, optimization_applied
        """
        # Get scenario-adapted system instruction from Story 2.1
        system_instruction = await self.get_system_instruction(scenario_id)

        # Get conversation messages from database
        messages = await get_messages(conversation_id)

        # Count tokens using Gemini API
        token_count = await self.count_tokens(system_instruction, messages)

        # Optimize context if needed (>10K tokens)
        optimization_applied = False
        if token_count > self.OPTIMIZATION_THRESHOLD:
            messages = await self.optimize_context(messages, scenario_id)
            token_count = await self.count_tokens(system_instruction, messages)
            optimization_applied = True

        # Inject character reminders for consistency
        messages = self.inject_character_reminders(messages, scenario_id)

        # Final validation
        if token_count > self.MAX_INPUT_TOKENS:
            raise ValueError(f"Context exceeds 1M token limit: {token_count}")

        return {
            "system_instruction": system_instruction,
            "messages": messages,
            "token_count": token_count,
            "optimization_applied": optimization_applied
        }

    async def optimize_context(
        self,
        messages: List[Dict],
        scenario_id: str
    ) -> List[Dict]:
        """
        Optimize long conversations (>10K tokens):
        - Keep recent 100 messages in full detail
        - Summarize older messages using Gemini
        """
        if len(messages) <= self.RECENT_MESSAGE_COUNT:
            return messages  # No optimization needed

        # Split into old and recent messages
        old_messages = messages[:-self.RECENT_MESSAGE_COUNT]
        recent_messages = messages[-self.RECENT_MESSAGE_COUNT:]

        # Summarize old messages using Gemini
        summary = await self.summarize_messages(old_messages)

        # Return: [summary] + recent messages
        return [
            {"role": "system", "content": f"Previous conversation summary: {summary}"}
        ] + recent_messages

    async def summarize_messages(self, messages: List[Dict]) -> str:
        """Use Gemini to summarize old messages"""
        prompt = "Summarize this conversation history in 200 words, focusing on key plot points and character decisions:\n\n"
        prompt += "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        response = await self.model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=500
            )
        )

        return response.text

    def inject_character_reminders(
        self,
        messages: List[Dict],
        scenario_id: str
    ) -> List[Dict]:
        """Inject character consistency reminders every 50 messages"""
        scenario = get_scenario(scenario_id)
        character = scenario.parameters.get('character')
        new_property = scenario.parameters.get('new_property')

        reminder = f"REMINDER: {character} is {new_property}. Maintain character consistency."

        result = []
        for i, msg in enumerate(messages):
            result.append(msg)
            # Inject reminder every 50 messages (less frequent due to 1M context)
            if (i + 1) % self.CHARACTER_REMINDER_INTERVAL == 0:
                result.append({
                    "role": "system",
                    "content": reminder
                })

        return result

    async def get_system_instruction(self, scenario_id: str) -> str:
        """Get scenario-adapted system instruction from Story 2.1"""
        # This uses the PromptAdapter from Story 2.1
        from .prompt_adapter import PromptAdapter
        adapter = PromptAdapter()
        prompt_data = await adapter.adapt_prompt(scenario_id)
        return prompt_data['system_instruction']
```

**FastAPI Endpoint**:

```python
@router.post("/api/ai/build-context")
async def build_context(request: BuildContextRequest):
    """
    Build conversation context for Gemini 2.5 Flash
    Returns: system_instruction, messages[], token_count, optimization_applied
    """
    context_manager = ContextWindowManager()

    # Check Redis cache first (TTL 5 minutes)
    cache_key = f"context:{request.conversation_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Build context with Gemini token counting
    try:
        context = await context_manager.build_context(
            request.scenario_id,
            request.conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Cache for 5 minutes
    await redis.setex(cache_key, 300, json.dumps(context))

    return context
```

**Gemini Caching API Usage** (for repeated system instructions):

```python
# Use Gemini Caching API to reduce costs for repeated contexts
# This caches the system_instruction + character traits
cached_content = genai.caching.CachedContent.create(
    model='gemini-2.5-flash',
    system_instruction=system_instruction,
    ttl=datetime.timedelta(minutes=60)
)

# Reuse cached content for multiple conversations
model = genai.GenerativeModel.from_cached_content(cached_content)
```

**Cost Analysis**:

- **Without optimization**: 50K tokens avg × $0.075/1M = $0.00375 per conversation
- **With optimization** (>10K conversations): 10K tokens avg × $0.075/1M = $0.00075 per conversation (80% reduction)
- **With Gemini Caching**: Additional 50% cost reduction for system_instruction reuse
- **Monthly cost** (10,000 conversations):
  - No optimization: $37.50
  - With optimization: $7.50 (80% reduction)
  - With caching: $3.75 (90% reduction)

## QA Checklist

### Functional Testing

- [ ] Context with 100 messages stays within 1M token limit
- [ ] Gemini token counting API returns accurate token count
- [ ] System instruction always included in context (from Story 2.1)
- [ ] Character reminders injected every 50 messages
- [ ] Token count matches Gemini's count_tokens() API

### Context Optimization Strategy

- [ ] Conversations <10K tokens include full history (no optimization)
- [ ] Conversations >10K tokens optimize: summarize old + keep recent 100
- [ ] Gemini summarization produces coherent 200-word summaries
- [ ] Recent 100 messages always in full detail
- [ ] optimization_applied flag correctly set

### Performance

- [ ] build_context < 500ms (uncached, with Gemini token counting)
- [ ] build_context < 50ms (cached from Redis)
- [ ] Cache hit rate >70% in load testing
- [ ] Gemini token counting API < 100ms per call

### Edge Cases

- [ ] Conversation with 1 message works
- [ ] Conversation with 500+ messages handles gracefully (optimization triggered)
- [ ] Empty message history returns only system_instruction
- [ ] Very long conversation (>1M tokens) returns 400 error with clear message
- [ ] Gemini API failure during summarization handled gracefully

### Cost & Metrics

- [ ] Average token usage logged per conversation
- [ ] Optimization rate tracked (optimized conversations / total)
- [ ] Cache hit rate exposed via /metrics endpoint
- [ ] Estimated cost per conversation calculated (<$0.01 target)
- [ ] Gemini Caching API usage monitored (if implemented)

## Estimated Effort

10 hours
