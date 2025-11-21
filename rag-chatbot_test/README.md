# FastAPI AI Service - Gaji AI Backend

**Epic 0 Story 0.2**: FastAPI Python service for internal AI/ML operations (Pattern B)

RAG 기반 "What If" 챗봇 대화 시스템을 위한 FastAPI 백엔드 서비스입니다.

---

## 📋 개요

이 서비스는 **내부 전용 AI/ML 서비스**로 Spring Boot를 통해서만 접근 가능합니다 (Pattern B).

### 주요 기능

1. **Gemini API Integration**: Gemini 2.5 Flash 통합 (Retry, Circuit Breaker)
2. **VectorDB Management**: ChromaDB (개발) / Pinecone (프로덕션) 추상화
3. **RAG Pipeline**: 검색 증강 생성 (Retrieval-Augmented Generation)
4. **Long Polling**: Redis 기반 비동기 작업 상태 추적
5. **Async Task Queue**: Celery를 통한 비동기 작업 처리
6. **Health Check**: 서비스 상태 모니터링

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 1. uv 설치 (권장 패키지 관리자)
pip install uv

# 2. 가상환경 생성
uv venv
# 출력 예시:
# Using CPython 3.11.6 interpreter at: /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
# Creating virtual environment at: .venv
# Activate with: source .venv/bin/activate

# 3. 가상환경 활성화
source .venv/bin/activate  # macOS/Linux
# Windows: .venv\Scripts\activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

# 4. 패키지 설치
uv pip install -r requirements.txt

# 또는 일반 pip 사용 (uv 없이)
pip install -r requirements.txt

# 5. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 설정
```

**참고**: `uv`는 Rust로 작성된 고속 Python 패키지 관리자입니다.

- 기존 pip보다 10-100배 빠른 설치 속도
- Python 3.11+ 필요
- Story 0.2 요구사항에 명시된 권장 도구

### 2. .env 파일 설정

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# VectorDB (chromadb for dev, pinecone for prod)
VECTORDB_TYPE=chromadb
CHROMA_PATH=./chroma_data
CHROMA_COLLECTION=novel_passages

# Redis (Long Polling + Celery)
REDIS_URL=redis://localhost:6379

# Spring Boot (callback URL)
SPRING_BOOT_URL=http://localhost:8080

# Application
APP_ENV=development
PORT=8000
LOG_LEVEL=INFO
```

### 3. Redis 및 Celery 실행

```bash
# Redis 실행 (Docker 사용 시)
docker run -d -p 6379:6379 redis:latest

# Celery Worker 실행
celery -A app.celery_app worker --loglevel=info

# 별도 터미널에서 Celery Beat 실행 (스케줄 작업용 - 선택)
celery -A app.celery_app beat --loglevel=info
```

### 4. 데이터 임포트 (선택)

```bash
# Pride and Prejudice 수집 및 임포트 (기존 스크립트 사용)
python scripts/collect_data.py --method datasets --titles "Pride and Prejudice" --output data/raw
python scripts/preprocess_text.py --input data/raw --output data/processed --chunk-size 400
python scripts/generate_embeddings.py --input data/processed --output data/embeddings
python scripts/import_to_chromadb.py --input data/embeddings --collection novel_passages
```

### 5. API 서버 실행

```bash
# 개발 모드 (hot reload)
uvicorn app.main:app --reload --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. API 테스트

```bash
# Health Check
curl http://localhost:8000/health

# API Documentation
open http://localhost:8000/docs

# 챗봇 대화 테스트 (Spring Boot를 통해서만 접근 가능)
# CORS 설정으로 인해 localhost:8080에서만 호출 가능
```

### 7. 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=app --cov-report=html

# 특정 테스트 파일 실행
pytest tests/test_health.py -v
```

---

## 📁 프로젝트 구조

