# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gaji** (가지, Korean for "branch") is a novel platform that applies Git-style forking to AI-mediated book discussions with the tagline **"Branch all of story"**. Users can fork conversations at specific moments to explore different discussion paths, creating a tree of diverse interpretations and collaborative exploration.

**Current Status**: MVP planning phase complete with comprehensive documentation. All 37 user stories across 7 epics (Epic 0-6) are fully documented with production-ready specifications. The platform uses a **hybrid database architecture** with **PostgreSQL for metadata** (13 tables) and **VectorDB for content/embeddings** (5 collections).

**Key Architectural Decisions**:

1. **Hybrid Database**: PostgreSQL (metadata) + VectorDB (ChromaDB/Pinecone for content)
2. **MSA Backend**: Spring Boot (CRUD, port 8080) + FastAPI (AI/RAG, port 8000)
3. **Novel Source**: Project Gutenberg Dataset (batch import, not real-time API)
4. **Scenario Fork**: Unlimited depth - users can create meta-scenarios by forking existing scenarios
5. **Conversation Fork**: ROOT-only (parent_conversation_id IS NULL) - maximum depth of 1 level
6. **Message Copy Logic**: When forking conversations, automatically copy **min(6, total_message_count)** most recent messages
7. **Conversation Start Rule**: Users always initiate conversations (no AI-first messages)

## Essential Development Commands

### Backend Development

```bash
# Core Backend (Spring Boot - Java with Gradle)
cd core-backend
./gradlew bootRun               # Run core backend (port 8080)
./gradlew build                 # Build and run tests
./gradlew test                  # Run unit tests only
./gradlew clean build           # Clean build

# AI Backend (FastAPI - Python with uv)
cd ai-backend
uv venv                         # Create virtual environment
source .venv/bin/activate       # Activate venv (macOS/Linux)
uv pip install -r requirements.txt  # Install dependencies
uvicorn main:app --reload       # Run AI backend (port 8000)
pytest                          # Run tests
```

### Frontend Development

```bash
# Vue.js Frontend with pnpm
cd frontend
pnpm install                    # Install dependencies
pnpm dev                        # Run development server (port 3000)
pnpm build                      # Build for production
pnpm lint                       # Lint code
pnpm format                     # Format with Prettier
pnpm prepare                    # Prepare Panda CSS (codegen)
```

### Database

```bash
# PostgreSQL (via Docker)
docker-compose up -d postgres   # Start PostgreSQL
docker-compose down             # Stop all services

# ChromaDB (via Docker - Development)
docker-compose up -d chromadb   # Start ChromaDB
# Access: http://localhost:8001

# Redis (for Celery)
docker-compose up -d redis      # Start Redis

# Run migrations (from core-backend)
./gradlew flywayMigrate         # Apply database migrations
./gradlew flywayInfo            # Check migration status
```

## Architecture Overview

### Multi-Service Architecture

```
/
├── core-backend/         # Spring Boot (Java) - Main business logic
│   ├── src/main/java/
│   │   ├── controller/  # REST API endpoints
│   │   ├── service/     # Business logic layer
│   │   ├── repository/  # Database access (JPA)
│   │   ├── model/       # Domain models & entities
│   │   ├── config/      # Spring configuration
│   │   └── client/      # FastAPI service client (WebClient)
│   └── src/main/resources/
│       └── db/migration/ # Flyway migrations
│
├── ai-backend/          # FastAPI (Python) - AI/RAG service
│   ├── app/
│   │   ├── api/         # AI endpoints
│   │   ├── services/    # RAG, LLM integration
│   │   │   ├── novel_ingestion.py
│   │   │   ├── rag_service.py
│   │   │   └── vectordb_client.py
│   │   ├── models/      # Pydantic models
│   │   ├── celery_app.py
│   │   └── utils/
│   └── requirements.txt
│
├── frontend/            # Vue 3 + TypeScript
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page components
│   │   ├── stores/      # Pinia stores (state management)
│   │   ├── router/      # Vue Router
│   │   └── services/    # API client services
│   │       ├── coreApi.ts    # Spring Boot API
│   │       └── aiApi.ts      # FastAPI API (if needed)
│   ├── styled-system/   # Panda CSS generated files
│   ├── panda.config.ts  # Panda CSS configuration
│   └── package.json
│
└── docs/                # Product documentation
    ├── PRD.md
    ├── architecture.md  # THIS DOCUMENT - Updated for VectorDB
    ├── ERD.md           # Hybrid DB schema (PostgreSQL + VectorDB)
    ├── epics/
    └── stories/
```

### Hybrid Database Architecture

> **CRITICAL**: Spring Boot uses ONLY PostgreSQL, FastAPI uses ONLY VectorDB. Cross-database access must go through REST API.

