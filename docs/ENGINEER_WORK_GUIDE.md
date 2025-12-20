# Gaji Platform: Engineer Work Guide

**Last Updated**: 2025-11-19  
**Version**: 1.0  
**Purpose**: 각 엔지니어(AI, Backend, Frontend)의 명확한 작업 순서와 의존성 가이드

---

## 📋 Overview

이 문서는 **3명의 엔지니어**(AI Engineer, Backend Engineer, Frontend Engineer)가 효율적으로 병렬 작업하면서도 의존성을 관리할 수 있도록 작업 순서를 정의합니다.

**핵심 원칙**:

1. **병렬 작업 최대화**: 독립적인 작업은 동시에 진행
2. **의존성 명확화**: 다른 팀원의 완료를 기다려야 하는 지점 표시
3. **일일 통합**: 매일 저녁 6시 전체 스택 통합 테스트
4. **빠른 피드백**: 블로킹 이슈는 즉시 공유

---

## 🎯 Role Responsibilities

### AI Engineer (1명)

**주요 책임**: FastAPI AI Service, VectorDB, Gemini API 통합, Prompt Engineering

**기술 스택**:

- Python 3.11+, FastAPI, ChromaDB/Pinecone
- Gemini 2.5 Flash API, Gemini Embedding API
- Redis (Long Polling), Celery (async tasks)

### Backend Engineer (1명)

**주요 책임**: Spring Boot API Gateway, PostgreSQL, Business Logic, API 설계

**기술 스택**:

- Java 17+, Spring Boot 3.2+, MyBatis
- PostgreSQL 15, Flyway
- Spring Security (JWT), WebClient

### Frontend Engineer (1명)

**주요 책임**: Vue.js Application, UI/UX, API 연동

**기술 스택**:

- Vue 3, TypeScript, Vite
- PandaCSS, PrimeVue, Pinia
- Axios, Vue Router

---

## 📅 Phase-by-Phase Work Guide

---

## Phase 1: Infrastructure Setup (Epic 0, Day 1-4)

### Day 1-2: 폭풍 셋업 (병렬 작업)

#### 🤖 AI Engineer

**Story 0.2: FastAPI AI Service Setup** (6h)

**작업 순서**:

1. **환경 설정** (1h)

   - Python 3.11+ 설치
   - uv 패키지 매니저 설치
   - 프로젝트 구조 생성 (`ai-backend/`)

   ```bash
   mkdir -p ai-backend/app/{api,services,models,utils}
   cd ai-backend
   uv init
   ```

2. **의존성 설치** (0.5h)

   - requirements.txt 작성:
     - FastAPI, Uvicorn
     - google-generativeai (Gemini SDK)
     - chromadb, pinecone-client
     - httpx, celery, redis

   ```bash
   uv pip install -r requirements.txt
   ```

3. **Gemini API 설정** (2h)

   - `.env` 파일 생성: `GEMINI_API_KEY` 설정
   - `services/gemini_client.py` 작성
     - Gemini 2.5 Flash 클라이언트 설정
     - Gemini Embedding API 설정 (768-dim)
     - Retry 로직 (3회, exponential backoff)
   - 테스트: 간단한 텍스트 생성 및 embedding 생성

4. **VectorDB 설정** (1.5h)

   - ChromaDB 클라이언트 설정 (dev)
   - 5개 collection 생성 함수:
     - `novel_passages`, `characters`, `locations`, `events`, `themes`
   - 테스트: Collection 생성 및 샘플 데이터 삽입

5. **FastAPI 앱 구조** (1h)
   - `main.py`: FastAPI 앱 초기화
   - `api/health.py`: Health check 엔드포인트
   - CORS 설정 (Spring Boot only)
   - Port 8000에서 실행 확인

**체크포인트**:

- [ ] `uvicorn app.main:app --reload` 실행 성공
- [ ] `GET /health` 응답: `{"status": "healthy"}`
- [ ] Gemini API 테스트 통과 (텍스트 생성)
- [ ] ChromaDB 연결 확인 (5개 collection 생성)

**의존성**: ❌ 없음 (독립적 작업)

---

#### 💾 Backend Engineer

**Story 0.1: Spring Boot Backend Setup** (6h)

**작업 순서**:

1. **Spring Boot 프로젝트 생성** (0.5h)

   - Spring Initializr로 프로젝트 생성
   - Dependencies: Web, WebFlux, MyBatis, Security, PostgreSQL, Actuator, Lombok

   ```bash
   gradle init --type=java-application
   ```

2. **프로젝트 구조 설정** (0.5h)

   ```
   com.gaji.corebackend/
   ├── config/
   ├── controller/
   ├── service/
   ├── mapper/
   ├── domain/
   ├── dto/
   ├── client/
   └── exception/
   ```

3. **WebClient 설정** (2h)

   - `config/WebClientConfig.java`
   - FastAPI proxy용 WebClient 설정
   - Base URL: `http://localhost:8000`
   - Timeout: 60초
   - Circuit Breaker 패턴 (Resilience4j)

4. **CORS & Security 기본 설정** (1h)

   - `config/SecurityConfig.java`
   - CORS: `http://localhost:3000` (dev)
   - JWT 인증 준비 (Basic skeleton)

5. **Health Check & Actuator** (1h)

   - `GET /actuator/health` 엔드포인트
   - FastAPI health check 호출
   - Application.yml 설정 (port 8080)

6. **테스트 실행** (1h)
   - `./gradlew bootRun` 실행 확인
   - Health check 테스트

**체크포인트**:

- [ ] `./gradlew bootRun` 실행 성공
- [ ] `GET /actuator/health` 응답 200 OK
- [ ] WebClient 설정 완료 (FastAPI 호출 준비)

**의존성**:

- ⚠️ Story 0.3 (PostgreSQL) 완료 후 DB 연결 가능
- ⚠️ Story 0.2 (FastAPI) 완료 후 AI proxy 테스트 가능

---

#### 🎨 Frontend Engineer

**Story 0.4: Vue.js Frontend Setup** (6h)

**작업 순서**:

1. **Vue 3 프로젝트 생성** (0.5h)

   ```bash
   npm create vite@latest frontend -- --template vue-ts
   cd frontend
   pnpm install
   ```

2. **PandaCSS 설정** (1.5h)

   - `pnpm add -D @pandacss/dev`
   - `panda.config.ts` 작성 (커스텀 테마)
   - `pnpm panda init`
   - 기본 스타일 적용

3. **PrimeVue 설정** (1h)

   - `pnpm add primevue`
   - `main.ts`에서 PrimeVue 등록
   - 기본 컴포넌트 테스트 (Button, Dialog)

4. **프로젝트 구조 설정** (1h)

   ```
   src/
   ├── components/
   ├── views/
   ├── router/
   ├── stores/
   ├── services/
   ├── types/
   └── utils/
   ```

5. **Axios 설정 (Single API Client)** (1h)

   - `services/api.ts` 작성
   - Base URL: `http://localhost:8080/api/v1` (Spring Boot ONLY)
   - Request/Response 인터셉터
   - JWT 토큰 자동 첨부

6. **Vue Router & Pinia 기본 설정** (1h)
   - Router 설정 (기본 routes)
   - Pinia stores 초기화:
     - `useAuthStore`
     - `useUserStore`

**체크포인트**:

- [ ] `pnpm dev` 실행 성공 (port 3000)
- [ ] PandaCSS 스타일 적용 확인
- [ ] PrimeVue 컴포넌트 렌더링 확인
- [ ] Axios API client 설정 완료

**의존성**:

- ⚠️ Story 0.1 (Spring Boot) 완료 후 API 호출 가능

---

### Day 2: Database & Docker Setup

#### 💾 Backend Engineer

**Story 0.3: PostgreSQL Database Setup** (5h)

**작업 순서**:

1. **PostgreSQL 설치/설정** (0.5h)

   - Docker로 PostgreSQL 15 실행

   ```bash
   docker run --name gaji-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:15
   ```

2. **Flyway 설정** (1h)

   - `build.gradle`에 Flyway 추가
   - `src/main/resources/db/migration/` 폴더 생성
   - `application.yml`에 Flyway 설정

3. **메타데이터 테이블 마이그레이션 작성** (3h)
   - `V1__create_users_table.sql`
   - `V2__create_novels_table.sql` (metadata only, no full_text)
   - `V3__create_base_scenarios_table.sql`
   - ... (총 13개 테이블)
