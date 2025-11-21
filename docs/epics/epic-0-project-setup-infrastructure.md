# Epic 0: Project Setup & Infrastructure

## Epic Goal

Establish the foundational technical infrastructure for Gaji platform with **Pattern B (API Gateway)** architecture: Spring Boot API Gateway (port 8080) + FastAPI AI Backend (port 8000, internal-only), Vue.js frontend with PandaCSS, **hybrid database** (PostgreSQL for metadata + VectorDB for content/embeddings), and **Gemini API integration** for AI-powered character conversations.

## User Value

While users don't directly interact with infrastructure, this epic ensures:

- **Enhanced Security**: FastAPI and Gemini API keys protected from external access
- **Cost Efficiency**: $700/year saved on SSL certificates and domains
- **Performance**: SSE streaming for real-time AI responses
- **Scalability**: Hybrid database architecture optimized for metadata (PostgreSQL) and semantic search (VectorDB)

## Timeline

**Week 1-2 of MVP development**

- **Infrastructure Setup**: Days 1-3 (Stories 0.1-0.6)
- **Data Import**: Day 4 (Story 0.7)

## Stories Overview

### Phase 1: Infrastructure Setup (~36 hours)

**Stories 0.1-0.6**: Spring Boot API Gateway, FastAPI AI service (internal-only), PostgreSQL (13 metadata tables), Vue.js + PandaCSS + PrimeVue, Docker, health checks

### Phase 2: Data Import (~3 hours)

**Story 0.7**: Import pre-processed Project Gutenberg dataset (passages, characters, locations, events, themes) into VectorDB, create PostgreSQL metadata via Spring Boot API

**Total Epic Effort**: ~39 hours (~5 working days for 2 engineers)

## Stories

### Story 0.1: Spring Boot Backend - API Gateway Setup

**Priority: P0 - Critical**

**Description**: Initialize Spring Boot application as **API Gateway** with WebClient for proxying FastAPI requests, REST API endpoints, and JWT authentication. Implements **Pattern B** architecture where frontend communicates only with Spring Boot.

**Acceptance Criteria**:

- [ ] Spring Boot 3.2+ project initialized with Gradle
- [ ] Dependencies configured:
  - Spring Web (REST API)
  - Spring WebFlux WebClient (FastAPI proxy client)
  - MyBatis (PostgreSQL SQL Mapper)
  - Spring Security (JWT authentication)
  - PostgreSQL Driver
  - Lombok (reduce boilerplate)
  - Spring Validation
  - Spring Boot Actuator (health checks)
- [ ] Package structure created:
  ```
  com.gaji.corebackend/
  ├── config/          # WebClient, Security, CORS
  ├── controller/      # REST controllers + AI proxy
  ├── service/         # Business logic
  ├── mapper/          # MyBatis Mapper interfaces (PostgreSQL only)
  ├── domain/          # Domain models (13 tables)
  ├── dto/             # Request/response DTOs
  ├── client/          # FastAPIClient (WebClient)
  ├── exception/       # Custom exceptions
  └── util/            # Utility classes
  ```
- [ ] application.yml configured:
  - Profiles: dev, staging, prod
  - `fastapi.base-url: http://localhost:8000` (internal proxy)
  - PostgreSQL connection (metadata only)
- [ ] WebClient configured for FastAPI proxy:
  - Base URL: `http://localhost:8000`
  - Timeout: 60 seconds (AI operations)
  - Error handling with circuit breaker pattern
- [ ] CORS configuration for frontend:
  - Dev: `http://localhost:3000` (Vite default)
  - Prod: `https://gaji.app`
- [ ] API Gateway routes:
  - `/api/v1/*` - Spring Boot direct endpoints
  - `/api/v1/ai/*` - Proxy to FastAPI (e.g., `/api/v1/ai/chat` → `http://localhost:8000/api/chat`)
- [ ] Global exception handler for consistent error responses
- [ ] Health check endpoint: `GET /actuator/health` (includes FastAPI health check)
- [ ] Swagger/OpenAPI documentation auto-generated
- [ ] Logging configured (SLF4J + Logback) with request/response logging
- [ ] Application runs on port 8080

**Technical Notes**:

- **Pattern B Implementation**: Frontend → Spring Boot ONLY. Spring Boot proxies AI requests to FastAPI internally.
- **Security Benefit**: FastAPI URL and Gemini API keys never exposed to frontend
- **Database Access**: Spring Boot accesses PostgreSQL ONLY (no VectorDB libraries)
- Use Spring Boot 3.2+ for Virtual Threads support (improves proxy throughput)
- Configure connection pooling: HikariCP with max 20 connections

**Estimated Effort**: 6 hours

---

### Story 0.2: FastAPI AI Service Setup (Internal-Only)

**Priority: P0 - Critical**

**Description**: Initialize FastAPI service for **internal AI/ML operations** including RAG pipeline, **Gemini 2.5 Flash API integration**, and VectorDB management. Service is **NOT externally exposed** - accessed only via Spring Boot proxy.

**Acceptance Criteria**:

- [x] Python 3.11+ project initialized with **uv** package manager
- [x] Dependencies configured (requirements.txt):
  - FastAPI 0.121.3+
  - Uvicorn (ASGI server)
  - Pydantic (data validation)
  - pydantic-settings 2.12.0+ (settings management)
  - **google-generativeai>=0.8.3** (Gemini API SDK - Gemini 2.5 Flash + Embedding API, 레거시 - google-genai 1.0+ 권장)
  - **chromadb>=1.3.5** (VectorDB for dev, Settings 클래스 제거됨)
  - **pinecone>=8.0** (VectorDB for prod, 새 SDK)
  - httpx (async HTTP client for Spring Boot callbacks)
  - celery 5.5.3+ (async task queue)
  - redis>=7.1.0 (Celery broker + Long Polling task storage)
  - tenacity 9.0.0+ (retry logic)
  - structlog 25.1.0+ (structured logging)
  - numpy<2.0.0 (ChromaDB 호환성)
