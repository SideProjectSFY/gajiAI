# Gaji Platform: Next Steps

**Last Updated**: 2025-11-14  
**Status**: Ready for Implementation  
**Phase**: Documentation Complete → Implementation Start

---

## 📊 Current Status

### ✅ Documentation Complete (100%)

- [x] Architecture design finalized (Pattern B - API Gateway)
- [x] Database strategy defined (PostgreSQL + VectorDB Hybrid)
- [x] Backend optimization strategies documented (7 strategies)
- [x] 7 Epics, 37 User Stories fully specified
- [x] All Korean content translated to English
- [x] Documentation consolidated (22 files → 12 files)

---

## 🎯 Immediate Actions (This Week)

### 1. Development Environment Setup ⚙️

**Time**: 4 hours  
**Owners**: Both developers

**Tasks**:

- [ ] Review [ARCHITECTURE.md](./ARCHITECTURE.md) and [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md)
- [ ] Install prerequisites (Java 17+, Python 3.11+, Node 18+, Docker)
- [ ] Clone all repositories (core-backend, ai-backend, frontend, api-contracts)
- [ ] Organize workspace directory structure
- [ ] Start PostgreSQL + Redis via Docker
- [ ] Verify all services start successfully

**Success**: Health check endpoints responding (Spring Boot :8080, FastAPI :8000)

---

### 2. Pattern B Implementation - Backend 🔧

**Time**: 16 hours  
**Owner**: 민영재 (Backend)

**Tasks**:

- [ ] Create `AIProxyController.java` with REST proxy endpoints
- [ ] Configure `WebClientConfig` for async FastAPI communication
- [ ] Implement Circuit Breaker (Resilience4j)
- [ ] Add Redis caching for passage search
- [ ] Write unit tests (>80% coverage)
- [ ] Write integration tests (Spring Boot ↔ FastAPI)

**Reference**: [BACKEND_OPTIMIZATION.md](./BACKEND_OPTIMIZATION.md) Strategies 1-3

**Success**: AIProxyController proxies all FastAPI endpoints with tests passing

---

### 3. Pattern B Implementation - Frontend 💻

**Time**: 8 hours  
**Owner**: 구서원 (Frontend)

**Tasks**:

- [ ] Create unified API client (`frontend/src/services/api.ts`)
- [ ] Remove dual clients (coreApi, aiApi)
- [ ] Update all service layer imports
- [ ] Update SSE EventSource paths to `/api/ai/stream/*`
- [ ] Update environment variables (`VITE_API_URL=http://localhost:8080`)
- [ ] Write E2E tests confirming no direct FastAPI calls

**Success**: Only 1 API client exists, all calls go through Spring Boot :8080

---

## 📅 Short-term Goals (Next 2 Weeks)

### Week 1: Pattern B Migration Complete ✅

**Deliverables**:

- ✅ AIProxyController implemented
- ✅ Frontend unified API client
- ✅ Docker Compose updated (FastAPI internal network only)
- ✅ All tests passing

---

### Week 2: Epic 0 Infrastructure 🏗️

**Goal**: Complete project foundation with pre-processed dataset

**Epic File**: `docs/epics/epic-0-project-setup-infrastructure.md`

**Stories** (39 hours total):

- [ ] 0.1: Spring Boot project setup (API Gateway) - 6h
  - Story: `docs/stories/epic-0-story-0.1-spring-boot-backend-setup.md`
- [ ] 0.2: FastAPI service setup (internal-only) - 6h
  - Story: `docs/stories/epic-0-story-0.2-fastapi-ai-service-setup.md`
- [ ] 0.3: PostgreSQL + Flyway migrations (13 metadata tables) - 5h
  - Story: `docs/stories/epic-0-story-0.3-postgresql-database-flyway-migrations.md`
- [ ] 0.4: Vue.js frontend setup (PandaCSS + PrimeVue) - 6h
  - Story: `docs/stories/epic-0-story-0.4-vue-js-frontend-project-setup.md`
- [ ] 0.5: Docker configuration (6 services) - 5h
  - Story: `docs/stories/epic-0-story-0.5-docker-configuration.md`
- [ ] 0.6: Health check endpoints (Pattern B validation) - 8h
  - Story: `docs/stories/epic-0-story-0.6-inter-service-health-check.md`
- [ ] 0.7: VectorDB data import from pre-processed dataset - 3h
  - Story: `docs/stories/epic-0-story-0.7-vectordb-data-import.md`