**PostgreSQL (Metadata Only - 13 Tables)** ← Spring Boot ONLY:

- `users` - User accounts
- `novels` - Novel metadata (NO full_text, stores vectordb_collection_id)
- `base_scenarios` - Scenario metadata with VectorDB references
- `root_user_scenarios` - User-created "What If" scenarios
- `leaf_user_scenarios` - Forked scenarios (depth 1)
- `scenario_character_changes` - References VectorDB character IDs
- `scenario_event_alterations` - References VectorDB event IDs
- `scenario_setting_modifications` - References VectorDB location IDs
- `conversations` - Conversation instances with character_vectordb_id
- `conversation_message_links` - Join table for message reuse
- `messages` - Individual messages
- `user_follows`, `conversation_likes`, `conversation_memos` - Social features

**VectorDB (Content + Embeddings - 5 Collections)** ← FastAPI ONLY:

- `novel_passages` - Novel text chunks with 768-dim Gemini embeddings
- `characters` - Character descriptions and personality traits (extracted via Gemini)
- `locations` - Setting descriptions
- `events` - Plot events
- `themes` - Thematic analysis

**Architecture Rules**:

| Component   | Allowed DB Access      | Cross-DB Pattern                                  |
| ----------- | ---------------------- | ------------------------------------------------- |
| Spring Boot | ✅ PostgreSQL (JPA)    | Call FastAPI `/api/ai/*` for VectorDB             |
| FastAPI     | ✅ VectorDB (ChromaDB) | Call Spring Boot `/api/internal/*` for PostgreSQL |
| Frontend    | ❌ No direct DB        | Call Spring Boot (metadata) + FastAPI (AI)        |

**Why Hybrid?**:

- **PostgreSQL**: ACID transactions, relational joins, user data integrity
- **VectorDB**: Semantic search (cosine similarity), high-dimensional embeddings, horizontal scaling
- **Cost**: VectorDB scales better for large novel collections (~100GB vs PostgreSQL storage costs)
- **Performance**: Semantic search in VectorDB is 10x faster than pgvector for high-dimensional vectors (768 dims)
- **Separation of Concerns**: Metadata (Spring Boot) vs Content+AI (FastAPI)

**Data Flow Example** (Novel Ingestion):

```
1. FastAPI parses Gutenberg file
2. FastAPI → Spring Boot: POST /api/internal/novels (metadata only)
3. Spring Boot saves to PostgreSQL, returns novel_id
4. FastAPI chunks text, generates embeddings via Gemini Embedding API
5. FastAPI stores passages in VectorDB novel_passages collection with novel_id
6. FastAPI extracts characters via Gemini 2.5 Flash
7. FastAPI stores characters in VectorDB characters collection with novel_id
8. FastAPI → Spring Boot: PATCH /api/internal/novels/{id} (update ingestion_status)
```

### Core Features Architecture

**MSA Communication**:

1. **Frontend → Spring Boot**: All requests (single entry point, Pattern B)
2. **Spring Boot → FastAPI**: AI operations (internal proxy, WebClient)
3. **FastAPI → VectorDB**: Semantic search, embedding storage
4. **FastAPI → Gemini API**: Text generation, embedding generation (not externally exposed)

**Conversation System**:

- **Forking Model**: ROOT-only conversation forking (max depth 1)
- **Message Copy Rule**: Copy **min(6, total_message_count)** from parent
- **Tree Structure**: PostgreSQL with adjacency list + recursive CTEs
- **Context Management**: ~500 tokens for character, 2000 for conversation history (Gemini 2.5 Flash)
- **Streaming**: Server-Sent Events (SSE) for real-time AI responses

**Novel Ingestion Pipeline** (FastAPI):

- Source: Project Gutenberg Dataset (batch import, not real-time API)
- Book content parsing and chunking (200-500 words per passage)
- Vector embedding generation (Gemini Embedding API: 768 dimensions)
- Character/location/event/theme extraction via Gemini 2.5 Flash
- Storage: VectorDB (ChromaDB dev / Pinecone prod)

**Character System**:

- Complete story knowledge approach (simplified vs. temporal consistency)
- System prompts: ~500 tokens defining character context
- Temperature: 0.7-0.8 for creativity + consistency balance
- Prompt re-injection every 10 turns prevents character drift

### Technology Stack

