# Gaji AI Backend - Character Chat & What If Scenarios

**책 속 인물과 대화하고 "What If" 시나리오를 탐험하는 AI 챗봇** (Gemini File Search 기반)

> **Note**: 이 프로젝트는 마이크로서비스 아키텍처(MSA)의 일부입니다. Spring Boot 백엔드와 통신하여 웹 서비스를 제공합니다.

## 🎭 프로젝트 소개

이 프로젝트는 Gemini의 File Search 기능을 활용하여 사용자가 책 속 등장인물과 몰입감 있는 대화를 나눌 수 있는 AI 챗봇 서비스입니다. 또한 "What If" 시나리오를 생성하여 캐릭터의 속성, 사건, 배경을 변경한 대체 타임라인을 탐험할 수 있습니다.

### 주요 특징

- 📚 **원본 텍스트 기반**: 구텐베르크 프로젝트의 고전 문학 작품 활용
- 🎭 **페르소나 시스템**: 각 캐릭터의 성격, 말투, 가치관을 반영한 대화
- 🔀 **What If 시나리오**: 캐릭터 속성, 사건, 배경 변경을 통한 대체 타임라인 생성
- 🔍 **자동 인용**: Gemini File Search가 원문 출처를 자동으로 제공
- 👥 **대화 상대 선택**: 제3의 인물 또는 같은 책의 다른 주인공과 대화 선택
- 🔑 **API 키 로테이션**: 여러 API 키 자동 전환으로 안정적인 서비스

## 🎬 사용 가능한 캐릭터

| 캐릭터 | 책 | 저자 |
|--------|-----|------|
| Victor Frankenstein | Frankenstein | Mary Shelley |
| Elizabeth Bennet | Pride and Prejudice | Jane Austen |
| Jay Gatsby | The Great Gatsby | F. Scott Fitzgerald |
| Romeo Montague | Romeo and Juliet | William Shakespeare |
| Tom Sawyer | The Adventures of Tom Sawyer | Mark Twain |
| Sherlock Holmes | The Adventures of Sherlock Holmes | Arthur Conan Doyle |

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
```

`.env` 파일에 Gemini API 키 설정:

```env
# 여러 API 키 (쉼표로 구분)
GEMINI_API_KEYS=key1,key2,key3,key4

# 또는 단일 키
GEMINI_API_KEY=your_api_key_here
```

### 2. 데이터 준비

```bash
# 1) CSV 메타데이터 생성 (선택, 검색 속도 향상)
py convert_to_csv.py

# 2) 책 검색 및 저장 (이미 55개 저장되어 있음)
py scripts/collect_data.py --search "Frankenstein" --yes
```

### 3. File Search Store 설정

```bash
# Gemini File Search Store에 책 업로드
py scripts/setup_file_search.py
```

**선택 옵션**:
- 모든 책 업로드 (55개)
- 주요 책만 업로드 (5개 추천)
- 개수 지정

**소요 시간**: 책 1개당 약 30초~1분

### 4. 캐릭터 페르소나 생성 (선택)

```bash
# File Search를 사용하여 원본 텍스트와 인물 관계도를 분석하여
# 각 책의 id 1, 2 캐릭터의 페르소나와 말투를 자동 생성
py scripts/generate_character_personas.py
```

**기능**:
- `origin_txt/`의 원본 텍스트를 File Search로 분석
- `char_graph/`의 인물 관계도에서 id 1, 2 캐릭터 추출
- 각 캐릭터의 페르소나와 말투를 **영어/한국어** 이중 생성
- `data/characters/` 폴더에 책별로 JSON 파일 저장

**출력 형식**:
```json
{
  "book_title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "characters": [
    {
      "character_name": "Nick Carraway",
      "persona": "...",           // 영어 (기존 호환성)
      "persona_en": "...",        // 영어
      "persona_ko": "...",        // 한국어
      "speaking_style": "...",    // 영어 (기존 호환성)
      "speaking_style_en": "...", // 영어
      "speaking_style_ko": "..."  // 한국어
    }
  ]
}
```

**소요 시간**: 책 1개당 약 4-6분 (캐릭터 2명 × 4개 생성)

**주의사항**:
- File Search Store가 설정되어 있어야 합니다
- API 키 할당량을 고려하여 실행하세요

### 5. 테스트

```bash
# 터미널에서 캐릭터와 대화
py test_character_chat.py
```

### 6. API 서버 실행

```bash
# FastAPI 서버 시작
uvicorn app.main:app --reload
```

서버 실행 후: http://localhost:8000/docs

## 📡 API 사용법

### Base URL
- **FastAPI**: `http://localhost:8000/api`
- **API 문서**: `http://localhost:8000/docs` (Swagger UI)

