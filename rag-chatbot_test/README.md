# Gaji AI Backend - Character Chat & What If Scenarios

**책 속 인물과 대화하고 "What If" 시나리오를 탐험하는 AI 챗봇** (Gemini File Search 기반)

## 🎭 프로젝트 소개

이 프로젝트는 Gemini의 File Search 기능을 활용하여 사용자가 책 속 등장인물과 몰입감 있는 대화를 나눌 수 있는 AI 챗봇 서비스입니다. 또한 "What If" 시나리오를 생성하여 캐릭터의 속성, 사건, 배경을 변경한 대체 타임라인을 탐험할 수 있습니다.

### 주요 특징

- 📚 **원본 텍스트 기반**: 구텐베르크 프로젝트의 고전 문학 작품 활용
- 🎭 **페르소나 시스템**: 각 캐릭터의 성격, 말투, 가치관을 반영한 대화
- 🔀 **What If 시나리오**: 캐릭터 속성, 사건, 배경 변경을 통한 대체 타임라인 생성
- 🔍 **자동 인용**: Gemini File Search가 원문 출처를 자동으로 제공
- 💬 **스트리밍 응답**: 실시간 대화 경험
- 🔑 **API 키 로테이션**: 여러 API 키 자동 전환으로 안정적인 서비스

## 🎬 사용 가능한 캐릭터

| 캐릭터              | 책                                | 저자                |
| ------------------- | --------------------------------- | ------------------- |
| Victor Frankenstein | Frankenstein                      | Mary Shelley        |
| Elizabeth Bennet    | Pride and Prejudice               | Jane Austen         |
| Jay Gatsby          | The Great Gatsby                  | F. Scott Fitzgerald |
| Romeo Montague      | Romeo and Juliet                  | William Shakespeare |
| Tom Sawyer          | The Adventures of Tom Sawyer      | Mark Twain          |
| Sherlock Holmes     | The Adventures of Sherlock Holmes | Arthur Conan Doyle  |

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

### 4. 테스트

```bash
# 터미널에서 캐릭터와 대화
py test_character_chat.py
```

### 5. API 서버 실행

### 5. API 서버 실행

```bash
# FastAPI 서버 시작
uvicorn app.main:app --reload
```

서버 실행 후: http://localhost:8000/docs

## 📡 API 사용법

### 1. 캐릭터 목록 조회

```http
GET /character/list
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

### 2. 캐릭터와 대화

```http
POST /character/chat
Content-Type: application/json

{
  "character_name": "Victor Frankenstein",
  "message": "당신의 창조물에 대해 어떻게 생각하시나요?",
  "conversation_history": []
}
```

**응답**:

```json
{
  "response": "아... 제 창조물이라니. 그것은 제 인생 최대의 실수였습니다...",
  "character_name": "Victor Frankenstein",
  "book_title": "Frankenstein; Or, The Modern Prometheus",
  "grounding_metadata": {
    "citations": [...]
  }
}
```

### 3. 스트리밍 대화

```http
POST /character/chat/stream
Content-Type: application/json

{
  "character_name": "Elizabeth Bennet",
  "message": "다아시 씨에 대한 첫인상은 어떠셨나요?"
}
```

**응답** (Server-Sent Events):

```
data: {"chunk": "처음에는", "character_name": "Elizabeth Bennet"}
data: {"chunk": " 그분을", "character_name": "Elizabeth Bennet"}
...
data: [DONE]
```

## 🔀 What If 시나리오 API

### 1. 시나리오 생성

```http
POST /scenario/create
Content-Type: application/json

