# 🚀 서비스 실행 가이드

## 사전 준비사항 확인

### 1. 필수 파일 확인
다음 파일들이 존재하는지 확인하세요:
- ✅ `.env` 파일 (API 키 설정)
- ✅ `data/file_search_store_info.json` (File Search Store 정보)
- ✅ `data/characters.json` (캐릭터 정보)
- ✅ `data/origin_txt/` 폴더에 책 텍스트 파일들

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
GEMINI_API_KEYS=YOUR-GEMINI-API-KEYS
```

### 2단계: 서버 실행

```bash
# 프로젝트 디렉토리로 이동
cd C:\SSAFY\gaji_PJT\gajiAI\rag-chatbot_test

# 서버 시작
py -m uvicorn app.main:app --reload
```

또는:

```bash
python -m uvicorn app.main:app --reload
```

### 3단계: 서비스 확인

서버가 정상적으로 시작되면 다음 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
[OK] API 키 #1 사용 중
```

### 4단계: API 테스트

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

