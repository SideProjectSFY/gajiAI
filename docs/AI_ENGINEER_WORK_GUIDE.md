# Gaji Platform: AI Engineer Work Guide 🤖

**Last Updated**: 2025-11-19  
**Version**: 1.0  
**Engineer**: AI Engineer (Python/FastAPI/Gemini API)

---

## 📋 Overview

이 문서는 **AI Engineer** 전용 작업 가이드입니다. FastAPI AI Service, VectorDB, Gemini API 통합, Prompt Engineering 관련 모든 작업이 포함됩니다.

**담당 영역**:

- FastAPI AI Service (:8000)
- Google Gemini API (2.5 Flash + Embedding)
- VectorDB (ChromaDB/Pinecone)
- Redis (Long Polling task storage)
- Celery (Async task queue)

**핵심 목표**:

- 첫 토큰 생성 <3초
- VectorDB 쿼리 <100ms
- Prompt 생성 <500ms

---

## 🎯 Role & Responsibilities

### 주요 책임

1. **AI Service 개발**: FastAPI 기반 AI 마이크로서비스
2. **Gemini API 통합**: Text generation + Embedding
3. **VectorDB 관리**: 5개 collection (passages, characters, locations, events, themes)
4. **Prompt Engineering**: 시나리오 → Gemini prompt 변환
5. **Performance Optimization**: Caching, Token management

### 기술 스택

- **Language**: Python 3.11+
- **Framework**: FastAPI, Uvicorn
- **AI**: Google Gemini 2.5 Flash API, Gemini Embedding API (768-dim)
- **VectorDB**: ChromaDB (dev), Pinecone (prod)
- **Cache**: Redis (Long Polling, 600s TTL)
- **Async**: Celery (task queue)

---

## 📅 Day-by-Day Work Schedule

### Day 1-2: FastAPI & VectorDB Setup (9h)

#### Day 1: 기초 인프라 구축 (6h)

**Story 0.2: FastAPI AI Service Setup**

**09:00-12:00 (3h): 환경 설정 & Gemini API**

```bash
# 1. Python 환경 설정 (1h)
mkdir -p ai-backend/app/{api,services,models,utils}
cd ai-backend
uv init
uv pip install fastapi>=0.121.3 uvicorn pydantic-settings>=2.12.0 \
  google-generativeai>=0.8.3 chromadb>=1.3.5 pinecone>=8.0 \
  redis>=7.1.0 celery>=5.5.3 httpx tenacity>=9.0.0 structlog>=25.1.0 \
  "numpy<2.0.0"

# 2. Gemini API 설정 (2h)
# .env 파일 생성
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004

# services/gemini_client.py 작성
# - Gemini 2.5 Flash 클라이언트
# - Retry logic (3회, exponential backoff)
# - Test: 간단한 텍스트 생성
```

**13:00-15:00 (2h): VectorDB 설정**

```python
# services/vectordb_client.py
# 5개 collection 생성:
# - novel_passages (5000+ passages)
# - characters (100+ characters)
# - locations (50+ locations)
# - events (200+ events)
# - themes (30+ themes)

# 테스트: Collection 생성 및 샘플 데이터 삽입
```

**16:00-18:00 (2h): FastAPI 앱 구조**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gaji AI Service")

# CORS: Spring Boot only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
)

# api/health.py
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai-backend"}

# Port 8000 실행
# uvicorn app.main:app --reload --port 8000
```

**체크포인트 (Day 1)**:

- [ ] `uvicorn app.main:app --reload` 실행 성공
- [ ] `GET /health` 응답: `{"status": "healthy"}`
- [ ] Gemini API 테스트 통과 (텍스트 생성 1회)
- [ ] ChromaDB 5개 collection 생성 확인

**의존성**: ❌ 없음 (독립적 작업)

---

#### Day 2: Redis & Docker 협업 (3h)

**19:00-21:00 (2h): Redis 설정 (야간 작업)**

```bash
# Redis 연결 테스트
docker run --name gaji-redis -p 6379:6379 -d redis:7