- [ ] Project structure created:
  ```
  ai-backend/
  ├── app/
  │   ├── main.py              # FastAPI app
  │   ├── api/
  │   │   ├── chat.py          # Conversation endpoints
  │   │   ├── ingestion.py     # Novel processing
  │   │   └── health.py        # Health check
  │   ├── services/
  │   │   ├── gemini_client.py # Gemini API integration
  │   │   ├── rag_service.py   # RAG pipeline
  │   │   ├── vectordb_client.py # ChromaDB/Pinecone
  │   │   └── novel_ingestion.py # Gutenberg parsing
  │   ├── models/
  │   │   └── schemas.py       # Pydantic models
  │   ├── config.py            # Environment config
  │   ├── celery_app.py        # Celery configuration
  │   └── utils/
  ├── tests/
  └── requirements.txt
  ```
- [ ] Environment configuration (.env):
  - `GEMINI_API_KEY` (Gemini 2.5 Flash API key)
  - `VECTORDB_TYPE=chromadb` (dev) / `pinecone` (prod)
  - `SPRING_BOOT_URL=http://localhost:8080` (for callbacks)
  - `REDIS_URL=redis://localhost:6379` (Celery broker + Long Polling task storage)
- [ ] Gemini API client configured:
  - **Gemini 2.5 Flash** for text generation: `gemini-2.5-flash`
  - **Gemini Embedding API** for 768-dim embeddings: `text-embedding-004`
  - Temperature: 0.6-0.8 for character conversations (configurable by scenario type)
  - Timeout: 30 seconds
  - Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
- [ ] VectorDB client configured:
  - ChromaDB (dev): Persistent client with local storage
  - Pinecone (prod): Cloud-hosted with API key
  - 5 collections: `novel_passages`, `characters`, `locations`, `events`, `themes`
- [ ] CORS middleware:
  - **Internal access only**: Allow `http://localhost:8080` (Spring Boot)
  - **NO external origins** (not exposed to frontend)
- [ ] Health check endpoint: `GET /health`
  - Returns Gemini API status, VectorDB connection status
- [ ] OpenAPI documentation at `/docs` (internal use only)
- [ ] Logging configured (structlog for JSON logs)
- [ ] Application runs on port 8000 (internal-only, not publicly exposed)
- [ ] Celery worker configured for async tasks (novel ingestion)
- [ ] Base API versioning: `/api/*`

**Technical Notes**:

- **Pattern B Implementation**: FastAPI is NOT externally exposed. Only Spring Boot can call it.
- **Security Benefit**: Gemini API key never exposed to frontend
- **Database Access**: FastAPI accesses VectorDB ONLY (no PostgreSQL drivers)
- **No PostgreSQL Access**: Use Spring Boot REST API for metadata queries
- Use async/await throughout for better performance
- **Gemini API Integration**:
  - google-generativeai>=0.8.3 (레거시 SDK, 새 프로젝트는 google-genai 1.0+ 권장)
  - Gemini 2.5 Flash: 1M input tokens, 8K output tokens
  - Pricing: $0.075 per 1M input, $0.30 per 1M output
  - Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
  - Circuit breaker: Fail after 5 consecutive errors
- **VectorDB Configuration**:
  - ChromaDB>=1.3.5 (dev): Persistent client with local storage at `./chroma_data`
    - API 변경: chromadb.config.Settings 클래스 제거됨
  - Pinecone>=8.0 (prod): Cloud-hosted with index name `gaji-prod`
    - 새 SDK: Pinecone(api_key) 생성자 사용
  - Connection pooling: min 5, max 15 connections
- **Redis>=7.1.0 for Long Polling**: Store task status with 600-second TTL (10 minutes)
  - protocol=3 지원

**Estimated Effort**: 6 hours

---

### Story 0.3: PostgreSQL Database Setup & Flyway Migrations (Metadata Only)

**Priority: P0 - Critical**

**Description**: Set up PostgreSQL database for **metadata storage only** (13 tables) using Flyway migrations. Novel content and embeddings are stored in VectorDB (ChromaDB/Pinecone). This implements the **hybrid database architecture**.

**Acceptance Criteria**:

- [ ] PostgreSQL 15+ installed/configured (Docker or Railway cloud)
- [ ] Database created: `gaji_db`
- [ ] PostgreSQL extensions enabled:
  - `uuid-ossp` for UUID generation
  - `pg_trgm` for full-text search
- [ ] Flyway configured in Spring Boot for schema migrations
- [ ] **13 metadata tables total** (NO content storage):
  - **Core Tables** (3):
    - `V1__create_users_table.sql`
    - `V2__create_novels_table.sql` (metadata only, stores `vectordb_collection_id`, NO `full_text` column)
    - `V3__create_base_scenarios_table.sql` (stores VectorDB passage IDs as ARRAY)
  - **Scenario Tables** (5):
    - `V4__create_root_user_scenarios_table.sql`
    - `V5__create_leaf_user_scenarios_table.sql`
    - `V6__create_scenario_character_changes_table.sql` (stores `character_vectordb_id`)
    - `V7__create_scenario_event_alterations_table.sql` (stores `event_vectordb_id`)
    - `V8__create_scenario_setting_modifications_table.sql` (stores `location_vectordb_id`)
  - **Conversation Tables** (3):
    - `V9__create_conversations_table.sql` (stores `character_vectordb_id`)
    - `V10__create_messages_table.sql`
    - `V11__create_conversation_message_links_table.sql`
  - **Social Features** (3):
    - `V12__create_user_follows_table.sql`
    - `V13__create_conversation_likes_table.sql`
    - `V14__create_conversation_memos_table.sql`
- [ ] **Hybrid Database Cross-References**:
  - `novels.vectordb_collection_id` (UUID) → VectorDB collection name
  - `base_scenarios.vectordb_passage_ids` (UUID[]) → VectorDB passage documents
  - `scenario_character_changes.character_vectordb_id` (UUID) → VectorDB characters collection
  - `conversations.character_vectordb_id` (UUID) → VectorDB characters collection
- [ ] **NO content columns**:
  - ❌ NO `novels.full_text` (stored in VectorDB `novel_passages` collection)
  - ❌ NO `characters` table (stored in VectorDB `characters` collection)
  - ❌ NO `locations` table (stored in VectorDB `locations` collection)
  - ❌ NO JSONB columns (all data normalized)
- [ ] CASCADE DELETE on all foreign keys for automatic cleanup
- [ ] B-tree indexes on:
  - All FK columns
  - `novels.title`, `novels.author` (search optimization)
  - `base_scenarios.novel_id`, `root_user_scenarios.base_scenario_id`
  - `conversations.user_id`, `conversations.scenario_id`
- [ ] Connection pooling configured (HikariCP):
  - Spring Boot: min 5, max 20 connections