| Layer                | Technology                                                      |
| -------------------- | --------------------------------------------------------------- |
| **Core Backend**     | Spring Boot 3.x (Java 17+), Port 8080                           |
| **AI Backend**       | FastAPI (Python 3.11+), Port 8000                               |
| **Frontend**         | Vue 3 + TypeScript + Vite                                       |
| **Package Managers** | pnpm (Frontend), uv (Python)                                    |
| **Styling**          | Panda CSS (CSS-in-JS with static extraction)                    |
| **UI Components**    | PrimeVue                                                        |
| **State Management** | Pinia                                                           |
| **Database**         | PostgreSQL 15+ (metadata only, 13 core tables)                  |
| **VectorDB**         | ChromaDB (dev) / Pinecone (prod)                                |
| **ORM**              | Spring Data JPA (Spring Boot)                                   |
| **Migrations**       | Flyway                                                          |
| **AI/ML**            | Gemini 2.5 Flash (text gen), Gemini Embedding API (768 dims)    |
| **Task Queue**       | Celery + Redis (async AI operations)                            |
| **Testing**          | JUnit 5 + Mockito (Java), pytest (Python), Vitest (Frontend)    |
| **Code Quality**     | ESLint + Prettier (Frontend), Checkstyle (Java), Black (Python) |

**Database Access Enforcement**:

- Spring Boot: `spring-boot-starter-data-jpa` (PostgreSQL), NO VectorDB libraries
- FastAPI: `chromadb` (dev) / `pinecone-client` (prod), NO PostgreSQL drivers
- Inter-service: `spring-webflux.WebClient` (Java), `httpx` (Python)

## Working with the Multi-Service Architecture

### 🚨 Database Access Rules (CRITICAL)

**Rule #1: Spring Boot → PostgreSQL ONLY**

```java
// ✅ CORRECT: Spring Boot uses JPA for PostgreSQL
@Service
public class ScenarioService {
    @Autowired
    private ScenarioRepository scenarioRepository;  // PostgreSQL via JPA

    @Autowired
    private WebClient aiServiceClient;  // Call FastAPI for VectorDB

    public Scenario createScenario(CreateScenarioRequest request) {
        // 1. Call FastAPI for VectorDB query
        PassageSearchResponse passages = aiServiceClient.post()
            .uri("/api/ai/search/passages")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(PassageSearchResponse.class)
            .block();

        // 2. Save to PostgreSQL with VectorDB IDs
        Scenario scenario = new Scenario();
        scenario.setVectordbPassageIds(passages.getPassageIds());
        return scenarioRepository.save(scenario);  // PostgreSQL
    }
}

// ❌ WRONG: Spring Boot trying to access VectorDB
ChromaClient chroma = new ChromaClient();  // NEVER DO THIS!
VectorDBClient vectordb = new VectorDBClient();  // FORBIDDEN!
```

**Rule #2: FastAPI → VectorDB ONLY**

```python
# ✅ CORRECT: FastAPI uses ChromaDB client
from chromadb import PersistentClient
import httpx

class RAGService:
    def __init__(self):
        # Only FastAPI has VectorDB client
        self.chroma = PersistentClient(path="./chroma_data")
        self.passages = self.chroma.get_collection("novel_passages")

    async def search_passages(self, query: str, novel_id: UUID):
        # VectorDB query ONLY in FastAPI
        results = self.passages.query(
            query_texts=[query],
            where={"novel_id": str(novel_id)},
            n_results=10
        )

        # Call Spring Boot for PostgreSQL metadata
        async with httpx.AsyncClient() as client:
            novel_metadata = await client.get(
                f"http://spring-boot:8080/api/internal/novels/{novel_id}"
            )

        return {"passages": results, "metadata": novel_metadata.json()}

# ❌ WRONG: FastAPI trying to access PostgreSQL
import psycopg2
conn = psycopg2.connect("postgresql://...")  # NEVER DO THIS!
from sqlalchemy import create_engine
engine = create_engine("postgresql://...")  # FORBIDDEN!
```

### Inter-Service Communication Patterns (Pattern B: API Gateway)

**Architecture Decision**: Frontend → Spring Boot (API Gateway) → FastAPI (Internal)

**Pattern 1: Frontend → Spring Boot Proxy → FastAPI**

```typescript
// Frontend: 단일 API 클라이언트 (Spring Boot만 호출)
import api from "@/services/api";

// AI 검색 요청 (Spring Boot Proxy를 통해 FastAPI 호출)
export const searchPassages = async (query: string, novelId: string) => {
  return api.post("/ai/search/passages", {
    query,
    novel_id: novelId,
    top_k: 10,
  });
};

// 대화 생성 요청
export const generateConversation = async (scenarioId: string) => {
  return api.post("/ai/generate", {
    scenario_id: scenarioId,
  });
};
```