# services/redis_client.py
# - Redis 클라이언트 설정
# - Long Polling task storage (TTL 600s)
# - Celery 기본 설정
```

**Story 0.5: Docker Configuration (협업, 2.5h)**

**13:00-15:30 (2.5h): FastAPI Dockerfile 작성**

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml (일부)
services:
  vectordb:
    image: chromadb/chroma:1.3.5
    ports:
      - "8001:8000"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  ai-service:
    build: ./ai-backend
    ports:
      - "8000:8000"
    depends_on:
      - vectordb
      - redis
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

**체크포인트 (Day 2)**:

- [ ] Redis 연결 성공
- [ ] `docker-compose up ai-service` 실행 성공
- [ ] VectorDB & Redis 서비스 healthy

**의존성**:

- ⚠️ Backend Engineer와 협업 (docker-compose.yml 통합)

---

### Day 3: VectorDB Data Import (3h)

**Story 0.7: VectorDB Data Import**

**09:00-12:00 (3h): Import Script 작성 & 실행**

```python
# scripts/import_dataset.py
import argparse
from app.services.vectordb_client import VectorDBClient
from app.services.gemini_client import GeminiClient

def import_novels(dataset_path: str):
    """
    Import 10+ novels to VectorDB
    - novels.json: Novel metadata
    - passages.parquet: 5000+ passages
    - characters.json: 100+ characters
    """
    vectordb = VectorDBClient()
    gemini = GeminiClient()

    # 1. Load dataset
    novels = load_json(f"{dataset_path}/novels.json")
    passages = load_parquet(f"{dataset_path}/passages.parquet")
    characters = load_json(f"{dataset_path}/characters.json")

    # 2. Generate embeddings (batch 100)
    for i in range(0, len(passages), 100):
        batch = passages[i:i+100]
        embeddings = gemini.embed_batch([p['text'] for p in batch])
        vectordb.add_passages(batch, embeddings)

    # 3. Add characters, locations, events, themes
    # ...

    print(f"Import complete: {len(novels)} novels, {len(passages)} passages")

# 실행
# python scripts/import_dataset.py --dataset-path /data/gutenberg
```

**검증 스크립트**:

```python
# scripts/verify_import.py
def verify():
    vectordb = VectorDBClient()

    # Count check
    assert vectordb.count("novel_passages") > 5000
    assert vectordb.count("characters") > 100

    # Semantic search test
    results = vectordb.search("brave protagonist", collection="characters", top_k=5)
    assert len(results) == 5

    print("✅ VectorDB import verification passed")

# python scripts/verify_import.py
```

**체크포인트 (Day 3)**:

- [ ] Import script 실행 성공 (10+ novels, 5000+ passages)
- [ ] VectorDB 5개 collection 데이터 확인
- [ ] Semantic search 테스트 통과 ("brave protagonist" → 5 results)
- [ ] PostgreSQL novel metadata 생성 확인 (Backend와 협업)

**의존성**:

- ✅ Story 0.2 (FastAPI & VectorDB) 완료 필요
- ⚠️ Backend Engineer와 협업 (Spring Boot API 호출하여 PostgreSQL 메타데이터 생성)

---

### Day 4: 대기 & 준비 작업 (2h)

**준비 작업**: Epic 1, 2 설계 & 계획

**16:00-18:00 (2h): 다음 주 작업 준비**

- Prompt Engine 설계 (Story 2.1)
- VectorDB 쿼리 최적화 전략
- Redis 캐싱 전략 설계

---

### Day 5-7: Epic 2 - AI Engine (32h)

#### Day 5: Prompt Engine 구현 (12h)

**Story 2.1: Scenario to Prompt Engine**

**09:00-12:00 (3h): PromptAdapter 설계**

```python
# services/prompt_adapter.py
from typing import Dict, List
from app.models.scenario import BaseScenario
from app.services.vectordb_client import VectorDBClient

class PromptAdapter:
    """
    시나리오 → Gemini prompt 변환
    3가지 타입 지원:
    - CHARACTER_CHANGE
    - EVENT_ALTERATION
    - SETTING_MODIFICATION
    """

    def __init__(self):
        self.vectordb = VectorDBClient()
        self.redis = RedisClient()

    def generate_prompt(self, scenario: BaseScenario) -> Dict:
        """
        Main prompt generation logic
        """
        # 1. VectorDB 조회
        context = self._fetch_context(scenario)

        # 2. Prompt template 적용
        prompt = self._apply_template(scenario, context)

        # 3. Redis 캐싱 (1h TTL)
        cache_key = f"prompt:{scenario.id}"
        self.redis.setex(cache_key, 3600, prompt)

        return {
            "prompt": prompt,
            "token_count": len(prompt.split()),
            "temperature": 0.7
        }