### 1. 캐릭터 목록 조회

```http
GET /api/ai/characters
```

**응답**:
```json
{
  "characters": [
    {
      "character_name": "Victor Frankenstein",
      "book_title": "Frankenstein; Or, The Modern Prometheus",
      "author": "Mary Shelley"
    }
  ],
  "total": 6
}
```

### 2. 캐릭터 정보 조회

```http
GET /api/ai/characters/info/{character_name}?book_title=Frankenstein
```

### 3. AI 캐릭터와 대화

```http
POST /api/ai/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "character_name": "Victor Frankenstein",
  "message": "당신의 창조물에 대해 어떻게 생각하시나요?",
  "conversation_history": [],  // 선택사항
  "conversation_partner_type": "stranger",  // "stranger" 또는 "other_main_character"
  "other_main_character": null,  // conversation_partner_type이 "other_main_character"일 때 필수
  "output_language": "ko"  // "ko" 또는 "en"
}
```

**응답**:
```json
{
  "response": "아... 제 창조물이라니. 그것은 제 인생 최대의 실수였습니다...",
  "character_name": "Victor Frankenstein",
  "book_title": "Frankenstein; Or, The Modern Prometheus",
  "output_language": "ko"
}
```

**참고**:
- `conversation_id`는 UUID 형식으로 생성하거나 기존 ID를 사용
- 기본 캐릭터 대화는 임시 대화 저장 기능 지원 (최대 5턴 연속 대화)
- 시나리오 대화와 달리 최종 저장/취소 기능은 없음 (5턴 후 자동 만료)


## 🔀 What If 시나리오 API

### 1. 시나리오 생성

```http
POST /api/scenarios?creator_id={user_id}
Content-Type: application/json

{
  "scenario_name": "셜록홈즈가 현대사회에서 활동한다면?",
  "book_title": "The Adventures of Sherlock Holmes",
  "character_name": "Sherlock Holmes",
  "is_public": true,
  "character_property_changes": {
    "enabled": true,
    "description": "이성적이고 논리적인 추리를 중시하지만 사람의 감정 역시 추리에 중요한 요소라고 생각한다."
  },
  "event_alterations": {
    "enabled": false
  },
  "setting_modifications": {
    "enabled": true,
    "description": "2025년 한국 현대사회를 배경으로 최신 과학기술들을 사용한다."
  }
}
```

**응답**:
```json
{
  "scenario_id": "1a190443-5d3f-45e1-bc1d-cc192d46e76f",
  "scenario_name": "셜록홈즈가 현대사회에서 활동한다면?",
  "book_title": "The Adventures of Sherlock Holmes",
  "character_name": "Sherlock Holmes",
  "creator_id": "default_user",
  "is_public": true,
  "created_at": "2025-11-28T06:14:11.202282Z"
}
```

### 2. 시나리오 대화 (통합 엔드포인트)

시나리오 대화는 하나의 통합 엔드포인트로 처리됩니다:

```http
POST /api/scenarios/{scenario_id}/chat?creator_id={user_id}
Content-Type: application/json

{
  "message": "안녕하세요, 헤르미온이님!",
  "conversation_id": null,  // 첫 대화 시작 시 null, 이어서 대화 시 기존 ID
  "conversation_partner_type": "stranger",  // "stranger" 또는 "other_main_character"
  "other_main_character": null  // conversation_partner_type이 "other_main_character"일 때 필수
}
```

**동작 방식**:
- `action`이 없고 `conversation_id`가 없으면: 첫 대화 시작
- `action`이 없고 `conversation_id`가 있으면: 대화 이어가기 (최대 5턴)
- `action`이 있으면: 저장/취소 처리 (5턴 완료 후)

**첫 대화 시작 응답**:
```json
{
  "conversation_id": "conv_123",
  "scenario_id": "scenario_123",
  "response": "안녕하세요...",
  "turn_count": 1,
  "max_turns": 5,
  "is_temporary": true
}
```

**대화 이어가기 요청**:
```http
POST /scenario/{scenario_id}/chat?creator_id={user_id}
Content-Type: application/json

{
  "message": "슬리데린에 배정된 후 어떤 변화가 있었나요?",
  "conversation_id": "conv_123"
}
```

**대화 저장/취소 (5턴 완료 후)**:
```http
POST /scenario/{scenario_id}/chat?creator_id={user_id}
Content-Type: application/json

{
  "action": "save",  // 또는 "cancel"
  "conversation_id": "conv_123"
}
```

