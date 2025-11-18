# RAG 기반 "What If" 챗봇 샘플 코드

Gaji 프로젝트의 RAG 기반 챗봇 대화 시스템을 위한 샘플 코드입니다.

---

## 📋 개요

이 샘플 코드는 다음 단계로 구성됩니다:

1. **데이터 수집**: Gutenberg 책 텍스트 수집
2. **전처리**: 텍스트 정제 및 청킹
3. **임베딩 생성**: Gemini Embedding API로 벡터 생성
4. **벡터 DB 저장**: ChromaDB에 저장
5. **RAG 서비스**: 검색 및 프롬프트 생성
6. **API 서버**: FastAPI로 챗봇 엔드포인트 제공

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
# Windows CMD:
set GEMINI_API_KEY=your_api_key_here

# Windows PowerShell:
$env:GEMINI_API_KEY="your_api_key_here"

# Linux/Mac:
export GEMINI_API_KEY=your_api_key_here

# 또는 .env 파일 생성 (python-dotenv 사용 시)
# GEMINI_API_KEY=your_api_key_here
# CHROMA_PATH=./chroma_data
# CHROMA_COLLECTION=novel_passages
```

### 2. 데이터 수집 (방법 1: datasets - 추천)

```bash
# Pride and Prejudice 수집
python scripts/collect_data.py \
    --method datasets \
    --titles "Pride and Prejudice" \
    --output data/raw
```

### 3. 텍스트 전처리 및 청킹

```bash
python scripts/preprocess_text.py \
    --input data/raw \
    --output data/processed \
    --chunk-size 400
```

### 4. 임베딩 생성

```bash
python scripts/generate_embeddings.py \
    --input data/processed \
    --output data/embeddings \
    --api-key $GEMINI_API_KEY
```

### 5. ChromaDB 임포트

```bash
python scripts/import_to_chromadb.py \
    --input data/embeddings \
    --collection novel_passages \
    --chroma-path ./chroma_data \
    --verify
```

### 6. API 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. 테스트

```bash
# 검색 테스트
curl "http://localhost:8000/api/ai/search/passages?query=Elizabeth%20Bennet&top_k=3"

# 챗봇 대화 테스트
curl -X POST "http://localhost:8000/api/ai/conversations/test-123/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is your opinion on marriage?",
    "scenario_context": "You are Elizabeth Bennet in an alternate timeline where you never met Mr. Darcy.",
    "book_id": "novel_pride_and_prejudice"
  }'
```

---

## 📁 프로젝트 구조

```
.
├── app/
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── routers/
│   │   └── chat.py              # 챗봇 API 엔드포인트
│   └── services/
│       └── rag_service.py       # RAG 서비스 (검색 + 생성)
├── scripts/
│   ├── collect_data.py          # 데이터 수집
│   ├── preprocess_text.py       # 전처리 및 청킹
│   ├── generate_embeddings.py  # 임베딩 생성
│   └── import_to_chromadb.py    # ChromaDB 임포트
├── data/
│   ├── raw/                     # 원본 텍스트
│   ├── processed/               # 청킹된 텍스트
│   └── embeddings/              # 임베딩 벡터
├── chroma_data/                 # ChromaDB 데이터
├── requirements.txt
└── README.md
```

---

## 🔧 주요 기능

### 1. 데이터 수집

두 가지 방법 지원:
- **datasets** (추천): 빠른 시작, 이미 정제된 데이터
- **gutenbergpy**: 특정 책 선택 가능

### 2. RAG 서비스

- **Semantic Search**: 사용자 질문과 관련된 청크 검색
- **Prompt Generation**: 검색된 청크 + 시나리오 컨텍스트로 프롬프트 생성
- **Response Generation**: Gemini 2.5 Flash로 응답 생성

### 3. API 엔드포인트

- `POST /api/ai/conversations/{id}/messages`: 일반 응답
- `POST /api/ai/conversations/{id}/messages/stream`: 스트리밍 응답 (SSE)
- `GET /api/ai/search/passages`: 청크 검색 (디버깅용)

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

## 🐛 문제 해결

### 1. datasets 로드 실패

```bash
# 캐시 삭제 후 재시도
rm -rf ~/.cache/huggingface/datasets
```

### 2. ChromaDB 연결 오류

```bash
# ChromaDB 데이터 디렉토리 권한 확인
chmod -R 755 ./chroma_data
```

### 3. Gemini API 키 오류

```bash
# 환경변수 확인
echo $GEMINI_API_KEY

# .env 파일 확인
cat .env
```

---

## 🔄 다음 단계

1. **더 많은 책 추가**: 여러 책으로 확장
2. **캐릭터 추출**: LLM으로 캐릭터 정보 자동 추출
3. **이벤트 추출**: 주요 이벤트 추출 및 저장
4. **프롬프트 최적화**: 시나리오별 프롬프트 템플릿 개선
5. **성능 최적화**: 배치 처리, 캐싱 등

---

## 📚 참고 자료

- [Gaji 프로젝트 문서](../docs/RAG_CHATBOT_PLAN.md)
- [Gemini API 문서](https://ai.google.dev/docs)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)

---

**작성일**: 2025-01-XX  
**버전**: 0.1.0