```

**13:00-15:00 (2h): VectorDB 조회 로직**

```python
def _fetch_context(self, scenario: BaseScenario) -> Dict:
    """
    VectorDB에서 관련 컨텍스트 조회
    """
    context = {}

    # 1. Passage 검색 (semantic search)
    if scenario.novel_id:
        passages = self.vectordb.search(
            query=scenario.character_name or scenario.event_name,
            collection="novel_passages",
            filter={"novel_id": scenario.novel_id},
            top_k=10
        )
        context["passages"] = passages

    # 2. Character 정보 검색
    if scenario.character_name:
        characters = self.vectordb.search(
            query=scenario.character_name,
            collection="characters",
            top_k=3
        )
        context["character"] = characters[0]

    # 3. Location/Event 정보
    # ...

    return context
```

**16:00-21:00 (5h): Prompt Template 작성 & API**

```python
# templates/prompt_templates.py
CHARACTER_CHANGE_TEMPLATE = """
You are a creative storytelling AI. Generate a compelling "what if" scenario.

**Original Context:**
{passages}

**Character:** {character_name}
**Original Traits:** {original_traits}
**Changed Trait:** {changed_trait}
**Reasoning:** {reasoning}

Generate a 200-word scenario exploring how this character change would alter the story.
"""

# api/prompt.py
from fastapi import APIRouter
from app.services.prompt_adapter import PromptAdapter

router = APIRouter(prefix="/api/prompts")

@router.post("/generate")
async def generate_prompt(scenario_id: str):
    adapter = PromptAdapter()
    # scenario = fetch_scenario_from_backend(scenario_id)
    prompt_data = adapter.generate_prompt(scenario)
    return prompt_data
```

**체크포인트 (Day 5)**:

- [ ] Prompt 생성 API 동작 (`POST /api/prompts/generate`)
- [ ] VectorDB 조회 <100ms
- [ ] Redis 캐싱 동작 확인 (1h TTL)

**의존성**:

- ✅ Story 0.7 (VectorDB import) 완료 필요
- ⚠️ Story 1.1 (Backend Scenario API) 완료 후 통합 가능

---

#### Day 6: Validation System (6h)

**Story 1.3: Scenario Validation System**

**09:00-12:00 (3h): Gemini API 검증 로직**

```python
# services/scenario_validator.py
from app.services.gemini_client import GeminiClient