4. **마이그레이션 실행 & 검증** (0.5h)
   ```bash
   ./gradlew flywayMigrate
   ```
   - 13개 테이블 생성 확인
   - Seed data 스크립트 실행 (10 users, 3 novels)

**체크포인트**:

- [ ] PostgreSQL 연결 성공
- [ ] 13개 테이블 생성 확인
- [ ] Spring Boot에서 DB 연결 성공

**의존성**: ❌ 없음 (독립적 작업)

---

#### 🤖 AI Engineer & 💾 Backend Engineer (협업)

**Story 0.5: Docker Configuration** (5h)

**작업 분담**:

- **AI Engineer** (2.5h): FastAPI Dockerfile 작성, ChromaDB & Redis 설정
- **Backend Engineer** (2.5h): Spring Boot Dockerfile 작성, docker-compose.yml 작성

**AI Engineer 작업**:

1. **FastAPI Dockerfile** (1h)

   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **docker-compose.yml - VectorDB & Redis 서비스** (1.5h)
   - ChromaDB 서비스 정의
   - Redis 서비스 정의
   - Health checks 설정

**Backend Engineer 작업**:

1. **Spring Boot Dockerfile** (1h)

   ```dockerfile
   FROM openjdk:17-jdk-slim
   WORKDIR /app
   COPY build/libs/*.jar app.jar
   ENTRYPOINT ["java", "-jar", "app.jar"]
   ```

2. **docker-compose.yml 통합** (1.5h)
   - 전체 6개 서비스 정의:
     - postgres, vectordb, redis
     - backend, ai-service, frontend
   - 네트워크 설정
   - 볼륨 설정 (데이터 영속성)
   - 서비스 의존성 정의

**체크포인트**:

- [ ] `docker-compose up` 실행 성공
- [ ] 6개 서비스 모두 healthy 상태
- [ ] 서비스 간 통신 확인

**의존성**:

- ✅ Story 0.1, 0.2 완료 필요 (Dockerfile 작성 위함)

---

### Day 3-4: Data Import & Integration

#### 🤖 AI Engineer

**Story 0.7: VectorDB Data Import** (3h)

**작업 순서**:

1. **Import Script 작성** (2h)
   - `scripts/import_dataset.py` 작성
   - CLI arguments: `--dataset-path`, `--vectordb-host`, `--spring-boot-api`
   - Workflow:
     1. 데이터셋 구조 검증 (`novels.json`, `passages.parquet`, `characters.json`)
     2. 5개 ChromaDB collection 생성
     3. Batch import (1000 passages per batch)
     4. Spring Boot API 호출 (PostgreSQL 메타데이터 생성)
2. **Import 실행 & 검증** (1h)
   ```bash
   python scripts/import_dataset.py --dataset-path /data/gutenberg
   ```
   - 10+ novels, 5000+ passages, 100+ characters import
   - `scripts/verify_import.py` 실행
   - 검증 통과 확인

**체크포인트**:

- [ ] Import script 실행 성공
- [ ] VectorDB에 5개 collection 데이터 확인
- [ ] PostgreSQL에 novel metadata 생성 확인
- [ ] Semantic search 테스트 통과

**의존성**:

- ✅ Story 0.2 (FastAPI & VectorDB) 완료 필요
- ✅ Story 0.3 (PostgreSQL) 완료 필요
- ⚠️ Backend Engineer와 협업 필요 (Spring Boot API 사용)

---

#### 💾 Backend Engineer

**Story 0.6: Inter-Service Health Check** (4h)

**작업 순서**:

1. **Health Check Endpoint 강화** (1h)

   - `GET /actuator/health`
   - PostgreSQL 상태 체크
   - FastAPI 상태 체크 (proxy)

2. **AI Proxy Controller 기본 틀** (2h)

   - `controller/AIProxyController.java`
   - FastAPI 엔드포인트 proxy:
     - `POST /api/v1/ai/search/passages`
     - `POST /api/v1/ai/chat/stream`
   - WebClient 사용

3. **통합 테스트** (1h)
   - Spring Boot → FastAPI 호출 테스트
   - Circuit Breaker 테스트
   - Error handling 테스트

**체크포인트**:

- [ ] Health check에 FastAPI 상태 포함
- [ ] AI Proxy Controller 동작 확인
- [ ] Integration test 통과

**의존성**:

- ✅ Story 0.2 (FastAPI) 완료 필요

---

#### 🎨 Frontend Engineer

**Day 3-4: 기본 레이아웃 & 네비게이션** (병렬 작업, 6h)

**작업 순서**:

1. **전역 레이아웃 컴포넌트** (2h)

   - `components/common/AppLayout.vue`
   - Header, Footer, Sidebar
   - PandaCSS로 스타일링

2. **네비게이션 바** (2h)

   - `components/common/NavBar.vue`
   - 메뉴: Home, Browse Books, My Scenarios, Profile
   - 로그인/로그아웃 버튼

3. **기본 페이지 스켈레톤** (2h)
   - `views/HomePage.vue`
   - `views/BrowseBooksPage.vue`
   - `views/NotFoundPage.vue`

**체크포인트**:

- [ ] 기본 레이아웃 렌더링 확인
- [ ] 네비게이션 작동 (Vue Router)
- [ ] 반응형 디자인 (모바일 대응)

**의존성**: ❌ 없음 (독립적 UI 작업)

---

## Phase 2: Scenario System (Epic 1, Day 5-7)

### Day 5-6: Scenario Foundation

#### 💾 Backend Engineer

**Story 1.1: Scenario Data Model & API** (8h)

**작업 순서**:

1. **Domain 모델 작성** (2h)

   - `domain/BaseScenario.java`
   - `domain/RootUserScenario.java`
   - `domain/ScenarioCharacterChange.java`
   - `domain/ScenarioEventAlteration.java`
   - `domain/ScenarioSettingModification.java`

2. **MyBatis Mapper 작성** (2h)

   - `mapper/ScenarioMapper.java`
   - CRUD SQL 매핑

3. **Service Layer** (2h)

   - `service/ScenarioService.java`
   - Business logic 구현

4. **REST API Controller** (2h)
   - `controller/ScenarioController.java`
   - `POST /api/v1/scenarios` (생성)
   - `GET /api/v1/scenarios/{id}` (조회)
   - `PUT /api/v1/scenarios/{id}` (수정)
   - `DELETE /api/v1/scenarios/{id}` (삭제)

**체크포인트**:

- [ ] CRUD API 동작 확인 (Postman)
- [ ] Unit test 통과 (>80% coverage)

**의존성**:

- ✅ Epic 0 완료 (DB, Spring Boot 설정)

---

#### 🤖 AI Engineer

**Story 2.1: Scenario to Prompt Engine** (12h, Epic 2이지만 병렬 시작)

**작업 순서**:

1. **PromptAdapter 설계** (3h)

   - `services/prompt_adapter.py`
   - 3가지 시나리오 타입별 프롬프트 생성:
     - Character Change
     - Event Alteration
     - Setting Modification

2. **VectorDB 조회 로직** (3h)

   - Passage 검색 (semantic search)
   - Character 정보 검색
   - Location/Event 정보 검색

3. **Prompt Template 작성** (3h)

   - system_instruction 생성
   - Redis 캐싱 (1시간 TTL)

4. **API 엔드포인트** (3h)
   - `POST /api/prompts/generate`
   - Request: `scenario_id`, `character_name`
   - Response: `prompt`, `token_count`, `temperature`

**체크포인트**:

- [ ] Prompt 생성 성공
- [ ] VectorDB 조회 <100ms
- [ ] Redis 캐싱 동작 확인

**의존성**:

- ✅ Epic 0 완료 (VectorDB 데이터 import)
- ⚠️ Story 1.1 완료 후 통합 가능

---

#### 🎨 Frontend Engineer

**Story 1.2: Unified Scenario Creation Modal** (12h)

**작업 순서**:

1. **시나리오 폼 컴포넌트** (4h)

   - `components/scenario/ScenarioCreateModal.vue`
   - PrimeVue Dialog 사용
   - 3가지 타입 선택: Character Change, Event Alteration, Setting Modification

2. **Character Change 폼** (3h)

   - Character 선택 (VectorDB 검색)
   - Attribute 변경 (name, personality, etc.)
   - Reasoning 입력

3. **Event/Setting 폼** (3h)

   - Event/Location 선택
   - 변경 사항 입력

4. **API 연동** (2h)
   - `POST /api/v1/scenarios` 호출
   - Loading state, Error handling
   - Success 후 리다이렉트

