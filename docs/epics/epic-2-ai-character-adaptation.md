# Epic 2: AI Character Adaptation to Alternative Timelines

## Epic Goal

Enable AI characters to authentically embody their alternate timeline selves by dynamically generating context-aware prompts that incorporate scenario parameters and VectorDB novel content, ensuring characters discuss their experiences in "What If" realities with coherence and depth using **Gemini 2.5 Flash** as the LLM backend.

## User Value

When users converse with "Hermione in Slytherin," the AI doesn't just pretend—it deeply understands the alternate timeline's cascading effects, discusses how Slytherin house shaped her differently, and maintains consistency across the entire alternative reality. This creates immersive "What If" exploration that feels authentic, not superficial.

## Architecture Context

- **LLM**: **Gemini 2.5 Flash** (1M input tokens, 8K output tokens)
- **Embedding**: Gemini Embedding API (text-embedding-004, 768 dimensions)
- **Backend**: Spring Boot (Port 8080) handles business logic, FastAPI (Port 8000) handles AI/LLM operations
- **Database**: PostgreSQL for metadata, **VectorDB (ChromaDB/Pinecone)** for novel content and embeddings
- **Novel Source**: Project Gutenberg Dataset (batch import via FastAPI, **not real-time API**)
- **Communication Pattern**: Spring Boot → FastAPI → Gemini 2.5 Flash, with Long Polling (2-second intervals) for async operations

## Timeline

**Week 2 of MVP development**

## Stories

### Story 2.1: Dynamic Scenario-to-Prompt Engine with VectorDB Integration

**Priority: P0 - Critical**

**Description**: Build Spring Boot service that transforms scenario parameters into comprehensive AI character prompts with full alternate timeline context, integrating with **FastAPI + VectorDB** for novel content retrieval.

**Acceptance Criteria**:

- [ ] PromptGenerationService with method: `generateCharacterPrompt(Scenario scenario, String characterName)`
- [ ] **VectorDB Integration via FastAPI**:
  - Call `POST /api/ai/vectordb/characters/search` for character personality/traits
  - Call `POST /api/ai/vectordb/events/search` for event details/outcomes
  - Call `POST /api/ai/vectordb/locations/search` for setting descriptions/cultural context
  - Call `POST /api/ai/vectordb/passages/search` for novel passage content using `base_scenarios.vectordb_passage_ids[]`
- [ ] Prompt templates for each scenario type:
  - CHARACTER_CHANGE template
  - EVENT_ALTERATION template
  - SETTING_MODIFICATION template
- [ ] Template variables populated from scenario parameters + VectorDB data:
  - `{character}`, `{property_change}`, `{cascading_effects}`, `{divergence_point}` (from VectorDB character collection)
  - `{event}`, `{alternate_outcome}`, `{ripple_effects}` (from VectorDB events collection)
  - `{original_setting}`, `{alternate_setting}`, `{cultural_context}` (from VectorDB locations collection)
  - `{passage_content}` (from VectorDB novel_passages collection)