{
  "scenario_name": "헤르미온이가 슬리데린에 배정되었다면?",
  "book_title": "Pride and Prejudice",
  "character_name": "Elizabeth Bennet",
  "is_private": false,
  "character_property_changes": {
    "enabled": true,
    "description": "그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해짐"
  },
  "event_alterations": {
    "enabled": false
  },
  "setting_modifications": {
    "enabled": false
  }
}
```

**응답**:

```json
{
  "scenario_id": "scenario_123",
  "scenario_name": "헤르미온이가 슬리데린에 배정되었다면?",
  "book_title": "Pride and Prejudice",
  "character_name": "Elizabeth Bennet",
  "creator_id": "default_user",
  "is_private": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. 첫 대화 시작 (원본 시나리오)

```http
POST /scenario/{scenario_id}/first-conversation
Content-Type: application/json

{
  "initial_message": "안녕하세요, 헤르미온이님!",
  "conversation_id": null
}
```

**응답**:

```json
{
  "response": "안녕하세요...",
  "conversation_id": "conv_123",
  "turn_count": 1,
  "max_turns": 5,
  "is_regenerable": true,
  "is_saved": false
}
```

### 3. 첫 대화 계속 (턴 2~5)

```http
POST /scenario/{scenario_id}/first-conversation/continue
Content-Type: application/json

{
  "conversation_id": "conv_123",
  "message": "슬리데린에 배정된 후 어떤 변화가 있었나요?"
}
```

### 4. 첫 대화 최종 컨펌 (5턴 완료 후)

```http
POST /scenario/{scenario_id}/first-conversation/confirm
Content-Type: application/json

{
  "conversation_id": "conv_123",
  "action": "save"  // 또는 "cancel"
}
```

**응답**:

```json
{
  "success": true,
  "message": "대화가 시나리오에 저장되었습니다.",
  "scenario_id": "scenario_123"
}
```

### 5. 공개 시나리오 목록 조회

```http
GET /scenario/public?book_title=Pride and Prejudice&character_name=Elizabeth Bennet&sort=popular
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
GET /scenario/{scenario_id}
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

```http
POST /scenario/{scenario_id}/fork
Content-Type: application/json

{
  "initial_message": "안녕하세요!"
}
```

**응답**:

```json
{
  "forked_scenario_id": "forked_scenario_456",
  "original_scenario_id": "scenario_123",
  "response": "안녕하세요...",
  "conversation_id": "conv_456",
  "turn_count": 1,
  "max_turns": 5,
  "is_temporary": true
}
```

### 8. Fork된 시나리오 대화 계속

```http
POST /scenario/{scenario_id}/fork/{forked_scenario_id}/continue
Content-Type: application/json

{
  "conversation_id": "conv_456",
  "message": "다음 질문..."
}
```

### 9. Fork된 시나리오 대화 컨펌

```http
POST /scenario/{scenario_id}/fork/{forked_scenario_id}/confirm-conversation
Content-Type: application/json

{
  "conversation_id": "conv_456",
  "action": "save"  // 또는 "cancel"
}
```

## 🏗️ 프로젝트 구조

```
rag-chatbot_test/
rag-chatbot_test/
├── app/
│   ├── main.py                          # FastAPI 메인
│   ├── routers/
│   │   ├── character_chat.py            # 캐릭터 대화 API
│   │   ├── scenario.py                   # What If 시나리오 API
│   │   └── chat.py                      # 레거시 RAG API
│   └── services/
│       ├── character_chat_service.py    # 캐릭터 대화 서비스
│       ├── scenario_management_service.py # 시나리오 관리 서비스
│       ├── scenario_chat_service.py     # 시나리오 대화 서비스
│       ├── api_key_manager.py           # API 키 관리
│       ├── rag_service.py               # 레거시 RAG 서비스
│       └── question_classifier.py       # 질문 분류기
├── scripts/
│   ├── collect_data.py                  # 책 검색 및 저장
│   ├── setup_file_search.py             # File Search Store 설정
│   ├── download_dataset.py              # 데이터셋 다운로드
│   ├── preprocess_text.py               # 텍스트 전처리 (레거시)
│   └── import_to_chromadb.py            # ChromaDB 임포트 (레거시)
├── gradio_test/
│   ├── app.py                           # Gradio UI (What If 시나리오 테스트)
│   └── requirements.txt                 # Gradio 의존성
├── data/
│   ├── origin_txt/                      # 원본 책 텍스트
│   ├── origin_dataset/                  # 다운로드된 데이터셋
│   ├── cache/                           # 메타데이터 캐시
│   ├── characters.json                  # 캐릭터 정보
│   └── file_search_store_info.json      # File Search Store 정보
├── convert_to_csv.py                    # 데이터셋 → CSV 변환
├── test_character_chat.py               # 터미널 테스트
├── requirements.txt                     # 패키지 목록
├── .env                                 # 환경 변수
└── README.md                            # 이 파일
```

## 🔧 기술 스택

### 백엔드

- **FastAPI**: 고성능 웹 프레임워크
- **Gemini 2.0 Flash**: Google의 최신 AI 모델
- **File Search**: Gemini의 RAG 기능 (자동 임베딩 + 벡터 검색)

### 데이터

- **Gutenberg Project**: 고전 문학 작품 48,000+ 권
- **Hugging Face Datasets**: 효율적인 데이터 로딩
- **Pandas**: 메타데이터 관리

### 주요 라이브러리

- `google-genai`: Gemini 새 SDK
- `python-dotenv`: 환경 변수 관리
- `datasets`: Hugging Face 데이터셋

## 📊 시스템 아키텍처

### 기존 시스템 (v1.0) - 레거시

```
사용자 질문
    ↓
텍스트 전처리
    ↓
로컬 임베딩 생성 (Gemini)
    ↓
ChromaDB 벡터 검색
    ↓
관련 문서 추출
    ↓
Gemini로 답변 생성
```

### 새로운 시스템 (v2.0) - 현재

```
사용자 질문
    ↓
캐릭터 선택
    ↓
페르소나 프롬프트 생성
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

### 4. 스트리밍 응답

- 실시간 대화 경험
- Server-Sent Events (SSE)
- 낮은 지연시간

### 5. What If 시나리오 시스템

- **시나리오 생성**: 캐릭터 속성, 사건, 배경 변경을 통한 대체 타임라인 생성
- **첫 대화**: 시나리오에 맞춘 캐릭터와의 대화 (최대 5턴)
- **시나리오 Fork**: 다른 사용자의 시나리오를 기반으로 새로운 대화 시작
- **공개 시나리오**: 커뮤니티와 시나리오 공유 및 탐색

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
response = requests.get("http://localhost:8000/character/list")
characters = response.json()['characters']
print(f"사용 가능한 캐릭터: {len(characters)}명")

# Victor Frankenstein과 대화
chat_request = {
    "character_name": "Victor Frankenstein",
    "message": "당신의 실험에 대해 말씀해주세요.",
    "conversation_history": []
}

response = requests.post(
    "http://localhost:8000/character/chat",
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
    "scenario_name": "헤르미온이가 슬리데린에 배정되었다면?",
    "book_title": "Pride and Prejudice",
    "character_name": "Elizabeth Bennet",
    "is_private": False,
    "character_property_changes": {
        "enabled": True,
        "description": "그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해짐"
    }
}

response = requests.post(
    "http://localhost:8000/scenario/create",
    json=scenario_request
)
scenario = response.json()
scenario_id = scenario['scenario_id']
print(f"시나리오 생성: {scenario_id}")

# 2. 첫 대화 시작
conversation_request = {
    "initial_message": "안녕하세요!",
    "conversation_id": None
}

response = requests.post(
    f"http://localhost:8000/scenario/{scenario_id}/first-conversation",
    json=conversation_request
)
result = response.json()
print(f"응답: {result['response']}")
print(f"턴: {result['turn_count']}/{result['max_turns']}")

# 3. 대화 계속 (턴 2~5)
continue_request = {
    "conversation_id": result['conversation_id'],
    "message": "슬리데린에 배정된 후 어떤 변화가 있었나요?"
}

response = requests.post(
    f"http://localhost:8000/scenario/{scenario_id}/first-conversation/continue",
    json=continue_request
)
result = response.json()
print(f"응답: {result['response']}")

# 4. 대화 저장 (5턴 완료 후)
confirm_request = {
    "conversation_id": result['conversation_id'],
    "action": "save"
}

response = requests.post(
    f"http://localhost:8000/scenario/{scenario_id}/first-conversation/confirm",
    json=confirm_request
)
print(response.json()['message'])

# 5. 공개 시나리오 조회
response = requests.get(
    "http://localhost:8000/scenario/public",
    params={"sort": "popular"}
)
scenarios = response.json()['scenarios']
print(f"\n공개 시나리오: {len(scenarios)}개")

# 6. 시나리오 Fork
fork_request = {
    "initial_message": "안녕하세요!"
}

response = requests.post(
    f"http://localhost:8000/scenario/{scenarios[0]['scenario_id']}/fork",
    json=fork_request
)
forked = response.json()
print(f"Fork된 시나리오 ID: {forked['forked_scenario_id']}")
```

### cURL

```bash
# 캐릭터 목록
curl http://localhost:8000/character/list

# 캐릭터 대화
curl -X POST http://localhost:8000/character/chat \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "Elizabeth Bennet",
    "message": "안녕하세요!",
    "conversation_history": []
  }'

# 시나리오 생성
curl -X POST http://localhost:8000/scenario/create \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "헤르미온이가 슬리데린에 배정되었다면?",
    "book_title": "Pride and Prejudice",
    "character_name": "Elizabeth Bennet",
    "is_private": false,
    "character_property_changes": {
      "enabled": true,
      "description": "그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해짐"
    }
  }'

# 공개 시나리오 목록
curl "http://localhost:8000/scenario/public?sort=popular"

# 시나리오 Fork
curl -X POST http://localhost:8000/scenario/{scenario_id}/fork \
  -H "Content-Type: application/json" \
  -d '{
    "initial_message": "안녕하세요!"
  }'
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

- `data/characters.json` 파일 확인
- 캐릭터 이름 정확히 입력

## 📈 향후 계획

- [ ] 더 많은 캐릭터 추가
- [ ] 다국어 지원
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