```java
// Spring Boot: AIProxyController - FastAPI 프록시
@RestController
@RequestMapping("/api/ai")
public class AIProxyController {

    @Autowired
    private WebClient fastApiClient;

    @PostMapping("/search/passages")
    @PreAuthorize("isAuthenticated()")
    public Mono<ResponseEntity<PassageSearchResponse>> searchPassages(
        @RequestBody PassageSearchRequest request,
        @CurrentUser User user
    ) {
        log.info("[Proxy] Passage search from user={}", user.getId());

        // FastAPI 내부 호출 (외부 노출 안 됨)
        return fastApiClient.post()
            .uri("/api/ai/search/passages")
            .bodyValue(request)
            .retrieve()
            .toEntity(PassageSearchResponse.class)
            .doOnSuccess(response ->
                log.info("[Proxy] Search completed: {} results",
                         response.getBody().getPassageIds().size())
            );
    }

    // SSE 스트리밍 프록시
    @GetMapping(value = "/stream/{conversationId}",
                produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @PreAuthorize("isAuthenticated()")
    public Flux<ServerSentEvent<String>> streamMessage(
        @PathVariable UUID conversationId,
        @RequestParam String userMessage
    ) {
        return fastApiClient.get()
            .uri(uriBuilder -> uriBuilder
                .path("/api/ai/stream/" + conversationId)
                .queryParam("user_message", userMessage)
                .build())
            .retrieve()
            .bodyToFlux(String.class)
            .map(token -> ServerSentEvent.<String>builder().data(token).build());
    }
}
```

**Pattern 2: FastAPI → Spring Boot (PostgreSQL Metadata)**

```python
# ai-backend: Call Spring Boot for PostgreSQL data
class NovelIngestionService:
    async def save_novel_metadata(self, metadata: dict) -> UUID:
        """FastAPI NEVER touches PostgreSQL directly"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://spring-boot:8080/api/internal/novels",
                json=metadata,
                headers={"X-Internal-Service": "fastapi"},
                timeout=30.0
            )
            response.raise_for_status()
            return UUID(response.json()["id"])

    async def ingest_novel(self, file_path: str):
        # 1. Parse Gutenberg file
        text = self.parse_gutenberg_file(file_path)
        metadata = self.extract_metadata(text)

        # 2. Save metadata to PostgreSQL via Spring Boot
        novel_id = await self.save_novel_metadata(metadata)

        # 3. Process content and save to VectorDB (FastAPI only)
        passages = self.chunk_text(text)
        embeddings = await self.generate_embeddings(passages)
        await self.store_in_vectordb(novel_id, passages, embeddings)
```

**Architecture Benefits (Pattern B)**:

- ✅ **Security**: Prevents external FastAPI exposure, protects Gemini API keys
- ✅ **Simplicity**: Frontend manages only 1 API client
- ✅ **Centralized Logging**: All requests go through Spring Boot for unified tracking
- ✅ **Cost**: Saves $700/year on SSL/domain costs (2 → 1)
- ⚠️ **Latency**: +50ms proxy overhead (negligible 1% on 5000ms AI tasks)

**Migration Guide**: [docs/PATTERN_B_MIGRATION_GUIDE.md](./docs/PATTERN_B_MIGRATION_GUIDE.md)  
**Pattern Comparison**: [docs/FRONTEND_BACKEND_ACCESS_PATTERN_COMPARISON.md](./docs/FRONTEND_BACKEND_ACCESS_PATTERN_COMPARISON.md)

````

### Database Schema Patterns

**Database Design Philosophy**: Fully normalized relational design with 32 tables (21 core + 11 normalized relationship tables). All JSONB columns have been eliminated in favor of structured relational tables for better queryability, type safety, and performance.

**Core Tables**:

```sql
-- Novels table with series and copyright metadata
CREATE TABLE novels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    author VARCHAR(200) NOT NULL,
    original_language VARCHAR(10),
    era VARCHAR(100),
    genre VARCHAR(100),
    full_text_s3_path VARCHAR(500),
    total_word_count INTEGER,
    publication_year INTEGER,
    isbn VARCHAR(20),
    series_title VARCHAR(300),  -- For book series (e.g., 'The Barton books for girls')
    series_number INTEGER,      -- Book number in series (e.g., 8)
    copyright_status VARCHAR(100) DEFAULT 'unknown',  -- 'public_domain', 'copyrighted', 'creative_commons', 'unknown'
    copyright_note TEXT,        -- Detailed copyright info (e.g., 'Public domain in the USA')
    cover_image_url VARCHAR(500),
    description TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    creator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_novels_series ON novels(series_title, series_number);
CREATE INDEX idx_novels_copyright ON novels(copyright_status);
````

**Normalized Character Analysis Tables**:

```sql
-- Character aliases (normalized from characters.aliases JSONB)
CREATE TABLE character_aliases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    alias VARCHAR(255) NOT NULL,
    usage_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, alias)
);

-- Character personality traits (normalized from characters.personality_traits JSONB)
CREATE TABLE character_personality_traits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    trait VARCHAR(100) NOT NULL,
    intensity DECIMAL(3,2) CHECK (intensity BETWEEN 0 AND 1),
    evidence_passage_id UUID REFERENCES novel_passages(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, trait)
);

