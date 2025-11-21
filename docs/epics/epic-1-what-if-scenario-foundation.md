# Epic 1: What If Scenario Foundation

## Epic Goal

Establish the core "What If" scenario infrastructure that enables users to create, store, and manage alternative story timelines with three distinct scenario types: Character Property Changes, Event Alterations, and Setting Modifications.

## User Value

Users can begin exploring alternative timelines by creating structured "What If" scenarios that answer questions like "What if Hermione was sorted into Slytherin?" or "What if Gatsby never met Daisy?" The foundation enables the entire platform's multiverse exploration experience.

## Timeline

**Week 1-2 of MVP development**

## Stories (3 total, 26 hours)

### Story 1.1: Scenario Data Model & API Foundation

**Priority: P0 - Critical**

**Story File**: `docs/stories/epic-1-story-1.1-scenario-data-model-api.md`

**Description**: Create the PostgreSQL database schema and Spring Boot REST API for managing What If scenarios with normalized database structure and VectorDB integration.

**Acceptance Criteria**:

- [ ] **Normalized scenario tables** created in PostgreSQL (metadata only):
  - `base_scenarios` with structured columns + **vectordb_passage_ids TEXT[]** (references to VectorDB)
  - `root_user_scenarios` and `leaf_user_scenarios` for user-created scenarios
  - `scenario_character_changes` table with **character_vectordb_id** (references VectorDB characters collection)
  - `scenario_event_alterations` table for EVENT_ALTERATION type parameters
  - `scenario_setting_modifications` table for SETTING_MODIFICATION type parameters
- [ ] **VectorDB integration via FastAPI**:
  - Spring Boot calls FastAPI endpoints for character/passage search
  - `POST /api/ai/search/characters` (semantic search in VectorDB)
  - `POST /api/ai/search/passages` (retrieve passages for scenarios)
- [ ] Recursive CTE query support for scenario tree retrieval (meta-timeline forking)
- [ ] CRUD API endpoints (Spring Boot):
  - POST /api/v1/scenarios (create root scenario, store passage IDs from FastAPI)
  - GET /api/v1/scenarios/{id} (retrieve with type-specific parameters + VectorDB references)
  - GET /api/v1/scenarios (list with filtering)
  - PUT /api/v1/scenarios/{id} (update)
  - DELETE /api/v1/scenarios/{id} (soft delete)
- [ ] Scenario forking endpoint: POST /api/v1/scenarios/{id}/fork
- [ ] Circular reference prevention in fork logic
- [ ] B-tree indexes on all FK columns (base_scenario_id, parent_scenario_id, creator_id)
- [ ] **GIN index on vectordb_passage_ids** for fast array queries
- [ ] Soft delete pattern with deleted_at timestamp
- [ ] Java domain models with proper MyBatis relationships to normalized tables
- [ ] Response time < 100ms for single scenario retrieval (PostgreSQL metadata only)
- [ ] Unit tests >80% coverage on repository and service layers

**Technical Notes**:

- **Hybrid Database Architecture**: PostgreSQL stores metadata, VectorDB stores full content
- **Cross-service communication**: Spring Boot → FastAPI for all VectorDB queries
- **character_vectordb_id** replaces character_id FK (characters now in VectorDB)
- parent_scenario_id (in root/leaf_user_scenarios) enables infinite meta-scenario branching
- Structured columns enable type-safe queries, better indexing vs JSONB
- XOR constraints ensure each scenario has exactly one type-specific parameter set
- CASCADE DELETE on FKs ensures automatic cleanup when scenarios are deleted
- fork_count, conversation_count support future recommendation algorithms
- **Never access VectorDB directly from Spring Boot** - always call FastAPI endpoints

**Estimated Effort**: 8 hours

---

### Story 1.2: Unified Scenario Creation Modal

**Priority: P1 - High**

**Story File**: `docs/stories/epic-1-story-1.2-unified-scenario-creation-modal.md`

**Description**: Build a single unified modal component for creating all three scenario types (Character Changes, Event Alterations, Setting Modifications) with real-time validation and character counters.

**Acceptance Criteria**:

- [ ] **ScenarioCreationModal.vue** component (PrimeVue Dialog)
- [ ] **Scenario Title input** (required, max 100 characters)
- [ ] **Three optional textareas**:
  - Character Changes (optional, min 10 chars if filled)
  - Event Alterations (optional, min 10 chars if filled)
  - Setting Modifications (optional, min 10 chars if filled)
- [ ] **Character counter component** with color coding:
  - Green (valid): ≥10 characters
  - Red (invalid): 1-9 characters
  - Gray (empty): 0 characters
- [ ] **Validation rules**:
  - At least ONE scenario type must have ≥10 characters
  - Scenario title required (max 100 chars)
  - Empty fields are allowed
- [ ] **Submit button state**: Disabled until validation passes
- [ ] **API integration**: POST /api/v1/scenarios with bookId + all filled types
- [ ] **Success behavior**: Navigate to new scenario detail page
- [ ] **Mobile responsive**: Fullscreen modal on < 768px
- [ ] **Keyboard shortcuts**: Escape to close, Cmd/Ctrl+Enter to submit