**체크포인트**:

- [ ] 시나리오 생성 폼 동작
- [ ] API 호출 성공
- [ ] Validation 동작

**의존성**:

- ✅ Story 1.1 (Backend API) 완료 필요

---

### Day 7: Scenario Validation

#### 🤖 AI Engineer

**Story 1.3: Scenario Validation System** (6h)

**작업 순서**:

1. **Gemini API 검증 로직** (3h)

   - `services/scenario_validator.py`
   - 품질 점수 계산 (0-100)
   - 논리적 일관성 체크

2. **Validation API** (2h)

   - `POST /api/scenarios/validate`
   - Request: `scenario_data`
   - Response: `quality_score`, `issues[]`, `suggestions[]`

3. **Redis 캐싱** (1h)
   - 검증 결과 캐싱 (5분 TTL)

**체크포인트**:

- [ ] 검증 API 동작
- [ ] 품질 점수 정확도 확인

**의존성**:

- ✅ Epic 0 완료 (Gemini API 설정)

---

#### 💾 Backend Engineer & 🎨 Frontend Engineer

**Integration & Testing** (협업, 각 2h)

**작업**:

- Backend: Validation API proxy (`POST /api/v1/ai/scenarios/validate`)
- Frontend: Validation 결과 UI 표시
- 통합 테스트: 시나리오 생성 → 검증 → 저장 플로우

---

## Phase 3: Conversation System (Epic 4, Day 8-11)

### Day 8-9: Message Streaming

#### 🤖 AI Engineer

**Story 4.2: Message Streaming & AI Integration** (12h)

**작업 순서**:

1. **Gemini Streaming 구현** (4h)

   - `services/gemini_streaming.py`
   - `generate_content_stream()` 사용
   - HTTP chunked transfer

2. **Context Manager 통합** (4h)

   - Story 2.2 로직 사용
   - 1M token window 관리

3. **Redis Task Storage** (2h)

   - Long Polling용 task 상태 저장
   - TTL: 600초 (10분)

4. **Streaming API** (2h)
   - `POST /api/chat/stream`
   - Return: `task_id`

**체크포인트**:

- [ ] Streaming 동작 확인
- [ ] 첫 토큰 <3초 생성
- [ ] Redis task 저장 확인

**의존성**:

- ✅ Story 2.2 (Context Manager) 완료 필요

---

#### 💾 Backend Engineer

**Story 4.1: Conversation Data Model & CRUD API** (8h)

**작업 순서**:

1. **Domain 모델** (2h)

   - `domain/Conversation.java`
   - `domain/Message.java`
   - ROOT-only forking 로직

2. **Mapper & Service** (3h)

   - `mapper/ConversationMapper.java`
   - `service/ConversationService.java`

3. **REST API** (3h)
   - `POST /api/v1/conversations`
   - `GET /api/v1/conversations/{id}`
   - `POST /api/v1/conversations/{id}/messages`
   - `POST /api/v1/conversations/{id}/fork`

**체크포인트**:

- [ ] CRUD API 동작
- [ ] Forking 로직 정확성 (max depth 1)

---

#### 🎨 Frontend Engineer

**Story 4.3: Conversation Forking UI** (6h)

**작업 순서**:

1. **Chat 컴포넌트** (3h)

   - `components/conversation/ChatWindow.vue`
   - 메시지 리스트
   - 입력창
   - Long Polling (2초 간격)

2. **Fork UI** (2h)

   - Fork 버튼
   - min(6, total) 메시지 복사 표시

3. **API 연동** (1h)
   - `POST /api/v1/conversations/{id}/fork`

**체크포인트**:

- [ ] Chat UI 동작
- [ ] Long Polling 동작 (2초)
- [ ] Fork 성공

---

## Phase 4: Discovery & Social (Epic 3, 5, 6, Day 12-14)

### Day 12-13: Scenario Discovery

#### 💾 Backend Engineer

**Epic 3: Scenario Discovery APIs** (병렬, 총 20h)

**작업 순서** (우선순위):

1. **Story 3.1-3.2: Book Browse & Detail APIs** (8h)

   - `GET /api/v1/books` (pagination)
   - `GET /api/v1/books/{id}`

2. **Story 3.3: Scenario Browse APIs** (6h)

   - `GET /api/v1/scenarios` (filtering)