-- Character relationships (normalized from characters.relationships JSONB)
CREATE TABLE character_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    related_character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    relationship_description TEXT,
    strength DECIMAL(3,2) CHECK (strength BETWEEN 0 AND 1),
    is_mutual BOOLEAN DEFAULT FALSE,
    first_interaction_chapter_id UUID REFERENCES novel_chapters(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK(character_id != related_character_id)
);
```

**Scenario Type-Specific Tables** (normalized from root/leaf_user_scenarios.custom_parameters JSONB):

```sql
-- Character changes in What If scenarios
CREATE TABLE scenario_character_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
    leaf_scenario_id UUID REFERENCES leaf_user_scenarios(id) ON DELETE CASCADE,
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    attribute VARCHAR(100) NOT NULL,
    original_value TEXT,
    new_value TEXT NOT NULL,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK((root_scenario_id IS NOT NULL AND leaf_scenario_id IS NULL) OR
          (root_scenario_id IS NULL AND leaf_scenario_id IS NOT NULL))
);

-- Event alterations in What If scenarios
CREATE TABLE scenario_event_alterations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
    leaf_scenario_id UUID REFERENCES leaf_user_scenarios(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    alteration_type VARCHAR(50) NOT NULL,
    new_outcome TEXT NOT NULL,
    cascading_effects TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK((root_scenario_id IS NOT NULL AND leaf_scenario_id IS NULL) OR
          (root_scenario_id IS NULL AND leaf_scenario_id IS NOT NULL))
);

-- Setting modifications in What If scenarios
CREATE TABLE scenario_setting_modifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
    leaf_scenario_id UUID REFERENCES leaf_user_scenarios(id) ON DELETE CASCADE,
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    modification_type VARCHAR(50) NOT NULL,
    new_description TEXT NOT NULL,
    impact_scope TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK((root_scenario_id IS NOT NULL AND leaf_scenario_id IS NULL) OR
          (root_scenario_id IS NULL AND leaf_scenario_id IS NOT NULL))
);
```

**Conversation Tree (PostgreSQL)** with Join Table Pattern:

```sql
-- Adjacency List model for tree structure
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    root_scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE SET NULL,
    leaf_scenario_id UUID REFERENCES leaf_user_scenarios(id) ON DELETE SET NULL,
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    fork_depth INTEGER DEFAULT 0 CHECK(fork_depth <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK((root_scenario_id IS NOT NULL AND leaf_scenario_id IS NULL) OR
          (root_scenario_id IS NULL AND leaf_scenario_id IS NOT NULL))
);

-- Join table pattern for message reuse across forks
CREATE TABLE conversation_message_links (
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    message_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, message_order)
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role VARCHAR(20) NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recursive CTE for tree traversal
WITH RECURSIVE conversation_tree AS (
    SELECT id, parent_conversation_id, 0 as depth
    FROM conversations
    WHERE id = ?
    UNION ALL
    SELECT c.id, c.parent_conversation_id, ct.depth + 1
    FROM conversations c
    JOIN conversation_tree ct ON c.parent_conversation_id = ct.id
)
SELECT * FROM conversation_tree;
```

**Spring Data JPA Entities**:

```java
@Entity
@Table(name = "conversations")
public class Conversation {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "parent_id")
    private Conversation parent;

    @OneToMany(mappedBy = "parent", cascade = CascadeType.ALL)
    private List<Conversation> children = new ArrayList<>();

    private Integer forkDepth = 0;

    // Getters, setters, etc.
}
```

### OpenAI Integration Patterns

**Context Window Management**:

```java
public class ConversationContextBuilder {
    private static final int MAX_CONTEXT_TOKENS = 4000;
    private static final int CHARACTER_PROMPT_TOKENS = 500;
    private static final int CONVERSATION_HISTORY_TOKENS = 2000;