- [ ] **Parallel VectorDB Queries**: Use CompletableFuture for concurrent FastAPI calls
- [ ] Multi-scenario support: nested scenarios combine prompts (meta-fork handling)
- [ ] Prompt length optimization: target 1,000-2,000 tokens for scenario context (well within Gemini 2.5 Flash's 1M input token limit)
- [ ] Caching: identical scenario_id + character combinations cached (5-minute TTL in Redis)
- [ ] **Error Handling**: Circuit breaker for FastAPI calls, fallback to base_scenarios metadata if VectorDB query fails
- [ ] **Long Polling Integration**: Return task_id for async prompt generation, poll `GET /api/prompts/{taskId}/status` every 2 seconds
- [ ] Unit tests for each scenario type prompt generation
- [ ] Integration test: retrieve scenario from PostgreSQL → query VectorDB via FastAPI → generate prompt → validate structure

**Prompt Template Examples**:

**CHARACTER_CHANGE Template**:

```
You are {character} in an alternate timeline where {property_change}.

DIVERGENCE POINT: {divergence_point}

ORIGINAL PASSAGE CONTEXT:
{passage_content from VectorDB}

CASCADING EFFECTS IN THIS TIMELINE:
{cascading_effects as numbered list from VectorDB character data}

You have complete knowledge of this alternate timeline. You experienced all events through this altered lens. You remember:
- How {property_change} shaped your personality differently
- Key relationships that formed because of this change (from VectorDB character relationships)
- Pivotal moments that played out differently due to your altered circumstances
- How you reflected on your journey in this timeline

When discussing your experiences, draw from THIS timeline's events, not the canonical story.

Tone: Thoughtful, introspective, aware of your alternate path.
```

**EVENT_ALTERATION Template**:

```
You are {character} in an alternate timeline where {event_description}.

ORIGINAL EVENT: {event} - {original_outcome} (from VectorDB events collection)
ALTERNATE EVENT: {event} - {alternate_outcome}
DIVERGENCE POINT: {divergence_point}

PASSAGE CONTEXT:
{passage_content from VectorDB showing original event}

RIPPLE EFFECTS IN THIS TIMELINE:
{ripple_effects as numbered list from VectorDB}

This change fundamentally altered the story's trajectory. Reflect on what might have been different.

Tone: Reflective, aware of the pivotal change, grounded in alternate reality.
```

**Technical Guidance**:

- Spring Boot service: `PromptGenerationService.java`
- **FastAPI VectorDB Client**: `VectorDbClient.java` with RestTemplate for HTTP calls
  - `POST /api/ai/vectordb/characters/search` → JSON response with character data
  - `POST /api/ai/vectordb/events/search` → JSON response with event data
  - `POST /api/ai/vectordb/locations/search` → JSON response with location data
  - `POST /api/ai/vectordb/passages/retrieve` → JSON response with passage content
- Template engine: Thymeleaf or Spring Expression Language (SpEL)
- Caching: Redis with `@Cacheable(key="#scenarioId + '_' + #characterName", expire=300)`
- Prompt structure: System prompt (1,500 tokens) + Context window (500 tokens) = ~2,000 tokens total
- **Error Handling**: Circuit breaker (Resilience4j) for VectorDB calls, fallback to base_scenarios table metadata
- **Performance**: Parallel VectorDB queries using `CompletableFuture.allOf(...)`
- **Long Polling**: Store task status in Redis, return task_id immediately, poll for completion
- Tests: JUnit 5 + Mockito for service mocking, TestContainers for Redis integration tests

**Estimated Effort**: 10 hours

---

### Story 2.2: Context Window Manager for Gemini 2.5 Flash

**Priority: P0 - Critical**

**Description**: Implement intelligent context window management that maximizes **Gemini 2.5 Flash's 1M input token capacity** by strategically including novel passages from VectorDB, character backgrounds, and scenario history while maintaining conversation coherence across long interactions.

**Acceptance Criteria**:

- [ ] ContextWindowService with method: `buildContextWindow(Conversation conversation, int messageCount)`
- [ ] **Token Budget Management for Gemini 2.5 Flash**:
  - Total input budget: **1,000,000 tokens** (Gemini 2.5 Flash limit)
  - Reserved for system prompt: **2,000 tokens** (character adaptation prompt from Story 2.1 + VectorDB context)
  - Reserved for user message: **1,000 tokens** (current user input)
  - Available for context: **997,000 tokens** (remaining budget)
  - Target context usage: **10,000-20,000 tokens** (optimal for conversation coherence, far below Gemini's capacity)
- [ ] **Context Priority Ranking** (highest to lowest):
  1. System prompt with scenario context (2,000 tokens)
  2. Last 50 messages (10,000-15,000 tokens estimated)
  3. VectorDB passage content (3,000-5,000 tokens, fetched via FastAPI)
  4. Character background from VectorDB (1,000-2,000 tokens)
  5. Older conversation history (truncated if needed)
- [ ] Token allocation strategy:
  - Scenario prompt: **2,000 tokens** (from Story 2.1 + VectorDB context)
  - Conversation history: **10,000-15,000 tokens** (last 50 messages)
  - VectorDB content: **3,000-5,000 tokens** (novel passages + character data)
  - Response buffer: **8,000 tokens** (Gemini output limit)

You experienced the core story of {base_story} but in a completely different cultural and temporal context. The themes, conflicts, and relationships were filtered through {alternate_setting}'s lens. You remember:

- How the different time period/location changed social dynamics
- Technology, customs, and cultural norms of this setting
- How core story conflicts translated to this context
- What remained universal and what was uniquely shaped by setting

Discuss your journey in THIS setting, drawing parallels to the original story's themes while grounding experiences in {alternate_setting}'s reality.

Tone: Culturally aware, reflective on universal vs. context-specific themes.

````

**Technical Notes**:

- Prompts stored in `resources/prompts/` as Mustache templates
- Scenario JSONB deserialized to strongly-typed DTOs for template population
- Token counting using custom tokenizer for Local LLM (aim for 600-800 tokens)
- Cache key: `{scenario_id}:{character_name}` (Guava cache, 5-min TTL)

**Estimated Effort**: 8 hours

---

### Story 2.2: Conversation Context Window Manager

**Priority: P0 - Critical**

**Description**: Implement sliding window context management that maintains scenario definition + recent conversation history within Local LLM's token limits while preventing timeline drift.

**Acceptance Criteria**:

- [ ] ContextWindowService with method: `buildContextWindow(Scenario scenario, List<Message> conversationHistory, String characterName)`
- [ ] Token allocation strategy:
  - Scenario prompt: 600-800 tokens (from Story 2.1)
  - Conversation history: 1,500-1,700 tokens
  - Response buffer: 800 tokens
  - Total: ~3,500 tokens (safe for Local LLM's 4,096 limit)
- [ ] Sliding window: keep last 10-15 messages, drop older messages
- [ ] Scenario context re-injection every 10 turns (prevents AI "forgetting" timeline)
- [ ] Token counting for message history using custom tokenizer
- [ ] Truncation strategy: if history exceeds limit, remove oldest messages first
- [ ] System message includes: scenario prompt + "conversation started {timestamp}"
- [ ] Unit tests for token counting accuracy
- [ ] Integration test: 20-message conversation maintains scenario consistency

**Context Window Structure**:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "{generated scenario prompt from Story 2.1}"
    },
    {
      "role": "system",
      "content": "Conversation started 2025-11-12 14:30 UTC. Remember this timeline throughout."
    },
    {
      "role": "user",
      "content": "How did being in Slytherin change you?"
    },
    {
      "role": "assistant",
      "content": "Being sorted into Slytherin was..."
    }
    // ... last 10-15 messages
  ]
}
````