3. **Story 3.6: Search & Filtering** (6h)
   - Full-text search with pg_trgm

---

#### 🎨 Frontend Engineer

**Epic 3: Discovery UI** (병렬, 총 26h)

**작업 순서**:

1. **Story 3.1: Book Browse Page** (8h)

   - Book 카드 리스트
   - Pagination

2. **Story 3.2: Book Detail Page** (10h)

   - Book 상세 정보
   - Scenario 리스트

3. **Story 3.3: Scenario Browse UI** (8h)
   - Scenario 필터링 UI
   - 카드 레이아웃

---

#### 🤖 AI Engineer

**Epic 2 완성 & Epic 3 지원** (병렬, 총 8h)

**작업 순서**:

1. **Story 2.3-2.4: Testing & Refinement** (8h)
   - Character consistency 테스트
   - 10개 핵심 시나리오 테스트
   - 성능 최적화

---

### Day 14: Tree Visualization & Auth

#### 🎨 Frontend Engineer

**Epic 5: Tree Visualization** (총 20h, 분산 작업)

**작업 순서**:

1. **Story 5.1-5.2: D3.js Tree Component** (14h)

   - D3.js 트리 렌더링
   - 줌/패닝 기능

2. **Story 5.3: Navigation** (6h)
   - 클릭 이벤트
   - 하이라이트

---

#### 💾 Backend Engineer

**Epic 6: Authentication & Social** (총 59h, 우선순위 작업)

**작업 순서** (MVP 우선):

1. **Story 6.1-6.2: User Registration & Auth** (14h)

   - JWT 인증 구현
   - 회원가입/로그인 API

2. **Story 6.7-6.9: Social Features** (20h)
   - Favorites API
   - Follow API
   - Activity Feed API

---

## 📊 Work Dependency Matrix

| Story                      | AI Engineer | Backend Engineer | Frontend Engineer | 의존성         |
| -------------------------- | ----------- | ---------------- | ----------------- | -------------- |
| **Epic 0 (Day 1-4)**       |
| 0.1 (Spring Boot)          | -           | ✅ 6h            | -                 | 없음           |
| 0.2 (FastAPI)              | ✅ 6h       | -                | -                 | 없음           |
| 0.3 (PostgreSQL)           | -           | ✅ 5h            | -                 | 없음           |
| 0.4 (Vue.js)               | -           | -                | ✅ 6h             | 없음           |
| 0.5 (Docker)               | ✅ 2.5h     | ✅ 2.5h          | -                 | 0.1, 0.2 완료  |
| 0.6 (Health Check)         | -           | ✅ 4h            | -                 | 0.2 완료       |
| 0.7 (Data Import)          | ✅ 3h       | (지원)           | -                 | 0.2, 0.3 완료  |
| **Epic 1 (Day 5-7)**       |
| 1.1 (Scenario API)         | -           | ✅ 8h            | -                 | Epic 0 완료    |
| 1.2 (Scenario UI)          | -           | -                | ✅ 12h            | 1.1 완료       |
| 1.3 (Validation)           | ✅ 6h       | (Proxy) 2h       | (UI) 2h           | Epic 0 완료    |
| **Epic 2 (Day 5-7, 병렬)** |
| 2.1 (Prompt Engine)        | ✅ 12h      | -                | -                 | 0.7 완료       |
| 2.2 (Context Manager)      | ✅ 8h       | -                | -                 | 2.1 완료       |
| 2.3-2.4 (Testing)          | ✅ 12h      | -                | -                 | 2.2 완료       |
| **Epic 4 (Day 8-11)**      |
| 4.1 (Conv. API)            | -           | ✅ 8h            | -                 | Epic 0 완료    |
| 4.2 (Streaming)            | ✅ 12h      | -                | -                 | 2.2 완료       |
| 4.3 (Chat UI)              | -           | -                | ✅ 6h             | 4.1, 4.2 완료  |
| **Epic 3 (Day 12-13)**     |
| 3.1-3.3 (Browse)           | -           | ✅ 14h           | ✅ 26h            | Epic 0, 1 완료 |
| 3.6 (Search)               | -           | ✅ 6h            | (UI)              | 3.1-3.3 완료   |
| **Epic 5 (Day 14)**        |
| 5.1-5.3 (Tree)             | -           | (API) 4h         | ✅ 20h            | Epic 4 완료    |
| **Epic 6 (Day 12-14)**     |
| 6.1-6.2 (Auth)             | -           | ✅ 14h           | ✅ 10h            | Epic 0 완료    |
| 6.7-6.9 (Social)           | -           | ✅ 20h           | ✅ 15h            | 6.1-6.2 완료   |