    public List<ChatMessage> buildContext(Conversation conv, Character character) {
        List<ChatMessage> messages = new ArrayList<>();

        // 1. System prompt with character definition
        messages.add(new ChatMessage("system", character.getPrompt()));

        // 2. Sliding window of recent messages
        List<Message> recentMessages = getRecentMessages(conv, 10);
        for (Message msg : recentMessages) {
            messages.add(new ChatMessage(msg.getRole(), msg.getContent()));
        }

        return messages;
    }
}
```

**Streaming Responses (SSE)**:

```java
@GetMapping(value = "/stream/{conversationId}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<ServerSentEvent<String>> streamResponse(
    @PathVariable Long conversationId,
    @RequestParam String userMessage
) {
    return openAiService.streamChatCompletion(conversationId, userMessage)
        .map(chunk -> ServerSentEvent.<String>builder()
            .data(chunk)
            .build());
}
```

## Key Design Patterns

### Conversation Forking Pattern

- **Limited Mid-Conversation Forking**: MVP allows forking up to depth 6 to manage complexity
- Fork inherits all parent context (messages up to fork point)
- Each fork creates new conversation branch with parent reference
- Tree visualization uses recursive queries for lineage display
- "Gaji" as verb: "Let's gaji this discussion" makes forking intuitive

### Character System Pattern

- **Complete Story Knowledge Approach**: Characters know entire story eliminating temporal consistency issues
- System prompt template: "You are [Character] who has experienced [Complete Story]. You remember all events..."
- Temperature 0.7-0.8 balances creativity with consistency
- Prompt re-injection every 10 turns prevents character drift
- No need for complex spatiotemporal tracking (simplified design)

### RAG Pipeline Pattern

- **Dual Backend Separation**: Core backend focuses on business logic, AI backend handles all ML/NLP
- Book content → Chunking → Embedding → Vector storage
- Character extraction via NLP analysis
- Relationship graph extraction for visualization
- Semantic search provides context for character responses

### Cost Optimization Patterns

- **Prompt compression**: Remove unnecessary context, compress system prompts (30-50% savings)
- **Response caching**: Semantic matching for similar queries (15-30% savings)
- **Model cascading**: Route simple tasks to GPT-3.5-turbo, complex to GPT-4o (60-80% savings)
- **Smart context management**: Sliding window, truncate old history
- Alternative models: Claude 3 Haiku (50% cheaper), Gemini 1.5 Flash (63% cheaper)

### Frontend State Management (Pinia)

```typescript
// stores/conversation.ts
export const useConversationStore = defineStore("conversation", {
  state: () => ({
    currentConversation: null,
    messages: [],
    conversationTree: null,
    isStreaming: false,
  }),

  actions: {
    async forkConversation(parentId: number, atMessageIndex: number) {
      // Create new conversation branch
      const newConv = await coreApi.post("/conversations/fork", {
        parentId,
        forkAtMessage: atMessageIndex,
      });

      // Inherit parent context
      this.messages = this.messages.slice(0, atMessageIndex + 1);
      this.currentConversation = newConv;
    },

    async streamMessage(content: string) {
      this.isStreaming = true;
      const eventSource = new EventSource(
        `/api/conversations/${this.currentConversation.id}/stream?message=${content}`
      );

      eventSource.onmessage = (event) => {
        this.appendToLastMessage(event.data);
      };

      eventSource.onerror = () => {
        this.isStreaming = false;
        eventSource.close();
      };
    },
  },
});
```

### Frontend Styling Patterns (Panda CSS)

**Component Styling with Panda CSS**:

```typescript
// components/ChatMessage.vue
<script setup lang="ts">
import { css } from '@/styled-system/css'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
}>()

const messageStyles = css({
  p: '4',
  rounded: 'lg',
  maxW: '2xl',
  bg: props.role === 'user' ? 'blue.50' : 'gray.50',
  borderLeft: '4px solid',
  borderColor: props.role === 'user' ? 'blue.500' : 'gray.400',
  _hover: {
    shadow: 'md'
  }
})

const avatarStyles = css({
  w: '10',
  h: '10',
  rounded: 'full',
  bg: props.role === 'user' ? 'blue.500' : 'teal.500',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: 'white',
  fontWeight: 'bold'
})
</script>

<template>
  <div :class="messageStyles">
    <div :class="avatarStyles">
      {{ role === 'user' ? 'U' : 'A' }}
    </div>
    <p>{{ content }}</p>
  </div>
</template>
```

**Responsive Design with Breakpoints**:

```typescript
import { css } from "@/styled-system/css";

const containerStyles = css({
  px: { base: "4", md: "8", lg: "12" },
  py: { base: "6", md: "10" },
  maxW: "7xl",
  mx: "auto",
  display: "grid",
  gridTemplateColumns: { base: "1", md: "2", lg: "3" },
  gap: { base: "4", md: "6", lg: "8" },
});
```

**Theme Tokens Configuration** (`panda.config.ts`):

```typescript
import { defineConfig } from "@pandacss/dev";

export default defineConfig({
  preflight: true,
  include: ["./src/**/*.{js,jsx,ts,tsx,vue}"],
  exclude: [],
  theme: {
    extend: {
      tokens: {
        colors: {
          primary: { value: "#3B82F6" },
          secondary: { value: "#10B981" },
          accent: { value: "#8B5CF6" },
        },
        spacing: {
          section: { value: "5rem" },
        },
      },
    },
  },
  outdir: "styled-system",
});
```

### UI Components (PrimeVue)

**Using PrimeVue Components**:

```vue
<!-- components/ConversationList.vue -->
<script setup lang="ts">
import { ref } from "vue";
import Button from "primevue/button";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Dialog from "primevue/dialog";
import { css } from "@/styled-system/css";