```
rag-chatbot_test/
├── app/
│   ├── main.py                    # FastAPI 애플리케이션
│   ├── config.py                  # 환경 설정
│   ├── celery_app.py              # Celery 설정
│   ├── api/                       # API 엔드포인트
│   │   ├── health.py              # 헬스 체크
│   │   └── ingestion.py           # 소설 임포트 API
│   ├── routers/                   # 레거시 라우터 (chat.py)
│   │   └── chat.py
│   ├── services/
│   │   ├── gemini_client.py       # Gemini API 클라이언트
│   │   ├── vectordb_client.py     # VectorDB 추상화
│   │   ├── rag_service.py         # RAG 파이프라인
│   │   ├── novel_ingestion.py     # 소설 파싱 서비스
│   │   └── question_classifier.py # 질문 분류
│   ├── models/
│   │   └── schemas.py             # Pydantic 모델
│   └── utils/
│       └── redis_client.py        # Redis 유틸리티
├── tests/
│   ├── conftest.py                # pytest 설정
│   ├── test_health.py             # 헬스 체크 테스트
│   └── test_config.py             # 설정 테스트
├── scripts/                       # 데이터 임포트 스크립트
├── .env.example                   # 환경 변수 예시
├── requirements.txt               # 의존성
├── pytest.ini                     # pytest 설정
└── README.md
```

---

## 🔧 주요 기능

### 1. Gemini API Integration

- **SDK Version**: google-generativeai >= 0.8.3 (레거시), google-genai >= 1.0.0 권장
- **Model**: Gemini 2.5 Flash (1M 입력 토큰, 8K 출력 토큰)
- **Retry Logic**: 3회 재시도, 지수 백오프 (1s, 2s, 4s)
- **Circuit Breaker**: 5회 연속 실패 시 60초 대기
- **Temperature**: 대화용 0.7-0.8, 검증용 0.2
- **Timeout**: 30초
- **Embedding**: text-embedding-004 (768차원, 무료)

### 2. VectorDB Management

- **개발 환경**: ChromaDB (로컬 저장)
- **프로덕션 환경**: Pinecone (클라우드)
- **추상화 레이어**: VectorDBClient 인터페이스
- **컬렉션**: novel_passages, characters, locations, events, themes (5개)
- **Connection Pooling**: 최소 5, 최대 15 연결

### 3. RAG Pipeline

- **Semantic Search**: 사용자 질문과 관련된 청크 검색
- **Prompt Generation**: 검색된 청크 + 시나리오 컨텍스트로 프롬프트 생성
- **Response Generation**: Gemini 2.5 Flash로 응답 생성
- **Streaming Support**: SSE (Server-Sent Events)

### 4. Async Task Queue (Celery)

- **Broker**: Redis DB 0
- **Backend**: Redis DB 1
- **작업**: 소설 임포트, 캐릭터 추출, 임베딩 생성
- **Long Polling**: Redis를 통한 작업 상태 추적 (600초 TTL)

### 5. API 엔드포인트

#### 대화 API

- `POST /api/conversations/{id}/messages`: 일반 응답
- `POST /api/conversations/{id}/messages/stream`: 스트리밍 응답 (SSE)
- `POST /api/conversations/{id}/messages/no-rag`: RAG 없이 응답 (비교용)

#### 검색 API

- `GET /api/search/passages`: 청크 검색 (디버깅용)

#### 임포트 API

- `POST /api/ingestion/novels`: 소설 임포트 (비동기)
- `GET /api/ingestion/tasks/{task_id}`: 작업 상태 조회

#### 모니터링 API

- `GET /health`: 헬스 체크 (Gemini, VectorDB, Celery 상태)

---

## 💡 사용 예시

### "What If" 시나리오 예시

```python
# 시나리오: "Pride and Prejudice에서 Elizabeth가 Darcy를 만나지 않은 경우"

scenario_context = """
You are Elizabeth Bennet in an alternate timeline where you never met Mr. Darcy.
You remained in Longbourn, focused on your family's financial struggles.
You never experienced the journey of overcoming prejudice and pride.
"""

# 사용자 질문
user_message = "What is your opinion on marriage?"

# RAG 서비스 호출
response = rag_service.generate_response(
    user_message=user_message,
    scenario_context=scenario_context,
    book_id="novel_pride_and_prejudice"
)
```

---

## 📊 성능 및 비용

### 예상 처리 시간

- 데이터 수집: 1-2분 (datasets)
- 전처리: 1-2분 (1개 책 기준)
- 임베딩 생성: 5-10분 (API 레이트 리밋 고려)
- ChromaDB 임포트: 1-2분

### Gemini API 비용 (예상)

- Embedding: $0.000075 per 1K tokens
- Text Generation: $0.075 per 1M input tokens, $0.30 per 1M output tokens

**1개 책 (약 500 청크) 기준**:

- 임베딩 생성: 약 $0.10-0.20
- 대화 1회 (평균 1000 토큰): 약 $0.001

---

## 📦 패키지 버전 정보

### 주요 의존성