**Success**: All services running + 10+ novels imported + 100+ characters in VectorDB

---

## 🚀 Mid-term Goals (Next Month)

### Month 1: Core Features (Epic 1-2)

**Epic 1: Scenario Foundation** (26h - 3 stories)

- **Epic File**: `docs/epics/epic-1-what-if-scenario-foundation.md`
- Story 1.1: Scenario data model & CRUD API (8h)
  - Story: `docs/stories/epic-1-story-1.1-scenario-data-model-api.md`
- Story 1.2: Unified scenario creation modal (12h)
  - Story: `docs/stories/epic-1-story-1.2-unified-scenario-creation-modal.md`
- Story 1.3: Scenario validation system (6h)
  - Story: `docs/stories/epic-1-story-1.3-scenario-validation-system.md`

**Epic 2: AI Character Adaptation** (32h - 4 stories)

- **Epic File**: `docs/epics/epic-2-ai-character-adaptation.md`
- Story 2.1: Scenario → prompt engine (10h)
  - Story: `docs/stories/epic-2-story-2.1-scenario-to-prompt-engine.md`
- Story 2.2: Context window manager (8h)
  - Story: `docs/stories/epic-2-story-2.2-conversation-context-window-manager.md`
- Story 2.3: Multi-timeline character consistency (6h)
  - Story: `docs/stories/epic-2-story-2.3-multi-timeline-character-consistency.md`
- Story 2.4: Scenario context testing & refinement (8h)
  - Story: `docs/stories/epic-2-story-2.4-scenario-context-testing-refinement.md`

**Milestone**: Users can create scenarios and start AI conversations with Gemini 2.5 Flash

---

## 📈 Long-term Goals (Next 3 Months)

### Month 2: Discovery & Conversation (Epic 3-4)

**Epic 3: Scenario Discovery & Forking** (63h - 7 stories)

- **Epic File**: `docs/epics/epic-3-scenario-discovery-forking.md`
- Story 3.1: Book browse page (8h)
  - Story: `docs/stories/epic-3-story-3.1-book-browse-page.md`
- Story 3.2: Book detail page (10h)
  - Story: `docs/stories/epic-3-story-3.2-book-detail-page.md`
- Story 3.3: Scenario browse UI & filtering (8h)
  - Story: `docs/stories/epic-3-story-3.3-scenario-browse-ui-filtering.md`
- Story 3.4: Scenario forking backend (10h)
  - Story: `docs/stories/epic-3-story-3.4-scenario-forking-backend-meta-timeline.md`
- Story 3.5: Scenario forking UI (8h)
  - Story: `docs/stories/epic-3-story-3.5-scenario-forking-ui-meta-fork-creation.md`
- Story 3.6: Scenario search & advanced filtering (9h)
  - Story: `docs/stories/epic-3-story-3.6-scenario-search-advanced-filtering.md`
- Story 3.7: Social sharing & dynamic og:image (10h)
  - Story: `docs/stories/epic-3-story-3.7-social-sharing-dynamic-og-image.md`

**Epic 4: Conversation System** (26h - 3 stories)

- Story 4.1: Conversation data model & CRUD API (8h)
- Story 4.2: Message streaming & AI integration (12h)
- Story 4.3: Conversation forking UI (6h)

### Month 3: Polish & Launch (Epic 5-6)

- D3.js tree visualization
- User authentication (JWT)
- Personal memos
- Beta launch (100 users)

---

## 📚 Documentation Structure

### Core Documents (Must Read)

| Document                             | Purpose                              |
| ------------------------------------ | ------------------------------------ |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Complete architecture guide (6 ADRs) |
| [README.md](../README.md)            | Project overview                     |
| [CLAUDE.md](../CLAUDE.md)            | AI development guide                 |

### Implementation Guides

| Document                                             | Purpose                  |
| ---------------------------------------------------- | ------------------------ |
| [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md)       | Local environment setup  |
| [BACKEND_OPTIMIZATION.md](./BACKEND_OPTIMIZATION.md) | 7 performance strategies |
| [DATABASE_STRATEGY.md](./DATABASE_STRATEGY.md)       | Hybrid DB design         |

### Specifications