const conversations = ref([]);
const showForkDialog = ref(false);

const tableStyles = css({
  mt: "4",
  "& .p-datatable-header": {
    bg: "gray.50",
    borderBottom: "2px solid",
    borderColor: "gray.200",
  },
});
</script>

<template>
  <div>
    <div
      :class="
        css({ display: 'flex', justifyContent: 'space-between', mb: '4' })
      "
    >
      <h2 :class="css({ fontSize: '2xl', fontWeight: 'bold' })">
        My Conversations
      </h2>
      <Button
        label="New Conversation"
        icon="pi pi-plus"
        @click="createConversation"
      />
    </div>

    <DataTable :value="conversations" :class="tableStyles" paginator :rows="10">
      <Column field="title" header="Title" sortable />
      <Column field="book" header="Book" sortable />
      <Column field="updatedAt" header="Last Updated" sortable />
      <Column>
        <template #body="{ data }">
          <Button
            icon="pi pi-code-branch"
            label="Fork"
            size="small"
            @click="forkConversation(data.id)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="showForkDialog"
      header="Fork Conversation"
      :modal="true"
    >
      <p>Select a message to fork from...</p>
    </Dialog>
  </div>
</template>
```

**PrimeVue Theme Configuration** (`main.ts`):

```typescript
import { createApp } from "vue";
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import Aura from "@primevue/themes/aura";
import "primeicons/primeicons.css";

import App from "./App.vue";

const app = createApp(App);

app.use(createPinia());
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      prefix: "p",
      darkModeSelector: ".dark-mode",
      cssLayer: {
        name: "primevue",
        order: "Panda-base, primevue, Panda-utilities",
      },
    },
  },
});