**Re-injection Logic** (every 10 turns):

```
IF (message_count % 10 == 0) {
  Insert system message: "TIMELINE REMINDER: {condensed scenario prompt}"
}
```

**Technical Notes**:

- Use custom tokenizer for accurate token counting with Local LLM
- Message trimming preserves user-assistant pairs (don't orphan messages)
- Scenario prompt condensed for re-injection: 300-400 tokens (vs. 600-800 initial)
- Database query fetches only last 20 messages (optimization)

**Estimated Effort**: 6 hours

---

### Story 2.3: Multi-Timeline Character Consistency

**Priority: P1 - High**

**Description**: Ensure characters maintain distinct personalities across different What If scenarios for the same base story, preventing "character personality bleed" between timelines.

**Acceptance Criteria**:

- [ ] CharacterConsistencyService validates prompts don't contradict scenario parameters
- [ ] Character personality attributes extracted from scenario JSONB:
  - CHARACTER_CHANGE: `{alternate_value}` defines personality shift
  - EVENT_ALTERATION: personality inferred from `{ripple_effects}`
  - SETTING_MODIFICATION: personality adapted to `{cultural_context}`
- [ ] Temperature setting optimization per scenario type:
  - CHARACTER_CHANGE: 0.7 (balanced creativity)
  - EVENT_ALTERATION: 0.6 (more conservative, prevent drift)
  - SETTING_MODIFICATION: 0.8 (more creative for cultural adaptation)
- [ ] A/B testing framework to compare consistency across temperature settings
- [ ] Scenario metadata includes `character_personality_notes` (optional user input)
- [ ] Integration test: same character in 3 different scenarios produces distinct responses

**Consistency Validation Logic**:

```java
public void validateConsistency(Scenario scenario, String characterName) {
  // Extract expected personality from scenario
  PersonalityProfile expected = extractPersonality(scenario);

  // Generate test prompt
  String prompt = promptGenerationService.generateCharacterPrompt(scenario, characterName);

  // Validate prompt includes personality markers
  assert prompt.contains(expected.primaryTrait);
  assert prompt.contains(expected.motivations);

  // Log for analytics
  analyticsService.recordConsistencyCheck(scenario.getId(), characterName, true);
}
```

**Example Validation**:

- Scenario: "Hermione in Slytherin"
- Expected Personality: ambitious, cunning, loyal to Slytherin
- Prompt MUST include: "ambitious", "cunning", "Slytherin values"
- Prompt MUST NOT include: "brave" (Gryffindor trait)

**Technical Notes**:

- Personality extraction uses keyword matching on scenario JSONB
- Temperature settings stored in `application.yml`, overridable per scenario
- Consistency checks run during scenario creation (Story 1.5 validation)

**Estimated Effort**: 5 hours

---

### Story 2.4: Scenario Context Testing & Refinement

**Priority: P1 - High**

**Description**: Iteratively test and refine scenario prompts with 30+ sample scenarios to ensure authentic, coherent What If conversations before MVP launch.

**Acceptance Criteria**:

- [ ] Test suite with 30+ scenarios across all three types:
  - 10 CHARACTER_CHANGE scenarios (various properties: house, personality, mentor, ambition)
  - 10 EVENT_ALTERATION scenarios (prevented events, reversed outcomes, never occurred)
  - 10 SETTING_MODIFICATION scenarios (time periods: medieval, Victorian, 1950s, modern; locations: Seoul, Tokyo, Paris)
- [ ] Manual QA checklist per scenario:
  - Character acknowledges alternate timeline explicitly
  - Responses reference cascading effects/ripple effects appropriately
  - No canonical story details contradicting scenario
  - Personality traits match scenario parameters
  - Cultural context reflected in responses (for SETTING_MODIFICATION)
- [ ] Automated regression tests: seed questions + expected response patterns
- [ ] Prompt refinement based on failures (iterate 3-5 times)
- [ ] Documentation: "Prompt Engineering Guide" with best practices
- [ ] Final prompt templates locked and versioned (v1.0)

**Test Scenario Examples**:

**Test 1**: "Hermione in Slytherin"

- Seed Question: "How did being in Slytherin change you?"
- Expected Pattern: Mentions ambition, Snape mentorship, Draco friendship
- Red Flag: References Gryffindor bravery, Harry/Ron friendship

**Test 2**: "Gatsby Never Met Daisy"

- Seed Question: "What did you do instead of pursuing Daisy?"
- Expected Pattern: Describes alternate path, California/tech career, freedom from obsession
- Red Flag: Mentions green light, parties for Daisy, tragic ending

**Test 3**: "Pride & Prejudice in 2024 Seoul"

- Seed Question: "How did you meet Mr. Darcy?"
- Expected Pattern: Modern Seoul setting, corporate culture, technology references
- Red Flag: Mentions balls, 19th century courtship, English countryside

**Regression Test Format**:

```java
@Test
public void testHermioneInSlytherin() {
  Scenario scenario = createHermioneSlytherינScenario();
  String prompt = promptService.generateCharacterPrompt(scenario, "Hermione Granger");

  // Assert critical elements present
  assertThat(prompt).contains("Slytherin");
  assertThat(prompt).contains("ambitious");
  assertThat(prompt).doesNotContain("Gryffindor");

  // Simulate conversation (manual QA)
  String response = llmService.sendMessage(prompt, "How did being in Slytherin change you?");

  // Log for review
  System.out.println("Response: " + response);
  // Manual verification required
}
```

**Technical Notes**:

- Budget 4-5 hours for iterative prompt testing (vs. 6-8 for knowledge-boundary approach)
- Use Local LLM (Llama-2-7B) for initial tests, Mistral-7B for final validation
- Document all prompt failures and refinements in `docs/prompt-engineering-log.md`
- Final templates committed to `resources/prompts/v1.0/`

**Estimated Effort**: 6 hours

---

- **Long Polling Integration**: Return task_id for async operations, poll every 2 seconds
- **Cost Estimate (Gemini 2.5 Flash)**: $0.075 per 1M input tokens, $0.30 per 1M output tokens

## Total Estimated Effort

**32 hours** (Story 2.1: 10h + Story 2.2: 8h + Story 2.3: 6h + Story 2.4: 8h)

## Epic-Level Acceptance Criteria

- [ ] All three scenario types generate coherent, timeline-specific character prompts with VectorDB content
- [ ] Characters maintain consistency across 100+ message conversations (far longer than Local LLM's 20-message limit)
- [ ] No "canonical story bleed" (characters don't reference events from original timeline when in alternate timeline)
- [ ] Token management keeps conversations under **20,000 tokens** on average (leaving 980K tokens margin with Gemini 2.5 Flash)
- [ ] Scenario context re-injection prevents timeline drift after **20+ turns** (less frequent than Local LLM's 10-turn re-injection)
- [ ] 30+ test scenarios pass automated QA with **80%+ coherence rating** (keyword match + semantic similarity)
- [ ] **Gemini generation configs** optimized for each scenario type (temperature, top_p, top_k)
- [ ] Prompt generation latency **<3 seconds** (including VectorDB queries via FastAPI)
- [ ] **Long polling** works for all async operations (prompt generation, context building, testing) with 2-second intervals
- [ ] **Browser notifications** trigger on async task completion via WebSocket/SSE

## Dependencies

**Blocks**:

- Epic 4: Conversation System (needs character prompts to enable Gemini conversations)
- Epic 5: Scenario Tree Visualization (displays scenario metadata, needs prompts working)

**Requires**:

- Epic 1: What If Scenario Foundation (needs scenario data structure, base_scenarios table, vectordb_passage_ids[])
- **FastAPI AI Service** (Port 8000): VectorDB queries, Gemini 2.5 Flash integration
- **Gemini 2.5 Flash**: Text generation API
- **Gemini Embedding API**: 768-dimensional embeddings for semantic search
- **VectorDB (ChromaDB/Pinecone)**: 5 collections (novel_passages, characters, locations, events, themes)
- Spring Boot backend with PromptGenerationService, ContextWindowService, CharacterConsistencyService, ScenarioTestingService

## Success Metrics

**Technical Metrics**:

- Prompt generation latency **<3 seconds** (p95, including VectorDB queries via FastAPI)
- Token counting accuracy **99%+** (using Gemini Tokenizer API)
- Cache hit rate **>60%** for popular scenarios (reduces prompt generation load)
- Zero timeline inconsistency errors in production (first 3 months)
- **VectorDB query latency <500ms** (p95 for FastAPI calls)
- **Long polling efficiency**: <10% overhead vs. WebSocket (fewer connections)
- **Gemini API cost**: <$1 per 1,000 conversations (input + output tokens combined)

**User Metrics** (Phase 1 - 3 months):

- **90%+ of conversations exceed 20 messages** (proves engagement, far higher than Local LLM's 10-message target)
- User feedback: "Character felt authentic to timeline" (qualitative surveys)
- **<2% user reports of "character breaking timeline"** (scenario consistency, improved from Local LLM's <5% target)
- 60%+ of scenarios forked have conversations (proves scenarios inspire engagement)
- **Human rating avg 4.2+ for Gemini-generated responses** (out of 5 stars)

## Risk Mitigation

**Risk 1: Gemini API costs exceed budget**

- Mitigation: Token budget target 10,000-20,000 tokens per conversation (far below 1M limit)
- Mitigation: Caching for identical prompts (5-minute TTL in Redis)
- Mitigation: Monitor usage via Gemini API dashboard, set alerts at $100/day
- Mitigation: Fallback to smaller context window (5,000 tokens) if costs spike

**Risk 2: Characters drift from timeline after extended conversations**

- Mitigation: Re-inject scenario context every **20 turns** with VectorDB-refreshed data (Story 2.2)
- Mitigation: **Gemini generation config tuning** per scenario type (temperature, top_p, top_k) (Story 2.3)
- Mitigation: Automated QA with semantic similarity checks via VectorDB (Story 2.4)

**Risk 3: VectorDB query failures disrupt prompt generation**

- Mitigation: **Circuit breaker pattern** (Resilience4j) with 5-second timeout for FastAPI calls
- Mitigation: Fallback to base_scenarios metadata if VectorDB unavailable
- Mitigation: Redis caching for VectorDB results (5-minute TTL)
- Mitigation: Health checks for FastAPI service, alert on 3+ consecutive failures

**Risk 4: Cultural insensitivity in SETTING_MODIFICATION scenarios**

- Mitigation: **Gemini Safety Settings** (BLOCK_MEDIUM_AND_ABOVE for all harm categories)
- Mitigation: VectorDB cultural context validation via FastAPI semantic search
- Mitigation: User-provided cultural context reviewed before publish (Story 1.5 from Epic 1)
- Mitigation: Community reporting (Phase 2) for offensive scenarios

**Risk 5: Long polling overhead slows down UI**

- Mitigation: 2-second polling interval balances responsiveness vs. server load
- Mitigation: Browser notifications trigger immediately on task completion (via WebSocket/SSE)
- Mitigation: Exponential backoff for failed polls (2s → 4s → 8s → max 30s)
- Mitigation: Cancel polling when user navigates away (cleanup on component unmount)

**Risk 6: Prompt engineering complexity delays MVP**

- Mitigation: Fixed time-box (8 hours for Story 2.4 testing with Gemini)
- Mitigation: Ship "good enough" prompts in MVP, iterate based on Gemini API feedback
- Mitigation: Prompt versioning (v1.0, v1.1...) enables gradual improvement
- Mitigation: A/B testing framework for comparing Gemini generation configs (Story 2.3)

## Technical Debt Decisions

**Accepted Debt** (to be addressed post-MVP):

- No dynamic personality extraction from novel text (using VectorDB character data only, not real-time LLM analysis)
- No multi-character conversations (one character per conversation in MVP)
- No sentiment analysis to detect timeline drift (automated keyword/semantic checks only)
- A/B testing framework limited to generation configs (not full prompt variations)
- Hardcoded Gemini generation configs (not ML-optimized per user/scenario)
- No prompt version rollback (forward-only versioning)
- No real-time VectorDB updates during conversation (refresh only every 20 turns)

**Won't Build** (architectural decisions):

- Real-time prompt optimization based on Gemini conversation quality (too complex for MVP)
- User-editable prompts (security risk, prompt injection attacks with Gemini API)
- Multiple LLM provider support (Gemini-only for MVP, OpenAI/Claude in Phase 2)
- Custom fine-tuned LLM (Gemini 2.5 Flash with prompt engineering sufficient for MVP)
- Real-time embedding generation (VectorDB embeddings pre-computed during novel ingestion)

## Testing Strategy

**Unit Tests** (Story 2.1):

- Prompt generation for all three scenario types with VectorDB mock data
- FastAPI VectorDB client methods with RestTemplate mocking
- JSONB parameter extraction and template population
- Token counting accuracy with Gemini Tokenizer API mock
- Cache hit/miss logic with Redis TestContainers

**Integration Tests** (Stories 2.1-2.2):

- Retrieve scenario from PostgreSQL → query VectorDB via FastAPI → generate prompt → validate structure
- 100-message conversation → context window management → token limits respected (using Gemini tokenizer)
- Scenario context re-injection after 20 turns with VectorDB-refreshed data
- Long polling: submit task → poll status every 2 seconds → verify completion within 10 seconds

**API Integration Tests** (Story 2.1):

- FastAPI VectorDB endpoints: `/api/ai/vectordb/characters/search`, `/events/search`, `/locations/search`, `/passages/retrieve`
- Gemini 2.5 Flash API: generate response with different generation configs (temperature, top_p, top_k)
- Gemini Embedding API: compute semantic similarity for consistency validation
- Gemini Tokenizer API: count tokens for context window management

**Manual QA Tests** (Story 2.4):

- 30+ scenarios with seed questions, Gemini-generated responses evaluated by humans
- Rating scale: 1-5 stars for timeline authenticity, character voice, coherence
- Edge cases: 100+ message conversations, nested scenarios (meta-forks), unusual cultural settings

**Performance Tests**:

- Prompt generation latency: target p95 <3 seconds (including VectorDB queries)
- VectorDB query latency: target p95 <500ms (FastAPI → ChromaDB/Pinecone)
- Gemini API latency: target p95 <2 seconds (text generation)
- Long polling overhead: <10% CPU vs. WebSocket equivalent

## Cost Estimates (Gemini 2.5 Flash)

**Per Conversation** (avg 50 messages, 20 turns):

- Input tokens: ~25,000 tokens total (prompts + context + messages)
- Output tokens: ~50,000 tokens total (50 messages × 1,000 tokens avg)
- Cost: (25K × $0.075 / 1M) + (50K × $0.30 / 1M) = $0.0019 + $0.015 = **$0.0169 per conversation**

**Monthly Estimates** (1,000 active users, 5 conversations each):

- Total conversations: 5,000/month
- Total cost: 5,000 × $0.0169 = **$84.50/month for Gemini API**
- VectorDB cost (Pinecone): ~$70/month for 100K vectors (768-dim)
- **Total AI cost: ~$155/month**

---

**Epic 2 Total**: **32 hours** | **4 stories** | **Gemini 2.5 Flash + VectorDB + FastAPI integration**

- Character personality consistency across different scenarios
- Cultural sensitivity review for SETTING_MODIFICATION scenarios
- Long conversation testing (30+ messages) for timeline drift

**Performance Tests**:

- Prompt generation latency (target < 50ms for 1,000 concurrent requests)
- Cache performance (hit rate >60% under load)
- Token counting speed (target < 10ms per message)

## Open Questions

1. **Q**: Should we support multi-character conversations? (e.g., "Hermione in Slytherin" + "Harry in Slytherin" together)
   **A**: Not in MVP. Single character per conversation keeps prompts simple. Phase 2 feature.

2. **Q**: How do we handle offensive or inappropriate alternate timelines in prompts?
   **A**: Validation system (Story 1.5) uses Local LLM to flag offensive content. Human review for edge cases.

3. **Q**: Should temperature settings be user-configurable?
   **A**: No. Temperature tuned per scenario type by system. User customization creates quality control nightmare.

4. **Q**: What if character doesn't exist in alternate timeline? (e.g., "What if Hermione never went to Hogwarts" → how to converse with her?)
   **A**: Scenario validation (Story 1.5) catches this. Prompt becomes: "You are Hermione who never attended Hogwarts. Discuss your Muggle life."

## Definition of Done

- [ ] All 4 stories completed with acceptance criteria met
- [ ] 30+ test scenarios passing manual QA (90%+ coherence)
- [ ] Prompt templates v1.0 locked and deployed to production
- [ ] Unit tests >80% coverage on PromptGenerationService, ContextWindowService
- [ ] Integration tests passing for all scenario types
- [ ] Performance benchmarks met (< 50ms prompt generation, < 10ms token counting)
- [ ] Documentation: "Prompt Engineering Guide" published in `docs/`
- [ ] Token limit regression tests prevent future prompt expansion beyond 4,000 tokens
- [ ] Code review completed, no P0/P1 issues
- [ ] Deployed to Railway staging, smoke tested with 5 sample conversations per scenario type

---

**Epic Owner**: AI/ML Lead + Backend Lead (joint ownership)

**Start Date**: Week 2, Day 1 of MVP development

**Target Completion**: Week 2, Day 5 (5 working days)

**Estimated Total Effort**: 25 hours (achievable within 1 week for 1-2 engineers)