---

## 🚦 Daily Integration Checkpoints

### 매일 오후 6시: 통합 테스트

**Day 1-2 체크포인트**:

- [ ] Docker Compose 전체 스택 실행 성공
- [ ] Health checks 통과 (postgres, vectordb, redis, backend, ai-service, frontend)
- [ ] 기본 API 호출 테스트 (Spring Boot → FastAPI)

**Day 3-4 체크포인트**:

- [ ] VectorDB 데이터 import 완료 (10+ novels)
- [ ] PostgreSQL metadata 생성 확인
- [ ] Semantic search 테스트 통과 ("brave protagonist" 쿼리)

**Day 5-7 체크포인트**:

- [ ] 시나리오 생성 플로우 E2E 테스트
  - Frontend: 폼 입력
  - Backend: API 저장
  - AI: Validation 통과
- [ ] Prompt 생성 테스트 (시나리오 → Gemini prompt)

**Day 8-11 체크포인트**:

- [ ] 대화 생성 플로우 E2E 테스트
  - Frontend: Chat UI 입력
  - Backend: Long Polling (2초)
  - AI: Streaming 응답 (<3초 첫 토큰)
- [ ] Conversation forking 테스트 (ROOT-only, min(6, total) 복사)

**Day 12-14 체크포인트**:

- [ ] 전체 User Journey 테스트
  - 회원가입 → 로그인 → Book Browse → 시나리오 생성 → 대화 → Fork → 트리 시각화
- [ ] 성능 테스트 (API <500ms, AI 첫 토큰 <3초)

---

## 🔧 Troubleshooting Guide

### AI Engineer 일반 이슈

**이슈 1: Gemini API 429 Too Many Requests**

- 원인: Rate limit 초과
- 해결: Retry logic 확인 (exponential backoff), Rate limiting 추가

**이슈 2: VectorDB 연결 실패**

- 원인: ChromaDB 서비스 미실행
- 해결: `docker-compose up vectordb` 확인

**이슈 3: Embedding 생성 느림 (>1초)**

- 원인: Batch processing 미적용
- 해결: Batch embedding API 사용 (100개씩)

---

### Backend Engineer 일반 이슈

**이슈 1: WebClient Timeout**

- 원인: FastAPI 응답 지연
- 해결: Timeout 60초로 증가, Circuit Breaker 설정 확인

**이슈 2: Flyway Migration 실패**

- 원인: SQL 문법 오류
- 해결: PostgreSQL 15 호환 문법 확인, 마이그레이션 순서 검증

**이슈 3: CORS 에러**

- 원인: Frontend origin 미등록
- 해결: `SecurityConfig.java`에 `http://localhost:3000` 추가

---

### Frontend Engineer 일반 이슈

**이슈 1: Axios 401 Unauthorized**

- 원인: JWT 토큰 만료
- 해결: Token refresh 로직 확인, 인터셉터 검증

**이슈 2: PandaCSS 스타일 미적용**

- 원인: Codegen 미실행
- 해결: `pnpm panda codegen` 실행

**이슈 3: Long Polling 동작 안 함**

- 원인: Task ID 미전달
- 해결: Backend API 응답 확인, 2초 interval 검증

---

## 📈 Success Metrics by Engineer

### AI Engineer KPIs

- **Gemini API 응답 시간**: 첫 토큰 <3초
- **VectorDB 쿼리 시간**: <100ms (top-10 semantic search)
- **Prompt 생성 시간**: <500ms
- **Error Rate**: <0.1% (Retry 후)

### Backend Engineer KPIs

- **API 응답 시간** (P95): <500ms
- **Database 쿼리 시간**: <100ms
- **Circuit Breaker 작동률**: >95%
- **Test Coverage**: >80%

### Frontend Engineer KPIs

- **First Contentful Paint**: <1.5초
- **Time to Interactive**: <3초
- **API 호출 성공률**: >99.5%
- **UI 반응성**: <100ms (사용자 입력)