app.mount("#app");
```

## Documentation Structure

Comprehensive product documentation lives in `docs/`:

- `docs/PRD.md` - Complete product requirements document with market analysis, What If scenario strategy
- `docs/architecture.md` - Technical architecture specification with Epic 0-6 implementation plan
- `docs/USER_FLOW.md` - User journey and interaction flows
- `docs/TEAM_ASSIGNMENTS.md` - Development team roles and responsibilities
- `docs/epics/*.md` - Epic-level feature specifications (7 epics: 0-6)
- `docs/stories/*.md` - **ALL 35 detailed user stories fully documented** with:
  - Complete acceptance criteria (10-15 per story)
  - Production-ready code examples (SQL, Java, Python, Vue.js)
  - Comprehensive QA checklists (5-6 categories, 20-27 test cases)
  - Bi-directional dependency mapping
  - Estimated effort in hours (~270 hours total)
- `docs/use-cases/` - Specific use case scenarios
- `docs/v0/` - V0 AI prompts for rapid prototyping

**Documentation Status**: 100% Complete (35/35 stories across 7 epics)

**Always review relevant docs before implementing features to understand requirements and constraints.**

## Critical Constraints

### What NOT to Do

1. **Never compromise conversation forking integrity**: Tree structure must remain consistent
2. **Never skip context window management**: OpenAI has hard token limits (4k for GPT-3.5-turbo)
3. **Never ignore API rate limits**: Implement exponential backoff and request queuing
4. **Never store sensitive data unencrypted**: Use proper password hashing, secure tokens
5. **Never make N+1 database queries**: Use JPA fetch joins and proper eager loading
6. **Never mix business logic between backends**: Core = business, AI = ML/NLP only
7. **Never bypass CORS in production**: Configure proper CORS policies for all backends

### Performance Requirements

- API response time < 200ms for non-AI endpoints
- Streaming response latency < 500ms for first token
- Database queries < 100ms for tree traversal (depth 10)
- Frontend bundle size < 500KB gzipped
- Support 100 concurrent users minimum (MVP scale)

### Cost Management Requirements

- Free tier: 10 forks/month per user, GPT-3.5-turbo only
- Implement aggressive caching (semantic similarity matching)
- Monitor OpenAI API costs daily (alert if > $50/day)
- Target < $0.0015 per conversation average
- Scale threshold: Consider self-hosting at 35K+ conversations/month

## Next Steps for Development

According to the PRD and epic structure, **all 35 stories are fully documented** and ready for implementation. The recommended implementation order follows epic dependencies:

1. **Epic 0**: Project Initialization & Development Foundation (6 stories - 38 hours)

   - 0.1: Repository Setup & Structure
   - 0.2: Docker Development Environment
   - 0.3: Database Setup (PostgreSQL + Flyway)
   - 0.4: Backend API Foundation (Spring Boot)
   - 0.5: Frontend Foundation (Vue 3 + Vite + PandaCSS)
   - 0.6: CI/CD Pipeline

2. **Epic 1**: Scenario Foundation (5 stories - 42 hours)

   - 1.1: Scenario Data Model & CRUD
   - 1.2: Scenario Parameter Validation
   - 1.3: Scenario Creation Wizard (multi-step UI)
   - 1.4: Scenario Browse & Detail View
   - 1.5: Scenario Edit & Deletion

3. **Epic 2**: AI Adaptation Layer (4 stories - 34 hours)

   - 2.1: OpenAI Integration Service
   - 2.2: Prompt Template System (What If scenarios)
   - 2.3: AI Response Processing (streaming, context)
   - 2.4: Error Handling & Rate Limiting

4. **Epic 4**: Conversation System (3 stories - 26 hours)

   - 4.1: Conversation Data Model (with ROOT-only fork constraints)
   - 4.2: Conversation Chat Interface (SSE streaming)
   - 4.3: Conversation Forking UI (min(6, total) message copy)

5. **Epic 3**: Scenario Discovery (5 stories - 45 hours)

   - 3.1: Scenario Browse UI (cards, infinite scroll)
   - 3.2: Scenario Forking Backend (meta-scenarios)
   - 3.3: Scenario Forking UI (fork modal)
   - 3.4: Scenario Search & Filtering (pg_trgm, GIN indexes)
   - 3.5: Social Sharing with og:image (Puppeteer)

6. **Epic 5**: Tree Visualization (3 stories - 26 hours)

   - 5.1: Tree Data Structure (recursive CTEs)
   - 5.2: Tree Visualization Component (D3.js)
   - 5.3: Tree Navigation & Interaction

7. **Epic 6**: User Authentication & Social (9 stories - 59 hours)
   - 6.1: Auth Backend (JWT)
   - 6.2: Auth Frontend (Pinia)
   - 6.3: User Profile & Edit
   - 6.4: Follow System Backend
   - 6.5: Follow/Unfollow UI
   - 6.6: Like System Backend
   - 6.7: Like Button UI & Feed
   - 6.8: Memo System Backend
   - 6.9: Memo UI

**Total Implementation Timeline**: 10-14 weeks for complete MVP

**Current Phase**: Documentation complete, ready to begin Epic 0.1 implementation

## Troubleshooting

### Backend Issues

**Spring Boot fails to start**

- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify database connection in `application.yml`
- Check port 8080 is not already in use: `lsof -i :8080`
- Review logs in `core-backend/logs/` directory

**FastAPI service errors**

- Ensure virtual environment is activated
- Install all dependencies: `uv pip install -r requirements.txt`
- Check port 8000 availability: `lsof -i :8000`
- Verify OpenAI API key in environment variables

**Database migration issues**

- Check Flyway migration files in `db/migration/`
- View migration status: `./gradlew flywayInfo`
- If needed, clean and re-migrate: `./gradlew flywayClean flywayMigrate`

### Frontend Issues

**pnpm install fails**

- Ensure Node.js >= 18 is installed
- Delete `node_modules` and `pnpm-lock.yaml`, retry
- Clear pnpm cache: `pnpm store prune`

**Panda CSS codegen issues**

- Run `pnpm prepare` manually to regenerate styled-system
- Check `panda.config.ts` for syntax errors
- Ensure `styled-system/` directory is gitignored but generated locally
- Verify PostCSS configuration if using with build tools

**Development server won't start**

- Check port 3000 availability
- Verify backend URLs in environment config
- Check for TypeScript errors: `pnpm type-check`
- Ensure PandaCSS has run codegen: `pnpm prepare`

### Integration Issues

**CORS errors between frontend and backend**

- Verify CORS configuration in Spring Boot `WebConfig`
- Check FastAPI CORS middleware settings
- Ensure frontend is using correct backend URLs

**OpenAI API rate limit errors**

- Implement exponential backoff in API client
- Add request queuing mechanism
- Monitor rate limit headers in responses
- Consider upgrading OpenAI tier if needed

**Streaming responses not working**

- Check SSE configuration in backend
- Verify EventSource setup in frontend
- Inspect network tab for SSE connection status
- Ensure proper error handling for connection drops

### Database Performance

**Slow recursive queries for conversation trees**

- Add index on `parent_id` column: `CREATE INDEX idx_conversations_parent ON conversations(parent_id)`
- Add index on `conversation_id` in messages: `CREATE INDEX idx_messages_conversation ON messages(conversation_id)`
- Use `EXPLAIN ANALYZE` to diagnose query performance
- Consider materialized paths if depth exceeds 15 levels

**N+1 query problems**

- Use JPA `@EntityGraph` or `JOIN FETCH` in queries
- Enable Hibernate query logging to identify issues
- Review repository methods for proper eager loading