| Document                                                     | Purpose                       |
| ------------------------------------------------------------ | ----------------------------- |
| [PRD.md](./PRD.md)                                           | Product requirements          |
| [ERD.md](./ERD.md)                                           | Database schema (13 tables)   |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)               | API reference (40+ endpoints) |
| [TESTING_STRATEGY.md](./TESTING_STRATEGY.md)                 | Testing guidelines            |
| [UI_UX_SPECIFICATIONS.md](./UI_UX_SPECIFICATIONS.md)         | Design specifications         |
| [V0_SCREEN_SPECIFICATIONS.md](./V0_SCREEN_SPECIFICATIONS.md) | Screen designs                |
| [SECURITY.md](./SECURITY.md)                                 | Security best practices       |

### Epic/Story Details

- [epics/](./epics/) - 7 epic specifications
- [stories/](./stories/) - 37 user story implementations

---

## ✅ Implementation Checklist

### Pattern B Migration (40h)

- [ ] Spring Boot AIProxyController (16h)
- [ ] Frontend API client unification (8h)
- [ ] Docker Compose update (4h)
- [ ] Testing & validation (12h)

### Epic 0: Infrastructure (39h - 7 stories)

- [ ] 0.1: Spring Boot backend setup (5h)
- [ ] 0.2: FastAPI AI service setup (5h)
- [ ] 0.3: PostgreSQL database + Flyway migrations (5h)
- [ ] 0.4: Vue.js frontend project setup (6h)
- [ ] 0.5: Docker configuration (8h)
- [ ] 0.6: Inter-service health check (5h)
- [ ] 0.7: VectorDB data import (5h)

### Epic 1: Scenario Foundation (26h - 3 stories)

- [ ] 1.1: Scenario data model & API (8h)
- [ ] 1.2: Unified scenario creation modal (12h)
- [ ] 1.3: Scenario validation system (6h)

### Epic 2: AI Character Adaptation (40h - 4 stories)

- [ ] 2.1: Scenario to prompt engine (12h)
- [ ] 2.2: Conversation context window manager (10h)
- [ ] 2.3: Multi-timeline character consistency (10h)
- [ ] 2.4: Scenario context testing & refinement (8h)

### Epic 3: Scenario Discovery & Forking (63h - 7 stories)

- [ ] 3.1: Book browse page (8h)
- [ ] 3.2: Book detail page (10h)
- [ ] 3.3: Scenario browse UI & filtering (8h)
- [ ] 3.4: Scenario forking backend (10h)
- [ ] 3.5: Scenario forking UI (8h)
- [ ] 3.6: Scenario search & advanced filtering (9h)
- [ ] 3.7: Social sharing & dynamic og:image (10h)

### Epic 4: Conversation System (26h - 3 stories)

- [ ] 4.1: Conversation data model & CRUD API (8h)
- [ ] 4.2: Message streaming & AI integration (12h)
- [ ] 4.3: Conversation forking UI (6h)

**Total Epics 0-4**: ~194 hours (~8 weeks for 2 developers)

---

## 📊 Success Metrics

### Technical KPIs

| Metric                  | Target   |
| ----------------------- | -------- |
| API Response Time (P95) | < 500ms  |
| AI First Token          | < 1000ms |
| Error Rate              | < 0.1%   |
| Test Coverage           | > 80%    |

### Product KPIs

| Metric             | Week 2 | Month 1 | Beta |
| ------------------ | ------ | ------- | ---- |
| Novels Ingested    | 1      | 10      | 50   |
| Scenarios Created  | 5      | 50      | 500  |
| Conversations      | 10     | 100     | 1000 |
| Daily Active Users | -      | 10      | 100  |

---

## 🎯 Action Items (This Week)

### 민영재 (Backend)

1. [ ] Review ARCHITECTURE.md + BACKEND_OPTIMIZATION.md
2. [ ] Environment setup (Java, PostgreSQL, Redis)
3. [ ] Implement AIProxyController (16h)
4. [ ] Write tests

### 구서원 (Frontend)

1. [ ] Review ARCHITECTURE.md + UI_UX_SPECIFICATIONS.md
2. [ ] Environment setup (Node.js, pnpm)
3. [ ] Unified API client implementation (8h)
4. [ ] Write E2E tests

### Both

- [ ] Daily standup (progress sync)
- [ ] Code review for Pattern B PR
- [ ] Deploy to staging (Railway + Vercel)

---

**Status**: Ready to Start Implementation 🚀  
**Next Review**: End of Week 1 (Pattern B migration complete)  
**Timeline**: 7 weeks to MVP