- **FastAPI**: 0.121.3+ (웹 프레임워크)
- **google-generativeai**: 0.8.3+ (Gemini API, 레거시)
  - 새 프로젝트는 `google-genai >= 1.0.0` 사용 권장
- **chromadb**: 1.3.5+ (벡터 DB, 로컬 개발)
  - API 변경: `chromadb.config.Settings` 클래스 제거됨
- **pinecone**: 8.0+ (벡터 DB, 프로덕션)
  - 새로운 SDK: `Pinecone(api_key)` 생성자 사용
- **redis**: 5.2.1+ (Long Polling + Celery 백엔드)
- **celery**: 5.5.3+ (비동기 작업 큐)
- **tenacity**: 9.0.0+ (재시도 로직)
- **structlog**: 25.1.0+ (구조화 로깅)

### 호환성 제약

- **NumPy**: <2.0.0 (ChromaDB 호환성)
- **Python**: 3.11+ 필요

---

## 🔒 보안 (Pattern B)

### CORS 설정

- **허용 Origin**: `http://localhost:8080` (Spring Boot만)
- **외부 접근 차단**: 프론트엔드는 직접 접근 불가
- **API 키 보호**: Gemini API 키가 프론트엔드에 노출되지 않음

### 로깅 보안

- **API 키 필터링**: 로그에 API 키가 기록되지 않도록 필터링
- **Structlog**: JSON 형식 구조화 로깅

---

## �🐛 문제 해결

### 1. Gemini API 키 오류

```bash
# 환경변수 확인
echo $GEMINI_API_KEY

# .env 파일 확인
cat .env

# API 키 유효성 확인
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"
```

### 2. ChromaDB 연결 오류

```bash
# ChromaDB 데이터 디렉토리 권한 확인
chmod -R 755 ./chroma_data

# ChromaDB 초기화
rm -rf ./chroma_data
python scripts/import_to_chromadb.py --verify
```

### 3. Redis 연결 오류

```bash
# Redis 상태 확인
redis-cli ping

# Redis 재시작 (Docker)
docker restart <redis_container_id>
```

### 4. Celery Worker 실행 안됨

```bash
# Celery 로그 확인
celery -A app.celery_app worker --loglevel=debug

# Redis 연결 확인
celery -A app.celery_app inspect ping
```

### 5. CORS 오류 (외부 접근)

이 서비스는 **내부 전용**이므로 Spring Boot를 통해서만 접근 가능합니다.

- 프론트엔드는 Spring Boot API(`localhost:8080`)를 호출
- Spring Boot가 FastAPI(`localhost:8000`)로 프록시

---

## � 테스트 커버리지

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 리포트
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### 목표 커버리지

- **목표**: 80% 이상
- **현재**: 기본 테스트 구현 완료
- **추가 필요**: RAG 서비스, Gemini Client 통합 테스트

---

## 🔄 다음 단계 (Epic 0 후속 Story)

1. **Story 0.7**: VectorDB 데이터 임포트 파이프라인
2. **Story 0.8**: 캐릭터 자동 추출 시스템
3. **Story 2.1**: Scenario-to-Prompt Engine
4. **Story 4.2**: Message Streaming (SSE)

---

## 📚 참고 자료

- [Story 0.2 요구사항](../docs/stories/epic-0-story-0.2-fastapi-ai-service-setup.md)
- [Architecture Documentation](../docs/ARCHITECTURE.md)
- [Gemini API 문서](https://ai.google.dev/docs)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [Pinecone 문서](https://docs.pinecone.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Celery 문서](https://docs.celeryq.dev/)

---

## ✅ Story 0.2 체크리스트

- [x] Python 3.11+ with uv package manager
- [x] Dependencies configured (requirements.txt)
- [x] Project structure created
- [x] Environment configuration (.env.example)
- [x] Gemini API client with Retry & Circuit Breaker
- [x] Redis client for Long Polling
- [x] VectorDB client (ChromaDB/Pinecone abstraction)
- [x] CORS middleware (Spring Boot only)
- [x] Health check endpoint (detailed status)
- [x] Celery worker configuration
- [x] API versioning (/api/\*)
- [x] Logging configured (structlog)
- [x] Base tests implemented
- [x] Documentation updated

---

**Epic**: 0 - Project Setup & Infrastructure  
**Story**: 0.2 - FastAPI AI Service Setup  
**Status**: Implementation Complete  
**작성일**: 2025-01-22  
**버전**: 0.1.0