- [ ] Database connection verified from Spring Boot
- [ ] Rollback testing: migrations can be reverted cleanly
- [ ] Seed data script for development:
  - 10 sample users
  - 3 sample novels (metadata only, with `vectordb_collection_id`)

**Schema Highlights** (Metadata Only):

```sql
-- V1__create_users_table.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  bio TEXT CHECK (length(bio) <= 500),
  avatar_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- V2__create_novels_table.sql (Metadata Only - NO full_text)
CREATE TABLE novels (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(500) NOT NULL,
  author VARCHAR(200) NOT NULL,
  publication_year INTEGER,
  genre VARCHAR(100),
  vectordb_collection_id VARCHAR(255) NOT NULL UNIQUE,  -- Reference to VectorDB
  ingestion_status VARCHAR(50) DEFAULT 'pending',       -- pending, processing, completed, failed
  total_passages_count INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- NOTE: Novel content is in VectorDB 'novel_passages' collection
-- NOTE: Characters are in VectorDB 'characters' collection

-- V3__create_base_scenarios_table.sql
CREATE TABLE base_scenarios (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  vectordb_passage_ids UUID[] NOT NULL,  -- Array of VectorDB passage IDs
  character_vectordb_ids UUID[],         -- Array of VectorDB character IDs
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- V6__create_scenario_character_changes_table.sql
CREATE TABLE scenario_character_changes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  scenario_id UUID NOT NULL REFERENCES root_user_scenarios(id) ON DELETE CASCADE,
  character_vectordb_id UUID NOT NULL,   -- Reference to VectorDB characters collection
  attribute VARCHAR(100) NOT NULL,
  original_value TEXT,
  new_value TEXT NOT NULL,
  reasoning TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- NOTE: Character data (name, description, personality) is in VectorDB

-- V9__create_conversations_table.sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  scenario_id UUID REFERENCES root_user_scenarios(id) ON DELETE SET NULL,
  character_vectordb_id UUID NOT NULL,   -- Reference to VectorDB characters collection
  parent_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
  title VARCHAR(200),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CHECK (parent_conversation_id IS NULL OR
         (SELECT parent_conversation_id FROM conversations WHERE id = parent_conversation_id) IS NULL)
);
-- NOTE: ROOT-only forking (max depth 1)

-- V12__create_user_follows_table.sql
CREATE TABLE user_follows (
  follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  followee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (follower_id, followee_id),
  CHECK (follower_id != followee_id)
);

-- V13__create_conversation_likes_table.sql
CREATE TABLE conversation_likes (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, conversation_id)
);

-- V14__create_conversation_memos_table.sql
CREATE TABLE conversation_memos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  content TEXT NOT NULL CHECK (length(content) <= 2000),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, conversation_id)
);
```

**Technical Notes**:

- **Hybrid Database Philosophy**: PostgreSQL stores ONLY relational metadata (13 tables). VectorDB stores content + embeddings (5 collections).
- **Cross-Database References**: UUIDs link PostgreSQL metadata to VectorDB documents
- **Why Metadata-Only?**:
  - Novel passages: ~100GB for 1000 books → Better in VectorDB
  - Character descriptions: Require semantic search → Better in VectorDB
  - Metadata queries: ACID transactions, complex JOINs → Better in PostgreSQL
- **VectorDB Collections** (managed by FastAPI):
  - `novel_passages` (content chunks, 768-dim embeddings)
  - `characters` (descriptions, personality traits)
  - `locations` (settings)
  - `events` (plot points)
  - `themes` (thematic analysis)
- **Data Flow Example**:
  1. FastAPI ingests novel, stores passages in VectorDB
  2. FastAPI → Spring Boot: `POST /api/internal/novels` (metadata only)
  3. Spring Boot saves to PostgreSQL with `vectordb_collection_id`
  4. Frontend queries Spring Boot for novel metadata
  5. Spring Boot → FastAPI: Get character data from VectorDB
- Use HikariCP connection pooling for optimal performance
- Enable query logging in dev mode for debugging

**Estimated Effort**: 5 hours

- All 11 JSONB columns have been eliminated in favor of structured relational tables
- Use CASCADE DELETE on all foreign keys for automatic cleanup of dependent records
- Add B-tree indexes on all FK columns, scoring columns (intensity, strength, relevance_score, importance_to_arc)
- Create triggers for `updated_at` auto-update on relevant tables
- Create indexes in separate migration (V33) for clarity
- Normalized design provides better queryability, type safety, and performance vs JSONB

**Estimated Effort**: 5 hours

---

### Story 0.4: Vue.js Frontend Project Setup

**Priority: P0 - Critical**

**Description**: Initialize Vue 3 application with TypeScript, Vite, **PandaCSS**, **PrimeVue**, Pinia, and **single API client** (Spring Boot only). Implements **Pattern B** where frontend communicates ONLY with Spring Boot API Gateway.

**Acceptance Criteria**:

- [ ] Vue 3 project initialized with Vite + TypeScript
- [ ] Package manager: **pnpm** (faster than npm/yarn)
- [ ] Dependencies configured:
  - Vue Router 4 (routing)
  - Pinia (state management)
  - **PandaCSS** (CSS-in-JS with static extraction)
  - **PrimeVue** (UI component library)
  - Axios (HTTP client - Spring Boot ONLY)
  - VueUse (composition utilities)
  - date-fns (date formatting)
- [ ] Project structure created:
  ```
  frontend/
  ├── src/
  │   ├── assets/          # Static assets
  │   ├── components/      # Reusable components
  │   │   ├── common/      # Generic components
  │   │   ├── scenario/    # Scenario-related
  │   │   ├── conversation/# Conversation-related
  │   │   └── user/        # User-related
  │   ├── views/           # Page components
  │   ├── router/          # Route definitions
  │   ├── stores/          # Pinia stores
  │   ├── services/
  │   │   └── api.ts       # Axios instance (Spring Boot only)
  │   ├── types/           # TypeScript types
  │   ├── utils/           # Utility functions
  │   └── styles/          # Global styles
  ├── styled-system/       # Panda CSS generated files
  ├── panda.config.ts      # Panda CSS config
  └── package.json
  ```
- [ ] **PandaCSS configured** with:
  - Custom theme (colors, typography, spacing)
  - Static extraction for zero-runtime CSS
  - TypeScript support for styled props
- [ ] **PrimeVue integrated**:
  - Component library for UI elements (buttons, dialogs, etc.)
  - Compatible with PandaCSS styling