**저장 응답**:
```json
{
  "scenario_id": "scenario_123",
  "status": "saved",
  "first_conversation": {...},
  "message": "첫 대화가 시나리오에 저장되었습니다."
}
```

### 5. 공개 시나리오 목록 조회

```http
GET /api/scenarios?book_title=Pride and Prejudice&character_name=Elizabeth Bennet&sort=popular
```

**응답**:
```json
{
  "scenarios": [
    {
      "scenario_id": "scenario_123",
      "scenario_name": "헤르미온이가 슬리데린에 배정되었다면?",
      "book_title": "Pride and Prejudice",
      "character_name": "Elizabeth Bennet",
      "creator_id": "user_123",
      "fork_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### 6. 시나리오 상세 조회

```http
GET /api/scenarios/{id}
```

**응답**:
```json
{
  "scenario_id": "scenario_123",
  "scenario_name": "헤르미온이가 슬리데린에 배정되었다면?",
  "book_title": "Pride and Prejudice",
  "character_name": "Elizabeth Bennet",
  "character_property_changes": {...},
  "event_alterations": {...},
  "setting_modifications": {...},
  "first_conversation": [...],
  "can_fork": true
}
```

### 7. 시나리오 Fork

시나리오 Fork는 시나리오 복사만 처리하며, 대화는 별도 엔드포인트에서 시작합니다:

```http
POST /api/scenarios/{id}/fork
Content-Type: application/json

{
  "conversation_partner_type": "stranger",  // 필수: "stranger" 또는 "other_main_character"
  "other_main_character": null  // conversation_partner_type이 "other_main_character"일 때 필수
}
```

**응답**:
```json
{
  "id": "forked_scenario_456",
  "base_story": "The Adventures of Sherlock Holmes",
  "parent_scenario_id": "scenario_123",
  "scenario_type": "CHARACTER_CHANGE",
  "parameters": {...},
  "quality_score": 0.0,
  "creator_id": "user_123",
  "fork_count": 0,
  "created_at": "2025-11-28T06:14:11.202282Z"
}
```

**참고**: 
- `conversation_partner_type`이 원본과 같으면 기존 대화 맥락(`reference_first_conversation`) 저장
- `conversation_partner_type`이 원본과 다르면 What If 설정만 저장

### 8. Fork된 시나리오 대화 (통합 엔드포인트)

Fork된 시나리오 대화도 하나의 통합 엔드포인트로 처리됩니다:

```http
POST /api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat?user_id={user_id}
Content-Type: application/json

{
  "message": "안녕하세요!",
  "conversation_id": null  // 첫 대화 시작 시 null, 이어서 대화 시 기존 ID
}
```

**동작 방식**:
- `action`이 없고 `conversation_id`가 없으면: 첫 대화 시작
- `action`이 없고 `conversation_id`가 있으면: 대화 이어가기 (최대 5턴)
- `action`이 있으면: 저장/취소 처리 (5턴 완료 후)

**참고**: 
- `conversation_partner_type`과 `other_main_character`는 Fork 시 저장된 값을 자동으로 사용
- 요청에서 받지 않음

**대화 이어가기**:
```http
POST /api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat?user_id={user_id}
Content-Type: application/json

{
  "message": "다음 질문...",
  "conversation_id": "conv_456"
}
```

**대화 저장/취소 (5턴 완료 후)**:
```http
POST /api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat?user_id={user_id}
Content-Type: application/json