**UI Structure**:

```
[ + Create Scenario ]  (Modal Dialog)

Scenario Title: [___________________________] (max 100 chars)

Character Changes (Optional):
[________________________________________________]  ✓ 45 chars
[________________________________________________]
[________________________________________________]

Event Alterations (Optional):
[________________________________________________]  ✗ 5 chars (min 10)
[________________________________________________]

Setting Modifications (Optional):
[________________________________________________]  - 0 chars
[________________________________________________]

ℹ️ At least one scenario type must have minimum 10 characters

[Cancel]  [Create Scenario] (disabled until valid)
```

**Technical Notes**:

- **Unified modal approach**: Replaces old 3-story tab wizard with single modal
- **Reduced complexity**: Users fill only what they want, validation ensures at least 1 type filled
- **CharCounter component**: Separate reusable component with computed statusClass (green/red/gray)
- **Trigger from multiple pages**: Book Detail page, Scenario Browse page
- Passes bookId and bookTitle as props for API integration

**Estimated Effort**: 12 hours

---

### Story 1.3: Scenario Validation System with Gemini 2.5 Flash

**Priority: P1 - High**

**Story File**: `docs/stories/epic-1-story-1.3-scenario-validation-system.md`

**Description**: Implement **Gemini 2.5 Flash via FastAPI** validation to ensure scenario coherence and prevent contradictions before publication.

**Acceptance Criteria**:

- [ ] **Validation service endpoint** (Spring Boot): POST /api/v1/scenarios/validate
  - Spring Boot proxies to FastAPI: POST /api/ai/scenarios/validate
  - FastAPI calls Gemini 2.5 Flash for validation analysis
- [ ] **Gemini 2.5 Flash validation** via FastAPI checking for:
  - Logical coherence (changes make sense given book context)
  - Character plausibility (altered characters remain recognizable)
  - Timeline consistency (no contradictions in cascading effects)
  - Story knowledge accuracy (events/characters actually exist in book)
- [ ] Validation score: 0-100 (threshold: 70+ to approve)
- [ ] Validation response includes:
  - Pass/Fail status
  - Coherence score
  - Specific issues found (if any)
  - Suggestions for improvement
- [ ] Frontend displays validation results before scenario creation
- [ ] User can force-publish despite warnings
- [ ] Validation results cached in Redis for 5 minutes (prevent duplicate calls)
- [ ] Token budget: max **2,000 tokens per validation** (Gemini 2.5 Flash allows richer analysis)

**Validation Prompt Template** (Gemini 2.5 Flash via FastAPI):

```
Analyze this "What If" scenario for logical coherence:

Book: {base_story}
Scenario Type: {scenario_type}
Changes: {scenario_parameters}

Evaluate:
1. Do the changes make logical sense given the book's world?
2. Would the character remain recognizable after these changes?
3. Are there any contradictions in the cascading effects?
4. Do the events/characters actually exist in the original book?

Respond with JSON:
{
  "coherence_score": 0-100,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1"]
}
```

**Technical Notes**:

- **API Gateway Pattern**: Frontend → Spring Boot → FastAPI → Gemini 2.5 Flash
- **Gemini API cost**: ~$0.00015 per validation (2,000 tokens × $0.075 / 1M input)
  - Example: 1,000 validations/month = $0.15 (negligible cost)
- **Cache validation results** in Redis using scenario hash (5-minute TTL)
- Validation runs async via FastAPI background task, shows loading spinner
- Expected response time: **2-3 seconds** (Gemini 2.5 Flash inference)
- Failed validations saved to PostgreSQL for quality analytics
- **Retry logic**: 3 retries with exponential backoff for Gemini API failures

**Estimated Effort**: 6 hours

---

## Epic-Level Acceptance Criteria

- [ ] All three scenario types (Character, Event, Setting) functional and tested
- [ ] Scenario creation flow takes < 3 minutes for average user
- [ ] Validation prevents 90%+ of nonsensical scenarios from being published
- [ ] Database supports minimum 100,000 scenarios without performance degradation
- [ ] API response times < 200ms for list queries, < 100ms for single retrieval
- [ ] Mobile experience functional on 375px+ width devices
- [ ] 30+ pre-seeded quality scenarios across 10 popular books

## Dependencies

**Blocks**:

- Epic 2: AI Character Adaptation (needs scenario data structure)
- Epic 3: Scenario Discovery & Forking (needs scenarios to display)
- Epic 4: Conversation System (needs scenario context for AI prompts)

**Requires**:

- **Epic 0**: Project Setup & Infrastructure (Spring Boot, PostgreSQL, FastAPI, VectorDB, Redis)
- **FastAPI AI Service**: Deployed with Gemini 2.5 Flash API key configured
- **VectorDB (ChromaDB dev / Pinecone prod)**: Seeded with characters, passages, events collections
- **Redis**: For validation result caching (5-minute TTL)

## Success Metrics

**Technical Metrics**:

- 0 data loss incidents
- 99%+ uptime for scenario API
- < 100ms p95 response time for single scenario GET
- < 500ms p95 response time for scenario list with filters

**User Metrics** (Phase 1 - 3 months):

- 50%+ of users create at least one scenario
- 3+ scenarios per active creator (validates repeat usage)
- 70%+ of created scenarios pass validation (proves template guidance works)
- 40%+ scenario fork rate (proves scenarios inspire further exploration)

## Risk Mitigation

**Risk 1: Complex scenario creation intimidates users**

- Mitigation: Template-driven UI with dropdowns/selectors (Stories 1.2-1.4)
- Mitigation: Real-time JSONB preview helps users understand structure
- Mitigation: Pre-seed 30+ example scenarios users can fork

**Risk 2: Poor quality scenarios pollute platform**

- Mitigation: Gemini 2.5 Flash validation (Story 1.5) filters obvious problems
- Mitigation: Community engagement metrics (likes, conversations, forks) indicate quality
- Mitigation: Community reporting in Phase 2 (deferred from MVP)

**Risk 3: Database performance degrades with scenario trees**

- Mitigation: Recursive CTE queries optimized with proper indexes
- Mitigation: Pagination on scenario lists (max 50 per page)
- Mitigation: Load testing with 100,000+ scenario tree before launch

**Risk 4: JSONB schema evolution creates migration headaches**

- Mitigation: JSONB provides schema-free flexibility—new scenario types add new keys
- Mitigation: Backward compatibility: old scenarios don't break when new fields added
- Mitigation: Document JSONB schema evolution strategy in Story 1.1

## Technical Debt Decisions

**Accepted Debt** (to be addressed post-MVP):

- Hardcoded character lists for popular books (future: RAG extraction)
- Hardcoded event timelines (future: RAG extraction)
- No ML-based scenario quality prediction (using Gemini 2.5 Flash validation)
- No scenario merge/combine mechanics (Phase 2 feature)
- No collaborative scenario editing (Phase 2 feature)

**Won't Build** (architectural decisions):

- Scenario versioning (parent_scenario_id provides forking, not versioning)
- Scenario rollback (soft delete is sufficient for MVP)
- Real-time collaborative editing (async creation only)

## Testing Strategy

**Unit Tests** (Story 1.1):

- ScenarioRepository CRUD operations
- ScenarioService fork logic
- Circular reference detection trigger
- JSONB serialization/deserialization

**Integration Tests** (All Stories):

- POST /api/scenarios with all three scenario types
- GET /api/scenarios with filters (base_story, scenario_type, creator_id)
- POST /api/scenarios/{id}/fork with meta-scenario creation
- Validation endpoint integration with Local LLM

**E2E Tests** (Stories 1.2-1.4):

- Create Character Property Change scenario end-to-end
- Create Event Alteration scenario end-to-end
- Create Setting Modification scenario end-to-end
- Validation failure prevents scenario creation
- Validation success enables scenario creation

**Performance Tests**:

- 100,000 scenario load test (database)
- Concurrent scenario creation (50 simultaneous users)
- Scenario tree retrieval with 5-level depth (recursive query performance)

## Open Questions

1. **Q**: Should scenario titles be auto-generated or user-provided?
   **A**: Auto-generate from parameters with user override option (e.g., "Hermione in Slytherin" auto-generated, user can change to "The Ambitious Hermione")

2. **Q**: How many cascading effects are optimal for user engagement vs. cognitive load?
   **A**: Min 2, max 5 (forced range ensures thoughtfulness without overwhelming)

3. **Q**: Should we allow "private" scenarios not visible in public discovery?
   **A**: Yes, add `visibility` field (public/unlisted/private) in Story 1.1—default to "public"

4. **Q**: What happens if user creates contradictory meta-fork? (e.g., "Hermione in Slytherin" + "Hermione never went to Hogwarts")
   **A**: Validation system (Story 1.3) catches this, suggests: "These scenarios contradict. Consider separate timelines."

## Definition of Done

- [ ] All 3 stories completed with acceptance criteria met
- [ ] Unit tests >80% coverage on backend services
- [ ] Integration tests passing for all API endpoints
- [ ] E2E tests passing for all three scenario creation flows
- [ ] 30+ pre-seeded scenarios created using the UI (manual QA)
- [ ] Performance benchmarks met (100ms retrieval, 200ms list queries)
- [ ] Mobile responsive verified on iOS Safari and Chrome Android
- [ ] Documentation: API docs (Swagger), scenario JSONB schema reference
- [ ] Database migration scripts committed (Flyway V2\_\_create_scenarios_table.sql)
- [ ] Code review completed, no P0/P1 issues remaining
- [ ] Deployed to Railway staging environment and smoke tested

---

**Epic Owner**: Backend Lead + Frontend Lead (joint ownership)

**Start Date**: Week 1, Day 1 of MVP development

**Target Completion**: Week 2, Day 5 (10 working days)

**Estimated Total Effort**: 26 hours (within 2-week sprint for 2 engineers)