- [ ] Vue Router configured with:
  - Protected routes (require authentication)
  - Public routes (login, register, browse)
  - 404 page
  - Navigation guards
- [ ] Pinia stores initialized:
  - `useAuthStore` (user authentication state)
  - `useUserStore` (current user profile)
  - `useScenarioStore` (scenario browsing/creation)
  - `useConversationStore` (conversation management with SSE)
- [ ] **Single Axios instance** configured:
  - Base URL: `http://localhost:8080/api/v1` (Spring Boot ONLY)
  - ❌ NO FastAPI URL (Pattern B: all AI requests go through Spring Boot proxy)
  - Request interceptor (add JWT token)
  - Response interceptor (handle 401 errors, refresh token)
  - SSE support for streaming AI responses
- [ ] Environment variables:
  - `.env.development`: `VITE_API_BASE_URL=http://localhost:8080/api/v1`
  - `.env.production`: `VITE_API_BASE_URL=https://api.gaji.app/api/v1`
- [ ] TypeScript strict mode enabled
- [ ] ESLint + Prettier configured
- [ ] Application runs on port 3000 (Vite default)
- [ ] pnpm commands:
  - `pnpm dev` - Run dev server
  - `pnpm build` - Build for production
  - `pnpm prepare` - Generate Panda CSS (codegen)

**Technical Notes**:

- **Pattern B Implementation**: Frontend → Spring Boot ONLY. All AI requests proxied internally.
- **Security Benefit**: No FastAPI URL or Gemini API keys exposed to browser
- **PandaCSS Benefits**:
  - Zero-runtime CSS (all styling extracted at build time)
  - Type-safe styling with TypeScript autocomplete
  - Smaller bundle size vs Panda
- Use `<script setup>` syntax for composition API
- Configure path aliases: `@/` → `src/`
- Enable Vite HMR for fast development
- Add meta tags for SEO and social sharing

**Estimated Effort**: 6 hours

---

### Story 0.5: Docker Configuration & Inter-Service Communication

**Priority: P1 - High**

**Description**: Create Docker containers for all services and configure docker-compose for local development with **VectorDB (ChromaDB)** and **Redis** services for Long Polling and async task processing.

**Acceptance Criteria**:

- [ ] Dockerfile created for each service:
  - `backend/Dockerfile` (Spring Boot)
  - `ai-service/Dockerfile` (FastAPI)
  - `frontend/Dockerfile` (Vue.js with Nginx)
- [ ] docker-compose.yml with services:
  - `postgres` (PostgreSQL 15)
  - **`vectordb`** (ChromaDB for dev)
  - **`redis`** (Redis 7 for Celery + Long Polling task storage)
  - `backend` (Spring Boot on port 8080)
  - `ai-service` (FastAPI on port 8000, internal-only)
  - `frontend` (Nginx on port 80)
- [ ] Docker network configured for inter-service communication
- [ ] Health checks configured for all services:
  - postgres: `pg_isready`
  - **vectordb**: `curl http://localhost:8000/api/v1/heartbeat` (ChromaDB)
  - **redis**: `redis-cli ping`
  - backend: `GET /actuator/health`
  - ai-service: `GET /health`
  - frontend: `curl localhost:80`
- [ ] Environment variables managed via .env file
- [ ] Volumes configured:
  - PostgreSQL data persistence (`postgres_data`)
  - **VectorDB data persistence** (`vectordb_data`)
  - **Redis data persistence** (`redis_data`)
  - Backend logs
  - AI service logs
- [ ] Service dependencies:
  - backend: waits for postgres, redis
  - ai-service: waits for postgres, vectordb, redis
  - frontend: waits for backend
- [ ] Hot reload enabled for development:
  - Backend: volume mount for target/classes
  - AI service: volume mount for app/
  - Frontend: Vite dev server
- [ ] Single command startup: `docker-compose up`
- [ ] Documentation: README with setup instructions

**docker-compose.yml Structure**:

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gaji_db
      POSTGRES_USER: gaji
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gaji"]
      interval: 10s
      timeout: 5s
      retries: 5

  vectordb:
    image: chromadb/chroma:1.3.5
    ports:
      - "8001:8000" # ChromaDB HTTP API
    volumes:
      - vectordb_data:/chroma/chroma
    environment:
      CHROMA_SERVER_AUTH_PROVIDER: "chromadb.auth.token.TokenAuthServerProvider"
      CHROMA_SERVER_AUTH_CREDENTIALS: ${VECTORDB_TOKEN}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/gaji_db
      SPRING_DATASOURCE_USERNAME: gaji
      SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
      FASTAPI_BASE_URL: http://ai-service:8000
      REDIS_URL: redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ai-service:
    build: ./ai-service
    ports:
      - "8000:8000" # Internal-only, NOT exposed to frontend
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      VECTORDB_TYPE: chromadb
      VECTORDB_URL: http://vectordb:8000
      SPRING_BOOT_URL: http://backend:8080
      REDIS_URL: redis://redis:6379
    volumes:
      - ./ai-service/app:/app # Hot reload for development
    depends_on:
      vectordb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      VITE_API_URL: http://localhost:8080/api/v1
    depends_on:
      - backend

volumes:
  postgres_data:
  vectordb_data:
  redis_data:
```

**Technical Notes**:

- **VectorDB Service**: ChromaDB for dev (Pinecone config added in production)
- **Redis Service**: Used for Celery task queue + Long Polling task storage (600-second TTL)
- **No External FastAPI Access**: Frontend → Spring Boot only (Pattern B)
- Use multi-stage builds for smaller images
- Configure `.dockerignore` to exclude node_modules, target/
- Set resource limits (memory, CPU) for production:
  - postgres: 2GB RAM
  - vectordb: 4GB RAM (embeddings require memory)
  - redis: 512MB RAM
  - backend: 1GB RAM
  - ai-service: 2GB RAM (Gemini API client)
  - frontend: 256MB RAM
- Enable BuildKit for faster builds: `DOCKER_BUILDKIT=1 docker-compose build`

**Estimated Effort**: 5 hours

---

### Story 0.6: Inter-Service Health Check & API Contract

**Priority: P1 - High**

**Description**: Implement health check endpoints and define API contracts between Spring Boot backend and FastAPI AI service for reliable inter-service communication.

**Acceptance Criteria**:

- [ ] Backend health check: GET /actuator/health returns:
  ```json
  {
    "status": "UP",
    "components": {
      "db": { "status": "UP" },
      "ai-service": { "status": "UP" }
    }
  }
  ```
- [ ] AI service health check: GET /health returns:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "llm_model": "loaded"
  }
  ```
