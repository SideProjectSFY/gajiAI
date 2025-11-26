# 🚀 서비스 실행 가이드

## 사전 준비사항 확인

### 1. 필수 파일 확인
다음 파일들이 존재하는지 확인하세요:
- ✅ `.env` 파일 (API 키 설정)
- ✅ `data/file_search_store_info.json` (File Search Store 정보)
- ✅ `data/characters.json` 또는 `data/characters/` 폴더 (캐릭터 정보)
- ✅ `data/origin_txt/` 폴더에 책 텍스트 파일들
- ✅ `data/char_graph/` 폴더에 인물 관계도 JSON 파일들

### 2. 패키지 설치 확인
```bash
pip install -r requirements.txt
```

## 서비스 실행 단계

### 1단계: API 키 설정 확인

`.env` 파일이 있는지 확인하고, 없다면 생성하세요:

```bash
# Windows PowerShell
cd C:\SSAFY\gaji_PJT\gajiAI\rag-chatbot_test
```

`.env` 파일 내용 예시:
```env
GEMINI_API_KEYS=YOUR-GEMINI-API-KEY1,YOUR-GEMINI-API-KEY2,YOUR-GEMINI-API-KEY3
```

### 2단계: 캐릭터 페르소나 생성 (선택, 처음 실행 시)

캐릭터 페르소나를 자동으로 생성하려면:

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

**소요 시간**: 책 1개당 약 4-6분 (캐릭터 2명 × 4개 생성)

**주의사항**:
- File Search Store가 설정되어 있어야 합니다 (`py scripts/setup_file_search.py` 실행 필요)
- API 키 할당량을 고려하여 실행하세요

### 3단계: 서버 실행

```bash
# 프로젝트 디렉토리로 이동
cd C:\SSAFY\gaji_PJT\gajiAI\rag-chatbot_test

# 서버 시작
py -m uvicorn app.main:app
```

또는:

```bash
python -m uvicorn app.main:app
```

### 4단계: 서비스 확인

서버가 정상적으로 시작되면 다음 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
[OK] API 키 #1 사용 중
```

### 5단계: API 테스트

#### 브라우저에서 확인
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/character/health
- 캐릭터 목록: http://localhost:8000/character/list

#### PowerShell에서 테스트
```powershell
# 헬스 체크
Invoke-WebRequest -Uri "http://localhost:8000/character/health" -UseBasicParsing

# 캐릭터 목록 조회
Invoke-WebRequest -Uri "http://localhost:8000/character/list" -UseBasicParsing
```

## 📡 API 엔드포인트

### 캐릭터 목록 조회
```http
GET /character/list
```

### 캐릭터 정보 조회
```http
GET /character/info/{character_name}
```

### 캐릭터와 대화
```http
POST /character/chat
Content-Type: application/json

{
  "character_name": "Romeo Montague",
  "message": "줄리엣에 대해 어떻게 생각해?",
  "conversation_history": []  // 선택사항
}
```

### 스트리밍 대화
```http
POST /character/chat/stream
Content-Type: application/json

{
  "character_name": "Sherlock Holmes",
  "message": "가장 어려웠던 사건은?",
  "conversation_history": []
}
```

## 🎭 사용 가능한 캐릭터

| 캐릭터 이름 | 책 제목 |
|------------|---------|
| Victor Frankenstein | Frankenstein; Or, The Modern Prometheus |
| Elizabeth Bennet | Pride and Prejudice |
| Jay Gatsby | The Great Gatsby |
| Romeo Montague | Romeo and Juliet |
| Tom Sawyer | The Adventures of Tom Sawyer, Complete |
| Sherlock Holmes | The Adventures of Sherlock Holmes |

## 🔧 문제 해결

### 서버가 시작되지 않는 경우
1. **포트 충돌**: 다른 프로세스가 8000번 포트를 사용 중일 수 있습니다.
   ```bash
   # 다른 포트로 실행
   py -m uvicorn app.main:app --reload --port 8001
   ```

2. **API 키 오류**: `.env` 파일의 API 키가 올바른지 확인하세요.
   ```
   [ERROR] API Key Manager 초기화 실패
   ```

3. **File Search Store 오류**: `data/file_search_store_info.json` 파일이 있는지 확인하세요.
   - 없다면: `py scripts/setup_file_search.py --mode main` 실행

4. **캐릭터 페르소나 생성 오류**: 
   - File Search Store가 설정되어 있는지 확인
   - `data/char_graph/` 폴더에 인물 관계도 JSON 파일이 있는지 확인
   - `data/origin_txt/saved_books_info.json` 파일이 있는지 확인

### API 할당량 초과 시
- 자동으로 다음 API 키로 전환됩니다.
- 모든 키가 할당량을 초과하면 에러 메시지가 표시됩니다.
- 잠시 후 다시 시도하세요.

## 🛑 서버 종료

서버를 종료하려면:
- 터미널에서 `Ctrl + C` 누르기

또는 PowerShell에서:
```powershell
Stop-Process -Name "python" -Force
```

## 📝 참고사항

- `--reload` 옵션은 코드 변경 시 자동으로 서버를 재시작합니다.
- 프로덕션 환경에서는 `--reload` 옵션을 제거하세요.
- API 키는 자동으로 로테이션되며, 할당량 초과 시 다음 키로 전환됩니다.

