# 🚀 서비스 실행 가이드

## 사전 준비사항

### 1. 필수 파일 확인
- `.env` 파일 (API 키 설정)
- `data/file_search_store_info.json` (File Search Store 정보)
- `data/characters/` 폴더 (캐릭터 정보)
- `data/origin_txt/` 폴더 (책 텍스트 파일들)

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일 생성:
```env
# Gemini API 키 (필수)
GEMINI_API_KEYS=YOUR-GEMINI-API-KEY1,YOUR-GEMINI-API-KEY2,YOUR-GEMINI-API-KEY3

# 또는 단일 키 (레거시 지원)
# GEMINI_API_KEY=YOUR-GEMINI-API-KEY

# Redis 설정 (선택적 - Celery 및 Long Polling용)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # 비밀번호가 있으면 설정

# Spring Boot URL (CORS 설정용)
SPRING_BOOT_URL=http://localhost:8080
CORS_ALLOWED_ORIGINS=http://localhost:8080

# 로깅 설정 (선택적)
LOG_LEVEL=INFO
LOG_FORMAT=console  # "console" 또는 "json"

# VectorDB 설정 (선택적)
VECTORDB_TYPE=chromadb  # "chromadb" 또는 "pinecone"
CHROMA_PATH=./chroma_data
```

## 서버 실행

### 방법 1: 직접 실행 (권장)

```bash
cd gajiAI/rag-chatbot_test
py -m uvicorn app.main:app --reload
```

서버가 시작되면: http://localhost:8000

### 방법 2: Docker Compose (선택적)

**사전 요구사항**: Docker Desktop 실행 중

```bash
# 모든 서비스 시작 (FastAPI + Redis + Celery)
docker-compose up -d

# 로그 확인
docker-compose logs -f fastapi

# 서비스 중지
docker-compose down
```

### 방법 3: Redis 및 Celery 워커 실행 (선택적)

비동기 작업(소설 임베딩, 캐릭터 추출)을 사용하려면 Redis와 Celery 워커가 필요합니다.

#### Redis 실행

**Windows**:
```bash
# 방법 1: 스크립트 사용
scripts\start_redis.bat

# 방법 2: Docker 직접 실행
docker run -d -p 6379:6379 --name gaji-redis redis:latest
```

**Linux/Mac**:
```bash
# 방법 1: 스크립트 사용
./scripts/start_redis.sh

# 방법 2: Docker 직접 실행
docker run -d -p 6379:6379 --name gaji-redis redis:latest
```

#### Celery 워커 실행

**Windows**:
```bash
scripts\start_celery_worker.bat
```

**Linux/Mac**:
```bash
chmod +x scripts/start_celery_worker.sh
./scripts/start_celery_worker.sh
```

**참고**: Celery 워커는 별도 터미널 창에서 실행해야 합니다.

## 주요 API 엔드포인트

- **API 문서**: http://localhost:8000/docs
- **헬스 체크**: `GET /health`
- **캐릭터 목록**: `GET /api/ai/characters`
- **캐릭터 정보**: `GET /api/ai/characters/info/{character_name}`
- **AI 대화**: `POST /api/ai/conversations/{conversation_id}/messages`
- **시나리오 생성**: `POST /api/scenarios`
- **시나리오 목록**: `GET /api/scenarios`
- **시나리오 상세**: `GET /api/scenarios/{id}`
- **시나리오 대화**: `POST /api/scenarios/{scenario_id}/chat`
- **시나리오 Fork**: `POST /api/scenarios/{id}/fork`
- **소설 임베딩**: `POST /api/ai/novels/ingest`
- **캐릭터 추출**: `POST /api/ai/characters/extract`
- **의미 검색**: `POST /api/ai/search/passages`
- **메트릭 조회**: `GET /api/metrics`
- **작업 상태**: `GET /api/tasks/{task_id}/status`

## 문제 해결

### 서버가 시작되지 않는 경우
1. **포트 충돌**: `--port 8001` 옵션으로 다른 포트 사용
2. **API 키 오류**: `.env` 파일의 API 키 확인
3. **File Search Store 오류**: `py scripts/setup_file_search.py --mode main` 실행

### Docker 오류
- Docker Desktop이 실행 중인지 확인: `docker ps`
- Docker Desktop이 없으면 방법 1(직접 실행) 사용

### Redis/Celery 오류
- **Redis 연결 실패**: Redis가 실행 중인지 확인 (`docker ps` 또는 `redis-cli ping`)
- **Celery 워커 오류**: 
  - Windows에서는 `--pool=solo` 옵션이 자동 적용됩니다
  - 프로젝트 루트 디렉토리에서 실행해야 합니다
  - `ModuleNotFoundError: No module named 'app'` 오류 시: 스크립트를 사용하세요 (`scripts/start_celery_worker.bat`)

**참고**: Redis와 Celery는 선택적 구성 요소입니다. 없어도 기본 AI 대화 기능은 정상 작동합니다. 다만 비동기 작업(소설 임베딩, 캐릭터 추출)은 Celery 워커가 필요합니다.

## 참고사항

### 필수 구성 요소
- ✅ FastAPI 서버
- ✅ Gemini API 키
- ✅ File Search Store (`data/file_search_store_info.json`)

### 선택적 구성 요소

**없어도 기본 기능 작동**:
- ⚪ Redis (Long Polling 및 Celery 브로커용)
- ⚪ Celery 워커 (비동기 작업용)

**비동기 작업 사용 시 필요**:
- ✅ Redis (Celery 브로커)
- ✅ Celery 워커 실행

**비동기 작업 예시**:
- 소설 임베딩 (`POST /api/ai/novels/ingest`)
- 캐릭터 추출 (`POST /api/ai/characters/extract`)

### 실행 순서 (비동기 작업 사용 시)

1. **Redis 시작** (선택적)
   ```bash
   scripts\start_redis.bat  # Windows
   # 또는
   docker-compose up -d redis
   ```

2. **Celery 워커 시작** (선택적)
   ```bash
   scripts\start_celery_worker.bat  # Windows
   ```

3. **FastAPI 서버 시작**
   ```bash
   py -m uvicorn app.main:app --reload
   ```

### 서비스 상태 확인

- **FastAPI**: http://localhost:8000/health
- **API 문서**: http://localhost:8000/docs
- **메트릭**: http://localhost:8000/api/metrics