class ScenarioValidator:
    """
    시나리오 품질 검증 (Gemini API 사용)
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.redis = RedisClient()

    def validate(self, scenario_data: Dict) -> Dict:
        """
        품질 점수 계산 (0-100)
        """
        # 1. Gemini API로 검증 요청
        validation_prompt = self._build_validation_prompt(scenario_data)
        response = self.gemini.generate(validation_prompt)

        # 2. 결과 파싱
        issues = self._extract_issues(response)
        suggestions = self._extract_suggestions(response)

        # 3. Redis 캐싱 (5분 TTL)
        cache_key = f"validation:{scenario_data['id']}"
        self.redis.setex(cache_key, 300, {
            "issues": issues,
            "suggestions": suggestions
        })

        return {
            "issues": issues,
            "suggestions": suggestions
        }
```

**13:00-15:00 (2h): Validation API & Redis 캐싱**

```python
# api/validation.py
@router.post("/scenarios/validate")
async def validate_scenario(scenario_data: Dict):
    validator = ScenarioValidator()
    result = validator.validate(scenario_data)
    return result
```

**체크포인트 (Day 6)**:

- [ ] Validation API 동작 (`POST /api/scenarios/validate`)
- [ ] 품질 점수 정확도 확인 (수동 테스트 10개)
- [ ] Redis 캐싱 동작 (5분 TTL)

**의존성**:

- ✅ Epic 0 완료 (Gemini API 설정)

---

#### Day 7: Context Manager & Character Consistency (14h)

**Story 2.2: Context Window Manager**

**09:00-13:00 (4h): Context Manager 구현**

```python
# services/context_manager.py
class ContextManager:
    """
    1M token window 관리
    """

    def __init__(self):
        self.max_tokens = 1_000_000
        self.redis = RedisClient()

    def manage_context(self, conversation_id: str, messages: List[Dict]) -> List[Dict]:
        """
        Token counting & window sliding
        """
        # 1. Token counting
        total_tokens = sum(self._count_tokens(msg['content']) for msg in messages)

        # 2. Window sliding (최신 메시지 우선)
        if total_tokens > self.max_tokens:
            messages = self._slide_window(messages, self.max_tokens)

        # 3. Redis 저장 (conversation context)
        self.redis.setex(f"context:{conversation_id}", 3600, messages)

        return messages

    def _count_tokens(self, text: str) -> int:
        # Approximate token counting (1 token ≈ 4 chars)
        return len(text) // 4
```

**14:00-18:00 (4h): Story 2.3 - Character Consistency**

```python
# services/character_consistency.py
class CharacterConsistencyTracker:
    """
    캐릭터 일관성 추적
    """

    def __init__(self):
        self.vectordb = VectorDBClient()
        self.gemini = GeminiClient()

    def extract_traits(self, character_name: str, passages: List[str]) -> Dict:
        """
        Trait extraction using Gemini
        """
        # 1. Gemini API로 trait 추출
        prompt = f"Extract personality traits of {character_name} from: {passages}"
        response = self.gemini.generate(prompt)

        # 2. Parse traits (JSON format)
        traits = self._parse_traits(response)

        # 3. VectorDB 저장 (Triple storage)
        self.vectordb.add(
            collection="character_traits",
            documents=[{
                "character": character_name,
                "trait": trait,
                "evidence": passages
            } for trait in traits]
        )

        return traits
```

**19:00-21:00 (2h): 통합 & 테스트**

```python
# 통합 테스트
def test_context_manager():
    manager = ContextManager()
    messages = [{"role": "user", "content": "Hello"} for _ in range(1000)]
    result = manager.manage_context("conv-123", messages)
    assert len(result) <= 1_000_000 // 4  # Token limit check

def test_character_consistency():
    tracker = CharacterConsistencyTracker()
    traits = tracker.extract_traits("Elizabeth Bennet", ["passage1", "passage2"])
    assert "prideful" in traits or "intelligent" in traits
```

**체크포인트 (Day 7)**:

- [ ] Context Manager 동작 (1M token 관리)
- [ ] Character Consistency 추출 테스트 통과
- [ ] VectorDB에 trait 저장 확인

**의존성**:

- ✅ Story 2.1 (Prompt Engine) 완료 필요

---

### Day 8-9: Epic 4 - Streaming (24h)

#### Day 8: Streaming 구현 (12h)

**Story 4.2: Message Streaming & AI Integration**

**09:00-13:00 (4h): Gemini Streaming 구현**

```python
# services/gemini_streaming.py
from google.generativeai import GenerativeModel

class GeminiStreamingService:
    """
    Gemini 2.5 Flash Streaming
    """

    def __init__(self):
        self.model = GenerativeModel('gemini-2.0-flash-exp')

    async def stream_response(self, prompt: str, conversation_id: str):
        """
        HTTP chunked transfer encoding
        목표: 첫 토큰 <3초
        """
        # 1. Context Manager 통합
        context = self._load_context(conversation_id)
        full_prompt = self._build_full_prompt(context, prompt)

        # 2. Streaming 시작
        response = self.model.generate_content_stream(
            full_prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            }
        )

        # 3. Chunk-by-chunk yield
        for chunk in response:
            if chunk.text:
                yield chunk.text
```

**14:00-18:00 (4h): Context Manager 통합 & Redis Task Storage**

```python
# services/task_manager.py
class TaskManager:
    """
    Long Polling용 task 관리
    """

    def __init__(self):
        self.redis = RedisClient()

    def create_task(self, conversation_id: str, user_message: str) -> str:
        """
        Task 생성 & Redis 저장
        """
        task_id = f"task:{uuid.uuid4()}"

        # 1. Task 상태 초기화
        task_data = {
            "status": "pending",
            "conversation_id": conversation_id,
            "user_message": user_message,
            "response": "",
            "created_at": datetime.utcnow().isoformat()
        }

        # 2. Redis 저장 (TTL 600s = 10분)
        self.redis.setex(task_id, 600, json.dumps(task_data))

        return task_id

    def update_task(self, task_id: str, status: str, response: str = ""):
        """
        Task 상태 업데이트
        """
        task_data = json.loads(self.redis.get(task_id))
        task_data["status"] = status
        task_data["response"] += response  # Streaming: append
        self.redis.setex(task_id, 600, json.dumps(task_data))
```

**19:00-21:00 (2h): Streaming API 엔드포인트**

```python
# api/chat.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/chat")

@router.post("/stream")
async def stream_chat(conversation_id: str, message: str):
    """
    Streaming API
    Return: task_id for Long Polling
    """
    # 1. Task 생성
    task_manager = TaskManager()
    task_id = task_manager.create_task(conversation_id, message)

    # 2. Background task로 streaming 시작
    asyncio.create_task(process_streaming(task_id, conversation_id, message))

    return {"task_id": task_id}

async def process_streaming(task_id: str, conversation_id: str, message: str):
    """
    Background: Streaming 처리
    """
    streaming = GeminiStreamingService()
    task_manager = TaskManager()

    # Update status: processing
    task_manager.update_task(task_id, "processing")

    # Stream & update
    async for chunk in streaming.stream_response(message, conversation_id):
        task_manager.update_task(task_id, "processing", chunk)

    # Complete
    task_manager.update_task(task_id, "completed")
```

**체크포인트 (Day 8)**:

- [ ] Streaming 기본 동작 확인
- [ ] 첫 토큰 <3초 생성 (목표)
- [ ] Redis task 저장 확인 (TTL 600s)

**의존성**:

- ✅ Story 2.2 (Context Manager) 완료 필요

---

#### Day 9: Streaming 완성 & Testing (12h)

**09:00-13:00 (4h): Streaming API 완성**

- Retry 로직 (3회, exponential backoff)
- Error handling (Gemini API 429, timeout)
- Performance 튜닝 (token optimization)

**14:00-18:00 (4h): Story 2.4 - Testing & Refinement**

```python
# tests/test_scenarios.py
CORE_SCENARIOS = [
    {
        "name": "Pride and Prejudice - Elizabeth modest",
        "character": "Elizabeth Bennet",
        "trait_change": "prideful → modest",
        "expected_outcome": "acceptance of Darcy's first proposal"
    },
    # ... 10개 핵심 시나리오
]

def test_core_scenarios():
    adapter = PromptAdapter()
    streaming = GeminiStreamingService()

    for scenario in CORE_SCENARIOS:
        # 1. Prompt 생성
        prompt_data = adapter.generate_prompt(scenario)

        # 2. Streaming 테스트
        response = streaming.stream_response(prompt_data["prompt"], "test-conv")

        # 3. 검증
        assert "first token time" < 3  # <3초
        assert len(response) > 100  # 최소 100자

        print(f"✅ {scenario['name']} passed")
```

**19:00-21:00 (2h): 성능 최적화**

- VectorDB 쿼리 최적화 (batch processing)
- Redis 캐싱 전략 개선
- Token counting 최적화

**체크포인트 (Day 9)**:

- [ ] Story 4.2 완성: Streaming API (<3초 첫 토큰)
- [ ] Story 2.4 완성: 10개 핵심 시나리오 테스트 통과
- [ ] Performance 목표 달성 확인

**의존성**: ❌ 없음 (AI 독립 작업)

---

### Day 10-11: Epic 3 지원 & 성능 최적화 (16h)

#### Day 10: Semantic Search 준비 (8h)

**Epic 3 지원 준비**

**09:00-13:00 (4h): VectorDB Semantic Search 튜닝**

```python
# services/search_service.py
class SearchService:
    """
    Epic 3 Discovery를 위한 semantic search
    """

    def __init__(self):
        self.vectordb = VectorDBClient()
        self.gemini = GeminiClient()

    def semantic_search(self, query: str, filters: Dict = None) -> List[Dict]:
        """
        Semantic search with filters
        """
        # 1. Query embedding
        query_embedding = self.gemini.embed(query)

        # 2. VectorDB 검색 (threshold 0.7)
        results = self.vectordb.search(
            query_vector=query_embedding,
            collection="novel_passages",
            filter=filters,
            top_k=20,
            score_threshold=0.7
        )

        return results
```

**14:00-18:00 (4h): Story 5.1 - Tree 데이터 지원**

```python
# services/tree_service.py
class TreeService:
    """
    Conversation Tree 생성 로직
    """

    def generate_tree_data(self, conversation_id: str) -> Dict:
        """
        대화 노드 JSON 생성
        """
        # 1. Conversation 조회 (Backend API)
        messages = self._fetch_messages(conversation_id)

        # 2. Tree 구조 생성
        tree = {
            "root": conversation_id,
            "nodes": [],
            "edges": []
        }

        for i, msg in enumerate(messages):
            tree["nodes"].append({
                "id": msg["id"],
                "content": msg["content"],
                "role": msg["role"],
                "timestamp": msg["created_at"]
            })

            if i > 0:
                tree["edges"].append({
                    "from": messages[i-1]["id"],
                    "to": msg["id"]
                })

        return tree
```

**체크포인트 (Day 10)**:

- [ ] Semantic search 준비 완료 (threshold 0.7)
- [ ] Tree 데이터 생성 로직 검증

---

#### Day 11: Hybrid Search & 성능 검증 (8h)

**Story 3.6: Advanced Search (Hybrid)**

**09:00-13:00 (4h): Hybrid Search 구현**

```python
# services/hybrid_search.py
class HybridSearchService:
    """
    Keyword + Similarity 하이브리드 검색
    """

    def hybrid_search(self, query: str, filters: Dict = None) -> List[Dict]:
        """
        1. Keyword search (PostgreSQL, Backend 호출)
        2. Similarity search (VectorDB)
        3. 결과 병합 (weighted scoring)
        """
        # 1. Keyword search (Backend API 호출)
        keyword_results = self._keyword_search(query, filters)

        # 2. Similarity search
        similarity_results = self._semantic_search(query, filters)

        # 3. 병합 (0.4 * keyword_score + 0.6 * similarity_score)
        merged = self._merge_results(keyword_results, similarity_results)

        return merged[:20]  # Top 20
```

**14:00-18:00 (4h): Epic 3 완성 & 성능 검증**

- Semantic search <100ms 달성 확인
- Hybrid search 정확도 테스트
- VectorDB 인덱스 최적화

**체크포인트 (Day 11)**:

- [ ] Story 3.6 완성: Hybrid Search 동작
- [ ] Semantic search <100ms (p95)
- [ ] Epic 3 완성 (AI 파트)

---

### Day 12-13: 성능 최적화 & 부하 테스트 (16h)

#### Day 12: 성능 개선 (8h)

**09:00-13:00 (4h): Embedding 캐싱 강화**

```python
# Redis 캐싱 전략 개선
# - Embedding 캐싱: 90%+ hit rate 목표
# - Prompt 캐싱: 1h TTL
# - Validation 캐싱: 5분 TTL
```

**14:00-18:00 (4h): Context Window 메모리 최적화**

- Token counting 알고리즘 개선
- Window sliding 최적화 (최신 메시지 우선)

---

#### Day 13: 부하 테스트 & 모니터링 (8h)

**09:00-13:00 (4h): 부하 테스트**

```python
# tests/load_test.py
import asyncio
from locust import HttpUser, task

class AIServiceLoadTest(HttpUser):
    @task
    def stream_chat(self):
        self.client.post("/api/chat/stream", json={
            "conversation_id": "test",
            "message": "Hello AI"
        })

# 목표: 1000 concurrent requests
# 첫 토큰 <3초 달성 확인
```

**14:00-18:00 (4h): Query 최적화 & 모니터링 대시보드**

- VectorDB 쿼리 최적화 (batch processing)
- Grafana + Prometheus 기본 설정

**체크포인트 (Day 13)**:

- [ ] 부하 테스트 완료: 1000 concurrent
- [ ] 첫 토큰 <3초 달성 (p95)
- [ ] 모니터링 대시보드 가동

---

### Day 14: 최종 검증 & 문서화 (8h)

**09:00-13:00 (4h): 최종 성능 검증**

- Latency 측정 (p50, p95, p99)
- Error rate 확인 (<0.1%)
- Redis hit rate 확인 (>90%)

**14:00-18:00 (4h): 문서화 & 배포 준비**

- FastAPI Swagger 문서 완성 (`/docs`)
- VectorDB schema 문서 작성
- Gemini API 사용 가이드 작성
- ENV 변수 설정 문서

**체크포인트 (Day 14)**:

- [ ] 성능 목표 달성: 첫 토큰 <3초, VectorDB <100ms
- [ ] 문서 완성: API Docs, VectorDB Schema, Usage Guide
- [ ] 프로덕션 배포 준비 완료

---

## 🚦 Daily Integration Checkpoints

### 매일 오후 6시: AI Service 통합 테스트

**Day 1-2**:

- [ ] FastAPI :8000 실행 확인
- [ ] Gemini API 테스트 통과 (1회)
- [ ] VectorDB 5개 collection 생성

**Day 3-4**:

- [ ] VectorDB import 완료 (10+ novels, 5000+ passages)
- [ ] Semantic search 테스트 통과

**Day 5-7**:

- [ ] Prompt Engine 동작 (시나리오 → prompt)
- [ ] Validation API 동작 (품질 점수 계산)
- [ ] Context Manager 동작 (1M token)

**Day 8-9**:

- [ ] Streaming API 동작 (첫 토큰 <3초)
- [ ] Redis task storage 확인
- [ ] 10개 핵심 시나리오 테스트 통과

**Day 10-13**:

- [ ] Semantic search <100ms
- [ ] Hybrid search 동작
- [ ] 부하 테스트 1000 concurrent 통과

**Day 14**:

- [ ] 전체 성능 목표 달성 확인
- [ ] 문서 완성

---

## 🔧 Troubleshooting Guide

### 이슈 1: Gemini API 429 Too Many Requests

**원인**: Rate limit 초과 (15 requests/minute)
**해결**:

```python
# Retry logic with exponential backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_gemini_api():
    return gemini.generate_content(prompt)
```

### 이슈 2: VectorDB 연결 실패

**원인**: ChromaDB 서비스 미실행
**해결**:

```bash
docker-compose up vectordb
# Verify: curl http://localhost:8001/api/v1/heartbeat
```

### 이슈 3: Streaming 첫 토큰 >3초

**원인**: Context가 너무 큼
**해결**:

- Token counting 확인
- Window sliding 최적화
- Prompt 길이 축소

### 이슈 4: Redis 메모리 부족

**원인**: 캐싱 데이터 누적
**해결**:

```bash
# Redis maxmemory 설정
docker run -d --name redis -e REDIS_MAXMEMORY=2gb -e REDIS_MAXMEMORY_POLICY=allkeys-lru redis:7
```

---

## 📈 Success Metrics (KPIs)

### 성능 목표

- **첫 토큰 생성**: <3초 (p95)
- **VectorDB 쿼리**: <100ms (p95)
- **Prompt 생성**: <500ms
- **Error Rate**: <0.1% (Retry 후)

### 품질 목표

- **Validation 정확도**: >85% (수동 검증)
- **Semantic Search 정확도**: >80% (top-10 relevance)
- **Redis Hit Rate**: >90%

### 테스트 커버리지

- **Unit Tests**: >80%
- **Integration Tests**: 주요 API 플로우
- **Load Tests**: 1000 concurrent requests

---

## 📚 Documentation Checklist

### API 문서 (/docs Swagger)

- [ ] `/health` - Health check
- [ ] `POST /api/prompts/generate` - Prompt 생성
- [ ] `POST /api/scenarios/validate` - Validation
- [ ] `POST /api/chat/stream` - Streaming
- [ ] `GET /api/tasks/{id}` - Task 상태 조회

### VectorDB Schema

- [ ] 5개 collection 구조 설명
- [ ] Embedding 생성 방법
- [ ] Query 예제

### Gemini API Usage Guide

- [ ] API Key 설정 방법
- [ ] Rate limiting 가이드
- [ ] Error handling 가이드

---

**Document Owner**: AI Engineer  
**Last Updated**: 2025-11-19  
**Next Review**: Day 7 (Epic 2 완성 후)