- [ ] Backend → AI service API contract defined:
  - POST /api/v1/prompts/generate (generate character prompt from scenario)
  - POST /api/v1/rag/extract-characters (extract characters from book text)
  - POST /api/v1/scenarios/validate (validate scenario coherence)
- [ ] Circuit breaker configured for AI service calls:
  - Timeout: 30 seconds
  - Fallback: return cached prompt or error response
  - Retry: 3 attempts with exponential backoff
- [ ] API versioning strategy documented
- [ ] Integration test: backend calls AI service successfully
- [ ] Error handling: graceful degradation if AI service down
- [ ] Monitoring: log all inter-service calls with duration

**API Contract Example**:

```typescript
// POST /api/v1/prompts/generate
Request:
{
  "scenario_id": "uuid",
  "character_name": "Hermione Granger"
}

Response:
{
  "prompt": "You are Hermione Granger in an alternate timeline...",
  "token_count": 650,
  "temperature": 0.7
}
```

**Technical Notes**:

- Use Resilience4j for circuit breaker (Spring Boot)
- Configure timeouts: connect 5s, read 30s
- Log request/response for debugging (sanitize sensitive data)
- Cache AI service responses (5-minute TTL)

**Estimated Effort**: 4 hours

---

### Story 0.7: VectorDB Data Import from Pre-processed Dataset

**Priority: P0 - Critical**

**Description**: Import **pre-processed Project Gutenberg dataset** into VectorDB (ChromaDB dev / Pinecone prod) using one-time Python import script. Dataset includes pre-chunked passages with **768-dim Gemini embeddings**, extracted characters, locations, events, and themes. Creates PostgreSQL metadata via Spring Boot API. **No LLM processing needed** (dataset already processed offline).

**Acceptance Criteria**:

- [ ] **Pre-processed Dataset Structure**:
  - `novels.json` - Novel metadata (title, author, year, genre, language)
  - `passages.parquet` - Text chunks + 768-dim embeddings (200-500 words each)
    - Columns: novel_id, chapter_num, passage_num, text, embedding (768-dim float array), word_count
  - `characters.json` - Character metadata + embeddings
    - Fields: character_id, novel_id, name, role, description, personality_traits[], embedding (768-dim)
  - `locations.json` - Setting descriptions + embeddings
  - `events.json` - Plot events + embeddings
  - `themes.json` - Thematic analysis + embeddings (optional for MVP)
- [ ] **Import Script**: `ai-backend/scripts/import_dataset.py`
  - CLI tool with arguments:
    - `--dataset-path` (path to dataset directory)
    - `--vectordb-host` (ChromaDB URL, default: `http://localhost:8001`)
    - `--spring-boot-api` (Spring Boot API URL, default: `http://localhost:8080`)
    - `--batch-size` (default: 1000 passages per batch)
  - Workflow:
    1. **Validate dataset structure**: Check all required files exist
    2. **Create 5 ChromaDB collections**: `novel_passages`, `characters`, `locations`, `events`, `themes`
    3. **Batch import passages**: 1000 passages per batch with embeddings
    4. **Batch import characters**: With personality traits and embeddings
    5. **Batch import locations, events, themes**
    6. **Create PostgreSQL metadata** via Spring Boot API: `POST /api/internal/novels`
    7. **Verify import**: Count validation, semantic search test
  - Progress tracking: Console output "Importing passages: 1000/5234 (19%)"
  - Error handling: Rollback on failure, retry Spring Boot API calls 3 times with exponential backoff
- [ ] **5 VectorDB Collections** (ChromaDB/Pinecone):
  - **`novel_passages`**:
    - Document schema: `{id, novel_id, chapter_num, passage_num, text, embedding[768], word_count, metadata}`
    - Index: HNSW with cosine similarity
  - **`characters`**:
    - Document schema: `{id, novel_id, name, role, description, personality_traits[], embedding[768], metadata}`
  - **`locations`**:
    - Document schema: `{id, novel_id, name, description, cultural_context, embedding[768], metadata}`
  - **`events`**:
    - Document schema: `{id, novel_id, event_name, description, outcomes[], embedding[768], metadata}`
  - **`themes`**:
    - Document schema: `{id, novel_id, theme_name, description, embedding[768], metadata}`
- [ ] **PostgreSQL Metadata Creation** (via Spring Boot API):
  - Endpoint: `POST /api/internal/novels`
  - Request payload:
    ```json
    {
      "title": "Pride and Prejudice",
      "author": "Jane Austen",
      "publication_year": 1813,
      "genre": "Romance",
      "language": "en",
      "vectordb_collection_id": "novel_UUID",
      "total_passages_count": 523,
      "total_characters_count": 47,
      "total_locations_count": 15,
      "total_events_count": 32,
      "ingestion_status": "completed",
      "dataset_source_path": "/data/gutenberg/pride-and-prejudice"
    }
    ```
  - Spring Boot validates and saves to PostgreSQL `novels` table
- [ ] **Verification Script**: `ai-backend/scripts/verify_import.py`
  - Check all 5 collections exist in VectorDB
  - Count validation: PostgreSQL metadata count == VectorDB document count
  - Semantic search test: Query "brave protagonist" → returns relevant characters with similarity scores
  - Cross-reference test: PostgreSQL `novels.vectordb_collection_id` matches VectorDB collection
  - Output: "✅ All checks passed" or "❌ Validation failed: {errors}"
- [ ] **Performance Requirements**:
  - Import speed: > 1000 passages/minute (batch insert optimization)
  - Total import time: < 10 minutes for 10 novels (~5000 passages total)
  - Memory usage: < 2GB during import (streaming parquet reads)
  - VectorDB query latency: < 100ms for top-10 semantic search

**Data Flow**:

```
1. Admin runs: python scripts/import_dataset.py --dataset-path /data/gutenberg
2. Script validates dataset structure (novels.json, passages.parquet, characters.json, etc.)
3. Script creates 5 ChromaDB collections (passages, characters, locations, events, themes)
4. Script imports passages batch (1000 per batch) → ChromaDB `novel_passages` collection
   - Each passage has pre-computed 768-dim embedding (Gemini text-embedding-004)
5. Script imports characters → ChromaDB `characters` collection
6. Script imports locations, events, themes → respective VectorDB collections
7. Script → Spring Boot API: POST /api/internal/novels (metadata only)
   - Spring Boot → PostgreSQL: Save novel metadata with vectordb_collection_id
8. Script runs verify_import.py to confirm success:
   - Count check: PostgreSQL total_passages_count == VectorDB passages count
   - Semantic search test: Query "brave protagonist" returns relevant results
   - Cross-reference: PostgreSQL vectordb_collection_id exists in VectorDB
9. Output: "✅ Import completed: 10 novels, 5234 passages, 127 characters"
```

**Technical Notes**:

- **Why Pre-processed Dataset**: Eliminates 52 hours of Local LLM extraction work
- **Embeddings**: 768-dim vectors from Gemini Embedding API (`text-embedding-004`)
  - Compatible with future Gemini API semantic search
  - Cosine similarity for semantic matching
- **Import Script Dependencies**:
  - `chromadb==0.4.18` (VectorDB client)
  - `pandas==2.1.4` (parquet file reading)
  - `pyarrow==14.0.1` (parquet backend)
  - `httpx==0.25.2` (Spring Boot API calls)
  - `tqdm==4.66.1` (progress bars)
- **Batch Import Optimization**:
  - Use `chromadb.add()` with batch_size=1000 for fast insertion
  - Stream parquet reads to avoid loading entire file into memory
  - Parallel API calls to Spring Boot (asyncio for metadata creation)
- **Error Handling**:
  - VectorDB connection error → Retry 3 times with exponential backoff (1s, 2s, 4s)
  - Spring Boot API error → Retry 3 times, rollback VectorDB on failure
  - Validation failure → Print detailed error report, suggest fixes
- **Dataset Source**: Store original path in PostgreSQL for debugging
  - `novels.dataset_source_path` (e.g., "/data/gutenberg/pride-and-prejudice")

**Estimated Effort**: 3 hours

---

## Epic Summary

**Total Stories**: 7 (Stories 0.1-0.7)

**Total Effort**: ~32 hours (~4 working days for 2 engineers)

**Effort Breakdown**:

- **Infrastructure Setup** (Stories 0.1-0.6): 28 hours
  - Story 0.1 (Spring Boot API Gateway): 6h
  - Story 0.2 (FastAPI AI Service): 6h
  - Story 0.3 (PostgreSQL Metadata): 5h
  - Story 0.4 (Vue.js Frontend): 6h
  - Story 0.5 (Docker + VectorDB + Redis): 5h
  - Story 0.6 (Health Checks): 4h
- **Data Import** (Story 0.7): 3 hours
  - VectorDB import from pre-processed dataset (no LLM processing)

**Success Criteria**:

- ✅ All 7 services running via Docker Compose (postgres, vectordb, redis, backend, ai-service, frontend)
- ✅ Pattern B architecture validated (FastAPI not externally accessible, all frontend requests → Spring Boot)
- ✅ PostgreSQL 13 metadata tables migrated (no content storage)
- ✅ 5 VectorDB collections created and populated (passages, characters, locations, events, themes)
- ✅ Health checks passing for all services (including VectorDB and Redis)
- ✅ Sample dataset imported (10+ novels, 5000+ passages, 100+ characters)
- ✅ Semantic search working (query "brave protagonist" returns relevant characters)
- ✅ Redis configured for Long Polling task storage (600-second TTL)

**Epic Dependencies**:

- Epic 0 → Epic 1 (Scenario system requires novel data from VectorDB)
- Epic 0 → Epic 2 (AI conversations require character data from VectorDB + Gemini API)
- Epic 0 → Epic 4 (Conversation system requires Redis for Long Polling)

**Cost Savings**:

- **52 hours removed** (Stories 0.7-0.12 Local LLM pipeline)
- **3 hours added** (Story 0.7 Pre-processed dataset import)
- **Net savings**: 49 hours (77h → 32h total effort)
- **Infrastructure cost**: ~$220-270/month for 1000 users (Railway + Pinecone + Gemini API)

---

## Epic-Level Acceptance Criteria

### Infrastructure Readiness

- [ ] All services containerized and running via Docker Compose
- [ ] Docker health checks passing for all 6 services (postgres, vectordb, redis, backend, ai-service, frontend)
- [ ] Inter-service communication working (backend ↔ AI service, backend ↔ PostgreSQL, AI service ↔ VectorDB, AI service ↔ Redis)
- [ ] Environment variables documented and example .env files provided
- [ ] README updated with complete local setup instructions
- [ ] Database migrations running successfully (Flyway for Spring Boot)

### Data Import Verified

- [ ] Sample dataset imported successfully (10+ novels, 5000+ passages, 100+ characters)
- [ ] 5 ChromaDB collections created and populated (passages, characters, locations, events, themes)
- [ ] VectorDB semantic search test passing (query "brave protagonist" returns relevant results)
- [ ] PostgreSQL metadata synced with VectorDB (count validation passing)
- [ ] Cross-reference validation: PostgreSQL `vectordb_collection_id` exists in VectorDB

### API Integration Operational

- [ ] Gemini API key configured in FastAPI environment
- [ ] Gemini 2.5 Flash text generation working (test prompt returns valid response)
- [ ] Gemini Embedding API working (test text returns 768-dim vector)
- [ ] Retry logic validated (3 attempts with exponential backoff 1s/2s/4s)
- [ ] Circuit breaker tested (fails after 5 consecutive errors)

### Developer Experience

- [ ] Development environment can be started with single command: `docker-compose up`
- [ ] Hot reload working for all services (backend, ai-service, frontend)
- [ ] Documentation includes troubleshooting guide for common issues
- [ ] Sample data seeded for testing (10+ novels with passages and characters)

---

## Dependencies

**External Dependencies**:

- Docker Desktop installed (version 20+)
- Docker Compose (bundled with Docker Desktop)
- JDK 17 (for Spring Boot local development)
- Node.js 18+ (for Vue.js local development)
- Python 3.11+ (for FastAPI local development)
- PostgreSQL 15 client tools (for database management)
- **Gemini API key** from Google Cloud Console
- **Pre-processed Project Gutenberg dataset** (download link TBD)

**Internal Dependencies**:

- None (Epic 0 is the foundation for all other epics)

**Required Infrastructure**:

- 8GB+ RAM (for running all services)
- 50GB+ disk space (Docker images, VectorDB data, database storage)
- Stable internet connection (for Gemini API calls)

**Tools and Services**:

- GitHub account (for repository access)
- Google Cloud Console (for Gemini API key)
- ChromaDB OSS (free, self-hosted for dev)
- Pinecone account (optional, for production VectorDB)

**Pre-requisites**:

- Project repository cloned locally
- Environment variables configured (.env files)
- Docker daemon running
- Database migrations prepared (Flyway scripts in `/db/migrations/`)
- Pre-processed dataset downloaded to `/data/gutenberg/`

---

## Definition of Done

**Infrastructure Complete**:

- [ ] All 6 Docker containers running without errors
- [ ] Health check endpoints returning 200 OK for all services (postgres, vectordb, redis, backend, ai-service, frontend)
- [ ] Database migrations applied successfully (13 PostgreSQL metadata tables created)
- [ ] Environment variables configured and validated
- [ ] Local development workflow documented and tested

**Data Import Complete**:

- [ ] Import script working: `python scripts/import_dataset.py --dataset-path /data/gutenberg`
- [ ] 5 VectorDB collections created (passages, characters, locations, events, themes)
- [ ] Sample dataset imported (10+ novels, 5000+ passages, 100+ characters)
- [ ] PostgreSQL metadata created via Spring Boot API
- [ ] Verification script passing: `python scripts/verify_import.py`

**Gemini API Integration Complete**:

- [ ] Gemini 2.5 Flash configured in FastAPI (text generation)
- [ ] Gemini Embedding API configured (768-dim embeddings)
- [ ] Retry logic validated (3 attempts with exponential backoff)
- [ ] Circuit breaker tested (fails after 5 consecutive API errors)
- [ ] API key securely stored in environment variables

**Quality Assurance**:

- [ ] Integration tests passing for all Epic 0 features
- [ ] API documentation generated (Swagger/OpenAPI for FastAPI, Spring REST Docs for Spring Boot)
- [ ] Performance benchmarks met:
  - Import speed: >1000 passages/minute
  - Import completion: <10 minutes for 10 novels
  - VectorDB semantic search: <100ms response time
- [ ] Error handling validated:
  - Gemini API failures gracefully handled with retry
  - VectorDB connection errors logged and retried
  - Spring Boot API errors trigger rollback

**Documentation Complete**:

- [ ] README.md updated with quick start guide
- [ ] DEVELOPMENT.md with detailed setup instructions
- [ ] API documentation published (accessible via `/api/docs` endpoints)
- [ ] Architecture diagrams updated in `/docs/ARCHITECTURE.md`
- [ ] Gemini API key configuration guide documented
- [ ] Pre-processed dataset structure documented
- [ ] Troubleshooting guide for common developer issues

**Cost Tracking Validated**:

- [ ] Gemini API usage tracked in llm_analysis_tracking table
- [ ] Cost estimates documented:
  - Per-conversation costs (Gemini 2.5 Flash)
  - Monthly infrastructure costs (Railway + Pinecone + Gemini API)
  - Estimated costs for 1000 users (~$220-270/month)

**Developer Handoff Ready**:

- [ ] Environment can be started with `docker-compose up`
- [ ] Sample data loaded (10+ novels with passages and characters)
- [ ] All tests passing (`npm test`, `pytest`, `./gradlew test`)
- [ ] Code review completed for all Epic 0 stories
- [ ] Epic 1 (Scenario Foundation) can begin development

---

## Success Metrics

### Infrastructure Performance

- **Startup Time**: All services running within 2 minutes of `docker-compose up`
- **Health Check Latency**: <500ms for all health check endpoints
- **Database Migration Time**: <10 seconds for full schema creation
- **Docker Image Sizes**: <500MB per service (optimized builds)

### Data Import Performance

- **Import Speed**: >1000 passages/minute (batch insert optimization)
- **Total Import Time**: <10 minutes for 10 novels (~5000 passages total)
- **Memory Usage**: <2GB during import (streaming parquet reads)
- **VectorDB Query Latency**: <100ms for top-10 semantic search

### Gemini API Performance

- **Text Generation Latency**: <3 seconds for typical conversation turn (Gemini 2.5 Flash)
- **Embedding Generation**: <500ms for single text embedding (768-dim)
- **Retry Success Rate**: >95% of failed API calls succeed on retry
- **Circuit Breaker Accuracy**: Opens after exactly 5 consecutive errors

### Cost Efficiency

#### Gemini API Costs (estimated monthly for 1000 users)

- **Text Generation** (Gemini 2.5 Flash):
  - Average: 10 conversations/user/month × 20 turns/conversation × 2,000 tokens/turn = 400,000 tokens/user
  - Total: 1000 users × 400,000 = 400M tokens/month
  - Input cost: 400M × $0.075 / 1M = **$30/month**
  - Output cost: 400M × 0.4 (40% output ratio) × $0.30 / 1M = **$48/month**
  - **Total text generation**: ~$78/month
- **Embeddings** (Gemini Embedding API):
  - Negligible (only for scenario validation, ~1000 calls/month)
  - **Total embeddings**: ~$0.075/month
- **Gemini API Total**: ~$78/month

#### Infrastructure Costs (monthly, estimated)

- **Railway Hosting**: ~$20-30/month for 1000 users
- **PostgreSQL Database**: ~$10/month (Railway PostgreSQL add-on)
- **Pinecone VectorDB** (production): ~$70/month for 100M vectors
- **Redis**: ~$10/month (Railway Redis add-on)
- **Gemini API**: ~$78/month (text generation + embeddings)
- **Total Infrastructure**: ~$188-198/month for 1000 users

### Developer Productivity

- **Setup Time**: <30 minutes from clone to running app (for experienced developers)
- **Hot Reload Speed**: <2 seconds for code changes to reflect
- **Test Execution Time**: <5 minutes for full test suite
- **Documentation Clarity**: >90% of developers can set up without support

---

## Notes

**LLM Integration Approach**:

- Epic 0 uses **Gemini 2.5 Flash API** for all AI interactions:
  - Character conversations (Epic 2)
  - Scenario validation (Epic 1)
  - What-if analysis
- **Pre-processed dataset** eliminates need for Local LLM extraction pipeline
- Dataset includes **768-dim Gemini embeddings** for semantic search

**VectorDB Strategy**:

- **Development**: ChromaDB OSS (self-hosted, free)
- **Production**: Pinecone (cloud-hosted, scalable)
- **Fallback**: PostgreSQL pgvector extension (if VectorDB unavailable)
- All code uses abstraction layer for easy switching between VectorDB backends

**Database Migrations**:

- Flyway for Spring Boot (Java-based migrations)
- Versioned SQL scripts in `/db/migrations/`
- Baseline version: V1.0\_\_initial_schema.sql (13 metadata tables)
- Future migrations use incremental versioning (V1.1, V1.2, etc.)

**Docker Optimization**:

- Multi-stage builds for smaller images
- Layer caching for faster rebuilds
- Health checks to prevent race conditions
- Resource limits to prevent memory exhaustion (vectordb 4GB, postgres 2GB, redis 512MB, backend 1GB, ai-service 2GB, frontend 256MB)

**Long Polling Implementation**:

- Frontend polls Spring Boot every 2 seconds for task status
- Spring Boot forwards to FastAPI internal endpoint
- Redis stores task status with 600-second TTL (10 minutes)
- Browser notifications via WebSocket/SSE for task completion

**Risk Mitigation**:

- **Gemini API Downtime**: Retry logic with exponential backoff (1s, 2s, 4s)
- **VectorDB Downtime**: PostgreSQL pgvector as emergency fallback
- **Database Corruption**: Daily automated backups
- **Cost Overruns**: Budget alerts and rate limiting

**Future Considerations** (post-MVP):

- Advanced metadata extraction (sentiment analysis, character relationships)
- Multi-language support (non-English novels)
- Real-time collaborative scenario editing
- Advanced cost optimization (prompt caching, model fine-tuning)

---

## Change Log

| Date       | Version | Change Description                                        | Changed By |
| ---------- | ------- | --------------------------------------------------------- | ---------- |
| 2025-11-27 | 1.0     | Initial Epic 0 creation with 12 stories (77h)             | PM         |
| 2025-11-27 | 2.0     | Updated to Gemini 2.5 Flash + Pre-processed Dataset (32h) | PO         |

- Removed Stories 0.7-0.12 (Local LLM pipeline, 52h)
- Added new Story 0.7 (VectorDB Data Import, 3h)
- Updated Story 0.2 (FastAPI with Gemini SDK + Redis for Long Polling)
- Updated Story 0.5 (Docker with VectorDB ChromaDB + Redis services)
- Updated Epic Summary (77h → 32h total effort)
- Updated Dependencies (removed Local LLM models, added Gemini API key)
- Updated Definition of Done (removed LLM pipeline criteria, added dataset import)
- Updated Success Metrics (removed LLM processing costs, added Gemini API costs)

---

**Epic Owner**: Platform Team (Backend + AI Engineers)
**Epic Status**: Draft (awaiting approval to begin Story 0.1)
**Epic Priority**: P0 - Critical (foundation for all features)

- No Kubernetes/orchestration (Docker Compose sufficient for MVP)
- No Redis caching layer (use in-memory cache)
- No message queue (RabbitMQ/Kafka deferred to scale phase)
- No service mesh (Istio/Linkerd unnecessary for MVP)
- No distributed tracing (add when debugging becomes difficult)

**Won't Build** (architectural decisions):

- Microservices split (two services sufficient: backend + AI)
- GraphQL (REST API simpler for MVP)
- Server-side rendering (SPA sufficient)
- Real-time WebSocket updates (polling acceptable for MVP)

## Testing Strategy

**Unit Tests**:

- Backend: Spring Boot test framework (JUnit 5, Mockito)
- AI service: pytest with fixtures
- Frontend: Vitest + Vue Test Utils

**Integration Tests**:

- Database migrations (verify schema correctness)
- Inter-service API calls (backend → AI service)
- Health check endpoints

**E2E Tests**:

- Full stack smoke test: frontend → backend → database
- Docker Compose startup test (all services healthy)

**Performance Tests**:

- Database connection pool under load
- Concurrent service startup

## Open Questions

1. **Q**: Should we use separate databases for backend and AI service?
   **A**: No. Single PostgreSQL instance, shared schema. Simpler for MVP, can split later.

2. **Q**: How to handle database schema changes in production?
   **A**: Blue-green deployment with Flyway migrations. Zero-downtime migrations required.

3. **Q**: Should we containerize for production or use platform services (Railway)?
   **A**: Railway for MVP (managed PostgreSQL, auto-deploy). Containers for development.

4. **Q**: How to manage secrets (API keys, database passwords)?
   **A**: Development: .env file. Production: Railway environment variables (encrypted at rest).

## Definition of Done

- [ ] All 12 stories completed with acceptance criteria met
- [ ] docker-compose up successfully starts all services
- [ ] All health checks passing
- [ ] Database migrations run cleanly (including all LLM-related tables)
- [ ] **LLM Pipeline Verified**:
  - [ ] Sample novel uploaded and processed successfully
  - [ ] Characters extracted with >85% accuracy
  - [ ] Locations, events, themes extracted
  - [ ] Passage embeddings generated
  - [ ] Base scenarios created and verified
- [ ] **Cost Tracking Operational**:
  - [ ] All LLM analyses tracked in llm_analysis_metadata
  - [ ] Cost dashboard showing accurate spend data
  - [ ] Budget alerts configured
- [ ] README documentation complete with setup instructions
- [ ] .env.example provided with all required variables (LLM_MODEL_PATH, LLM_MODEL_TYPE)
- [ ] Local LLM model download instructions documented
- [ ] CI/CD pipeline configured (optional for MVP, recommended)
- [ ] All services accessible at documented URLs
- [ ] Integration tests passing (inter-service communication + LLM pipeline)
- [ ] Code review completed, no P0/P1 issues
- [ ] At least one developer successfully onboarded using documentation
- [ ] Admin dashboard accessible and functional

---

**Epic Owner**: Tech Lead / Full Stack Lead / AI/ML Engineer

**Start Date**: Week 1, Day 1 of MVP development

**Target Completion**: Week 2, Day 10 (10 working days)

**Estimated Total Effort**: 77 hours

- **Infrastructure**: 25 hours (Stories 0.1-0.6)
- **LLM Pipeline**: 52 hours (Stories 0.7-0.12)

**Priority**: HIGHEST - All other epics blocked until infrastructure (0.1-0.6) completes. Epic 1 requires LLM pipeline (0.7-0.11) to be complete.