---

## 🎯 Priority & Critical Path

### Critical Path (블로킹 작업)

```
Epic 0 (인프라) → Epic 1 (시나리오) → Epic 2 (AI 엔진) → Epic 4 (대화)
```

**반드시 순서대로**:

1. Epic 0 완료 없이는 어떤 Epic도 시작 불가
2. Epic 1 완료 없이는 시나리오 생성 불가
3. Epic 2 완료 없이는 AI 대화 불가

### Parallel Tracks (병렬 가능)

- **Epic 1 & Epic 2**: Story 1.1 후 2.1 시작 가능
- **Epic 3**: Epic 1 완료 후 언제든 시작 (독립적)
- **Epic 5**: Epic 4 완료 후 시작
- **Epic 6**: Epic 0 완료 후 언제든 시작 (인증 부분)

---

## 📝 Communication Protocol

### Daily Standup (09:00-09:15)

**각 엔지니어 보고 형식**:

1. **어제 완료**: 구체적 Story/Task 명시
2. **오늘 할 것**: Story/Task + 예상 완료 시간
3. **블로커**: 다른 팀원 작업 대기 중인지 명시

**예시**:

```
🤖 AI Engineer:
- 어제: Story 0.2 완료 (FastAPI 셋업, Gemini API 테스트)
- 오늘: Story 0.7 시작 (VectorDB import), 예상 12시 완료
- 블로커: Story 0.3 (PostgreSQL) 대기 중 → Backend 확인 필요

💾 Backend Engineer:
- 어제: Story 0.3 완료 (13개 테이블 마이그레이션)
- 오늘: Story 0.6 시작 (Health check), 예상 15시 완료
- 블로커: 없음

🎨 Frontend Engineer:
- 어제: Story 0.4 완료 (Vue 프로젝트 셋업)
- 오늘: 기본 레이아웃 작업 (6h), 예상 18시 완료
- 블로커: 없음 (독립 작업)
```

### Integration Point (18:00-18:30)

**통합 테스트 체크리스트**:

- [ ] `docker-compose up` 전체 스택 실행
- [ ] Health checks 모두 통과
- [ ] 오늘 완료된 기능 E2E 테스트
- [ ] 이슈 발견 시 즉시 공유 → 다음날 오전 최우선 수정

---

## 📚 Documentation Responsibilities

### AI Engineer

- FastAPI API 문서 (`/docs` Swagger)
- VectorDB schema 문서 (5 collections)
- Gemini API 사용 가이드

### Backend Engineer

- Spring Boot API 문서 (Spring REST Docs)
- Database schema 문서 (13 tables + ERD)
- API Gateway 설정 가이드

### Frontend Engineer

- Component library 문서 (Storybook)
- API client 사용 가이드
- UI/UX 디자인 시스템 문서

---

## ✅ Epic Completion Checklist

### Epic 0 Complete

- [ ] AI: FastAPI 실행 + VectorDB 데이터 10+ novels
- [ ] Backend: Spring Boot 실행 + PostgreSQL 13 tables
- [ ] Frontend: Vue.js 실행 + 기본 레이아웃
- [ ] 통합: Docker Compose 전체 스택 healthy

### Epic 1 Complete

- [ ] AI: Prompt engine 동작 (시나리오 → prompt)
- [ ] Backend: Scenario CRUD API 완료
- [ ] Frontend: 시나리오 생성 폼 동작
- [ ] 통합: 시나리오 생성 E2E 테스트 통과

### Epic 2 Complete

- [ ] AI: Context Manager (1M token), Character Consistency 테스트 통과
- [ ] Backend: AI proxy API 완료
- [ ] Frontend: (Epic 4에서 통합)
- [ ] 통합: Prompt 생성 테스트 통과

### Epic 4 Complete

- [ ] AI: Streaming 동작 (<3초 첫 토큰)
- [ ] Backend: Conversation CRUD + Fork API
- [ ] Frontend: Chat UI + Long Polling (2초)
- [ ] 통합: 대화 생성 → Streaming → Fork E2E 테스트

---

**Document Owner**: John (PM)  
**Last Updated**: 2025-11-19  
**Next Review**: 2025-11-26 (프로젝트 시작 후 1주)