{
  "action": "save",  // 또는 "cancel"
  "conversation_id": "conv_456"
}
```

## 🏗️ 프로젝트 구조

```
rag-chatbot_test/
├── app/
│   ├── main.py                          # FastAPI 메인 애플리케이션
│   ├── config/
│   │   ├── settings.py                  # 환경 변수 설정 (Pydantic)
│   │   ├── celery_app.py                # Celery 설정
│   │   └── redis_client.py              # Redis 클라이언트 (태스크 상태)
│   ├── middleware/
│   │   └── correlation_id.py            # Correlation ID 미들웨어
│   ├── routers/
│   │   ├── character_chat.py            # 캐릭터 대화 API (/api/ai/*)
│   │   ├── scenario.py                  # What If 시나리오 API (/api/scenarios/*)
│   │   ├── novel_ingestion.py           # 소설 임베딩 API (/api/ai/novels/*)
│   │   ├── semantic_search.py           # 의미 검색 API (/api/ai/search/*)
│   │   ├── character_extraction.py      # 캐릭터 추출 API (/api/ai/characters/extract)
│   │   ├── tasks.py                     # 비동기 작업 상태 API (/api/tasks/*)
│   │   └── metrics.py                   # 메트릭 조회 API (/api/metrics)
│   ├── services/
│   │   ├── base_chat_service.py         # 기본 대화 서비스 (공통 API 호출 로직)
│   │   ├── character_data_loader.py     # 캐릭터 데이터 로더 (유틸리티)
│   │   ├── character_chat_service.py    # 캐릭터 대화 서비스
│   │   ├── scenario_management_service.py # 시나리오 관리 서비스
│   │   ├── scenario_chat_service.py     # 시나리오 대화 서비스
│   │   ├── character_extractor.py       # 캐릭터 추출 서비스 (chargraph 통합)
│   │   ├── api_key_manager.py           # API 키 관리
│   │   └── vectordb_client.py           # VectorDB 클라이언트 (ChromaDB)
│   ├── tasks/
│   │   ├── novel_ingestion.py           # 소설 임베딩 Celery 태스크
│   │   └── character_extraction.py      # 캐릭터 추출 Celery 태스크
│   └── utils/
│       ├── metrics.py                   # 메트릭 수집 유틸리티
│       └── redis_client.py              # Redis 클라이언트 (Long Polling)
├── scripts/
│   ├── collect_data.py                  # 책 검색 및 저장
│   ├── setup_file_search.py             # File Search Store 설정
│   ├── generate_character_personas.py   # 캐릭터 페르소나 자동 생성
│   ├── embed_novels_to_vectordb.py      # 소설 임베딩 스크립트
│   ├── check_vectordb.py                # VectorDB 데이터 확인
│   ├── convert_to_csv.py                # 데이터셋 → CSV 변환
│   ├── start_celery_worker.bat          # Celery 워커 시작 (Windows)
│   └── start_redis.bat                  # Redis 시작 (Windows)
├── data/
│   ├── origin_txt/                      # 원본 책 텍스트
│   ├── origin_dataset/                  # 다운로드된 데이터셋
│   ├── cache/                           # 메타데이터 캐시
│   ├── characters/                      # 책별 캐릭터 페르소나 (자동 생성)
│   ├── char_graph/                      # 인물 관계도 JSON 파일
│   ├── scenarios/                       # 시나리오 데이터 (public/private/forked)
│   ├── characters.json                  # 캐릭터 정보 (레거시)
│   └── file_search_store_info.json      # File Search Store 정보
├── chroma_data/                         # ChromaDB 데이터 저장소
├── requirements.txt                     # 패키지 목록
├── pytest.ini                           # Pytest 설정
├── docker-compose.yml                   # Docker Compose 설정
├── Dockerfile.dev                       # 개발용 Dockerfile
├── .env                                 # 환경 변수
└── README.md                            # 이 파일
```

## 🔧 기술 스택

### 백엔드
- **FastAPI**: 고성능 웹 프레임워크
- **Gemini 2.5 Flash**: Google의 최신 AI 모델
- **File Search**: Gemini의 RAG 기능 (자동 임베딩 + 벡터 검색)
- **Celery**: 비동기 작업 처리
- **Redis**: Celery 브로커 및 Long Polling 저장소
- **ChromaDB**: VectorDB (개발 환경)
- **Pinecone**: VectorDB (프로덕션 환경, 선택)

### 데이터
- **Gutenberg Project**: 고전 문학 작품 48,000+ 권
- **Hugging Face Datasets**: 효율적인 데이터 로딩
- **Pandas**: 메타데이터 관리

### 주요 라이브러리
- `google-genai`: Gemini 새 SDK
- `python-dotenv`: 환경 변수 관리
- `datasets`: Hugging Face 데이터셋
- `structlog`: 구조화된 로깅
- `pydantic-settings`: 환경 변수 타입 안전 관리
- `httpx`: 비동기 HTTP 클라이언트 (Spring Boot 통신용)
- `celery`: 비동기 작업 큐
- `redis`: 인메모리 데이터 저장소

## 📊 시스템 아키텍처

### 마이크로서비스 아키텍처 (MSA)

이 프로젝트는 **마이크로서비스 아키텍처**를 사용합니다:

- **Spring Boot (Port 8080)**: PostgreSQL ONLY (메타데이터, 사용자 데이터, 소셜 기능)
- **FastAPI (Port 8000)**: VectorDB ONLY (소설 콘텐츠, 임베딩, 의미 검색)

**통신 패턴**:
- **Pattern B (API Gateway)**: 프론트엔드는 Spring Boot만 호출, Spring Boot가 FastAPI로 프록시
- **Internal APIs**: 서비스 간 통신용 내부 API
  - Spring Boot → FastAPI: `/api/ai/*` (VectorDB 쿼리)
  - FastAPI → Spring Boot: `/api/internal/*` (PostgreSQL 메타데이터)

### AI 대화 시스템 (v2.0) - 현재
```
사용자 질문
    ↓
캐릭터 선택
    ↓
CharacterDataLoader → 캐릭터 정보 로드
    ↓
페르소나 프롬프트 생성
    ↓
BaseChatService → 공통 API 호출 로직
    ↓
Gemini File Search
  ├─ 자동 임베딩
  ├─ 벡터 검색
  └─ 관련 문서 추출
    ↓
캐릭터 페르소나 적용
    ↓
몰입감 있는 답변 생성
    ↓
인용 정보 포함
```

### 서비스 계층 구조 (v2.1 - 최적화 완료)
```
BaseChatService (공통 로직)
  ├─ API 키 관리
  ├─ Store 정보 관리
  ├─ API 호출 (재시도 로직)
  └─ _call_gemini_api(), _extract_response()

CharacterDataLoader (유틸리티)
  ├─ load_characters() - 캐릭터 정보 로드
  ├─ get_character_info() - 캐릭터 정보 조회
  └─ get_available_characters() - 캐릭터 목록 반환

CharacterChatService (BaseChatService 상속)
  ├─ CharacterDataLoader 사용
  ├─ 기본 페르소나 프롬프트 생성
  └─ chat()

ScenarioChatService (BaseChatService 상속)
  ├─ CharacterDataLoader 직접 사용
  ├─ 시나리오 프롬프트 생성
  ├─ 대화 저장/관리
  └─ first_conversation(), chat_with_scenario()
```

**최적화 효과:**
- ✅ API 호출 로직 중복 제거
- ✅ 불필요한 의존성 제거 (CharacterChatService 인스턴스 불필요)
- ✅ 메모리 효율 향상 (캐릭터 데이터만 로드)
- ✅ 코드 재사용성 향상

## 🎯 주요 기능

### 1. 품질 기반 책 선택
- 4가지 기준으로 최적 버전 자동 선택
  - 텍스트 길이 (40점)
  - Gutenberg ID (30점)
  - 구조적 완성도 (20점)
  - 텍스트 품질 (10점)

### 2. 페르소나 시스템
- 각 캐릭터의 성격, 말투, 가치관 반영
- 책의 내용과 맥락 기반 응답
- 자연스럽고 몰입감 있는 대화

### 3. API 키 로테이션
- 여러 API 키 자동 전환
- 할당량 초과 시 자동 재시도
- 실패한 키 일정 시간 후 재활성화

### 4. What If 시나리오 시스템
- **시나리오 생성**: 캐릭터 속성, 사건, 배경 변경을 통한 대체 타임라인 생성
- **통합 대화 API**: 하나의 엔드포인트로 첫 대화, 이어가기, 저장/취소 처리
- **시나리오 Fork**: 다른 사용자의 시나리오를 기반으로 새로운 대화 시작
  - Fork 시 `conversation_partner_type` 선택 필수
  - 원본과 같은 `conversation_partner_type`이면 기존 대화 맥락 저장
  - 원본과 다른 `conversation_partner_type`이면 What If 설정만 저장
- **공개 시나리오**: 커뮤니티와 시나리오 공유 및 탐색
- **대화 상대 선택**: 제3의 인물 또는 같은 책의 다른 주인공과 대화 선택 가능
  - **제3의 인물 (stranger)**: 캐릭터가 처음 보는 완전한 낯선 사람으로 인식
  - **다른 주인공 (other_main_character)**: 같은 책의 다른 주인공으로 인식 (예: Romeo 선택 시 Juliet과 대화)
  - 원본 시나리오: 대화 시작 시 선택 가능
  - Fork된 시나리오: Fork 시 선택하며, 대화 중에는 변경 불가

### 5. 서비스 아키텍처 최적화
- **BaseChatService**: 공통 API 호출 로직을 상속으로 재사용
- **CharacterDataLoader**: 캐릭터 정보 로드 로직을 유틸리티로 분리
- **의존성 최소화**: 각 서비스가 필요한 기능만 사용
- **코드 중복 제거**: 유지보수 용이성 향상

## 📚 추가 문서

- [마이그레이션 가이드](MIGRATION_GUIDE.md) - v1.0 → v2.0 전환
- [텍스트 품질 분석](TEXT_QUALITY_ANALYSIS.md) - 책 선택 알고리즘
- [API 키 설정](API_KEY_SETUP_SUMMARY.md) - API 키 관리
- [변경 이력](CHANGELOG.md) - 버전별 변경사항

## 💡 사용 예시

### Python 클라이언트 - 캐릭터 대화

```python
import requests

# 캐릭터 목록 조회
response = requests.get("http://localhost:8000/api/ai/characters")
characters = response.json()['characters']
print(f"사용 가능한 캐릭터: {len(characters)}명")

# Victor Frankenstein과 대화
import uuid
conversation_id = str(uuid.uuid4())  # 새 대화 ID 생성

chat_request = {
    "character_name": "Victor Frankenstein",
    "message": "당신의 실험에 대해 말씀해주세요.",
    "conversation_history": [],
    "output_language": "ko"
}

response = requests.post(
    f"http://localhost:8000/api/ai/conversations/{conversation_id}/messages",
    json=chat_request
)

result = response.json()
print(f"\n{result['character_name']}: {result['response']}")
```

### Python 클라이언트 - What If 시나리오

```python
import requests

# 1. 시나리오 생성
scenario_request = {
    "scenario_name": "셜록홈즈가 현대사회에서 활동한다면?",
    "book_title": "The Adventures of Sherlock Holmes",
    "character_name": "Sherlock Holmes",
    "is_public": True,
    "character_property_changes": {
        "enabled": True,
        "description": "이성적이고 논리적인 추리를 중시하지만 사람의 감정 역시 추리에 중요한 요소라고 생각한다."
    },
    "event_alterations": {
        "enabled": False
    },
    "setting_modifications": {
        "enabled": True,
        "description": "2025년 한국 현대사회를 배경으로 최신 과학기술들을 사용한다."
    }
}

response = requests.post(
    "http://localhost:8000/api/scenarios?creator_id=default_user",
    json=scenario_request
)
scenario = response.json()
scenario_id = scenario['scenario_id']
print(f"시나리오 생성: {scenario_id}")

# 2. 첫 대화 시작 (다른 주인공과 대화)
conversation_request = {
    "message": "안녕하세요? 제가 누군지 아시나요?",
    "conversation_id": None,
    "conversation_partner_type": "other_main_character",
    "other_main_character": {
        "character_name": "Dr. Watson",
        "book_title": "The Adventures of Sherlock Holmes"
    }
}

response = requests.post(
    f"http://localhost:8000/api/scenarios/{scenario_id}/chat?creator_id=default_user",
    json=conversation_request
)
result = response.json()
print(f"응답: {result['response']}")
print(f"턴: {result['turn_count']}/{result['max_turns']}")
conversation_id = result['conversation_id']

# 3. 대화 계속 (턴 2~5)
continue_request = {
    "message": "농담이었어, 셜록. 최근 해결한 사건 중에 내가 기록할만한 흥미로운 사건이 있을까?",
    "conversation_id": conversation_id
}

response = requests.post(
    f"http://localhost:8000/api/scenarios/{scenario_id}/chat?creator_id=default_user",
    json=continue_request
)
result = response.json()
print(f"응답: {result['response']}")
print(f"턴: {result['turn_count']}/{result['max_turns']}")

# ... (턴 3, 4, 5 계속)

# 4. 대화 저장 (5턴 완료 후)
confirm_request = {
    "action": "save",
    "conversation_id": conversation_id
}

response = requests.post(
    f"http://localhost:8000/api/scenarios/{scenario_id}/chat?creator_id=default_user",
    json=confirm_request
)
print(response.json()['message'])

# 5. 공개 시나리오 조회
response = requests.get(
    "http://localhost:8000/api/scenarios",
    params={"sort": "popular"}
)
scenarios = response.json()['scenarios']
print(f"\n공개 시나리오: {len(scenarios)}개")

# 6. 시나리오 Fork (원본과 같은 대화 상대 선택)
fork_request = {
    "conversation_partner_type": "other_main_character",
    "other_main_character": {
        "character_name": "Dr. Watson",
        "book_title": "The Adventures of Sherlock Holmes"
    }
}

response = requests.post(
    f"http://localhost:8000/api/scenarios/{scenarios[0]['scenario_id']}/fork",
    json=fork_request
)
forked = response.json()
forked_scenario_id = forked['id']
print(f"Fork된 시나리오 ID: {forked_scenario_id}")

# 7. Fork된 시나리오 대화 시작 (conversation_partner_type은 Fork 시 저장된 값 사용)
forked_chat_request = {
    "message": "안녕하세요? 제가 누군지 아시나요?"
}

response = requests.post(
    f"http://localhost:8000/api/scenarios/{scenarios[0]['scenario_id']}/fork/{forked_scenario_id}/chat?user_id=default_user",
    json=forked_chat_request
)
result = response.json()
print(f"응답: {result['response']}")
print(f"턴: {result['turn_count']}/{result['max_turns']}")
```

### cURL

```bash
# 캐릭터 목록
curl http://localhost:8000/api/ai/characters

# 캐릭터 정보 조회
curl http://localhost:8000/api/ai/characters/info/Victor%20Frankenstein?book_title=Frankenstein

# 캐릭터 대화
curl -X POST http://localhost:8000/api/ai/conversations/{conversation_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "Elizabeth Bennet",
    "message": "안녕하세요!",
    "conversation_history": [],
    "output_language": "ko"
  }'

# 시나리오 생성
curl -X POST "http://localhost:8000/api/scenarios?creator_id=default_user" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "셜록홈즈가 현대사회에서 활동한다면?",
    "book_title": "The Adventures of Sherlock Holmes",
    "character_name": "Sherlock Holmes",
    "is_public": true,
    "character_property_changes": {
      "enabled": true,
      "description": "이성적이고 논리적인 추리를 중시하지만 사람의 감정 역시 추리에 중요한 요소라고 생각한다."
    },
    "event_alterations": {
      "enabled": false
    },
    "setting_modifications": {
      "enabled": true,
      "description": "2025년 한국 현대사회를 배경으로 최신 과학기술들을 사용한다."
    }
  }'

# 시나리오 대화 시작
curl -X POST "http://localhost:8000/api/scenarios/{scenario_id}/chat?creator_id=default_user" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요? 제가 누군지 아시나요?",
    "conversation_partner_type": "other_main_character",
    "other_main_character": {
      "character_name": "Dr. Watson",
      "book_title": "The Adventures of Sherlock Holmes"
    }
  }'

# 공개 시나리오 목록
curl "http://localhost:8000/api/scenarios?sort=popular"

# 시나리오 상세 조회
curl "http://localhost:8000/api/scenarios/{id}"

# 시나리오 Fork
curl -X POST "http://localhost:8000/api/scenarios/{id}/fork" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_partner_type": "stranger"
  }'

# Fork된 시나리오 대화
curl -X POST "http://localhost:8000/api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat?user_id=default_user" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요!"
  }'

# 헬스 체크
curl http://localhost:8000/health

# 메트릭 조회
curl http://localhost:8000/api/metrics

# 작업 상태 조회
curl http://localhost:8000/api/tasks/{task_id}/status
```

## 🔐 보안 및 제한사항

### API 제한
- **File Search Store 크기**:
  - Free tier: 1GB
  - 현재 사용량: ~30MB (55개 책)
- **파일 크기**: 최대 100MB per file
- **Rate Limit**: API 키별 할당량 적용

### 권장사항
- 프로덕션 환경에서는 CORS 설정 제한
- API 키는 환경 변수로 관리
- 대화 기록은 최근 5개만 유지

## 🐛 문제 해결

### File Search Store 정보를 찾을 수 없습니다
```bash
# 해결: File Search Store 설정 실행
py scripts/setup_file_search.py
```

### API 할당량 초과
- 여러 API 키 설정 (`.env`의 `GEMINI_API_KEYS`)
- 자동 로테이션 활성화됨

### 캐릭터를 찾을 수 없습니다
- `data/characters/` 폴더의 JSON 파일 확인 (새 구조)
- 또는 `data/characters.json` 파일 확인 (레거시)
- 캐릭터 이름 정확히 입력

## 🎭 캐릭터 페르소나 자동 생성

### 개요

`scripts/generate_character_personas.py` 스크립트는 File Search를 활용하여 원본 텍스트와 인물 관계도를 분석하고, 각 책의 주요 캐릭터(id 1, 2)의 페르소나와 말투를 자동으로 생성합니다.

### 특징

- **File Search 기반 분석**: 원본 텍스트에서 실제 대사와 행동 패턴 추출
- **인물 관계도 활용**: char_graph의 관계 정보를 반영한 페르소나 생성
- **이중 언어 생성**: 영어와 한국어로 각각 생성하여 번역 손실 방지
- **책별 저장**: `data/characters/` 폴더에 책별로 JSON 파일 저장

### 사용 방법

```bash
# 모든 책의 캐릭터 페르소나 생성
py scripts/generate_character_personas.py
```

### 생성 프로세스

1. **데이터 수집**
   - `saved_books_info.json`에서 책 목록 로드
   - 각 책의 `char_graph` JSON에서 id 1, 2 캐릭터 추출

2. **원본 텍스트 분석** (File Search 사용)
   - 캐릭터의 주요 대사 샘플 추출
   - 주요 사건/장면 요약
   - 행동 패턴 및 결정 분석
   - 다른 인물의 평가 수집

3. **페르소나 생성**
   - 영어 페르소나 생성
   - 한국어 페르소나 생성

4. **말투 생성**
   - 영어 말투 생성
   - 한국어 말투 생성 (한국어 특유의 표현, 어미, 존댓말/반말 수준 등 구체적으로 명시)

5. **결과 저장**
   - `data/characters/[책제목].json` 형식으로 저장

### 출력 파일 구조

```
data/characters/
├── Frankenstein; Or, The Modern Prometheus.json
├── Pride and Prejudice.json
├── The Great Gatsby.json
├── Romeo and Juliet.json
├── The Adventures of Tom Sawyer, Complete.json
└── The Adventures of Sherlock Holmes.json
```

### 한국어 말투 생성의 중요성

한국어로 번역할 때 말투의 본질을 유지하기 위해, 원본 텍스트의 대사 패턴을 분석하여 한국어로 말할 때의 말투를 직접 생성합니다. 이를 통해:

- 번역 과정에서 손실되는 뉘앙스 방지
- 한국어 특유의 표현, 어미, 존댓말/반말 수준을 구체적으로 명시
- 캐릭터의 성격과 일치하는 자연스러운 한국어 말투 구현

## 📈 향후 계획

### 완료된 기능 ✅
- [x] 캐릭터 페르소나 자동 생성 (File Search 기반)
- [x] 서비스 아키텍처 최적화 (BaseChatService, CharacterDataLoader)
- [x] 대화 상대 선택 기능 (제3의 인물 / 다른 주인공)
- [x] API 경로 표준화 (`/api/ai/*`, `/api/scenarios/*`)
- [x] 비동기 작업 처리 (Celery + Redis)
- [x] 캐릭터 추출 기능 (chargraph 통합)
- [x] 메트릭 수집 및 헬스 체크

### Spring Boot 통신 통합 (TODO) 🔧

#### Phase 1: 기본 통신 (필수)
- [ ] **Spring Boot Internal API 클라이언트 구현**
  - `httpx.AsyncClient`를 사용한 Spring Boot `/api/internal/*` 호출
  - Internal API 인증 토큰 처리
  - 재시도 로직 및 에러 처리
  
- [ ] **인증/인가 미들웨어 추가**
  - JWT 토큰 검증 미들웨어
  - Spring Boot에서 전달받은 토큰 검증
  - 사용자 정보 추출 및 의존성 주입
  
- [ ] **시나리오 CRUD를 Spring Boot로 위임**
  - 시나리오 생성/조회/수정/삭제를 Spring Boot API로 호출
  - FastAPI는 AI 대화 기능만 담당

#### Phase 2: 데이터 동기화 (필수)
- [ ] **시나리오 메타데이터를 PostgreSQL로 이동**
  - 현재 파일 시스템 저장 → PostgreSQL 저장으로 전환
  - Spring Boot의 시나리오 관리 API 활용
  
- [ ] **FastAPI는 VectorDB만 관리**
  - 소설 임베딩, 캐릭터 추출, 의미 검색만 담당
  - 메타데이터는 Spring Boot에서 관리
  
- [ ] **Spring Boot ↔ FastAPI 간 데이터 동기화 로직**
  - 소설 임베딩 시 Spring Boot에 메타데이터 저장
  - 캐릭터 추출 시 Spring Boot에 캐릭터 정보 저장

#### Phase 3: 개선 (권장)
- [ ] **응답 형식 표준화**
  - 공통 응답 래퍼 클래스 구현
  - 에러 응답 형식 통일
  - API 문서와 일치하는 응답 형식
  
- [ ] **에러 처리 개선**
  - 표준화된 에러 코드
  - 상세한 에러 메시지
  - 로깅 강화
  
- [ ] **로깅 및 모니터링 강화**
  - Correlation ID 추적
  - 성능 메트릭 수집
  - 분산 추적 시스템 통합

### 기능 확장 (선택)
- [ ] 더 많은 캐릭터 추가
- [ ] 음성 대화 기능
- [ ] 감정 분석 및 반영
- [ ] 프론트엔드 웹 인터페이스
- [ ] 대화 기록 저장 및 분석

## 🤝 기여

이 프로젝트는 SSAFY 프로젝트의 일부입니다.

## 📄 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**Made with ❤️ by Gaji Team**
