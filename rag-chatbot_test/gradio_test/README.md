# Gradio UI for What If Scenario Chat

`rag-chatbot_test`의 What If 시나리오 기능을 테스트할 수 있는 Gradio 인터페이스입니다.

## 기능

- 🔀 **What If 시나리오 생성**: 캐릭터 속성, 사건, 배경 변경을 통한 대체 타임라인 생성
- 💬 **시나리오 대화**: 생성된 시나리오에 맞춰 캐릭터와 대화 (최대 5턴)
- 💾 **대화 저장**: 만족스러운 대화를 시나리오에 저장
- 🎭 **캐릭터 선택**: 다양한 소설 캐릭터 선택
- 📊 **시나리오 정보**: 생성된 시나리오의 상세 정보 표시

## 설치 방법

```bash
# 상위 폴더로 이동
cd ..

# 패키지 설치 (상위 폴더의 requirements.txt 사용)
pip install -r requirements.txt

# Gradio 추가 설치
pip install -r gradio_test/requirements.txt
```

## 환경 변수 설정

`.env` 파일이 상위 폴더에 있어야 합니다:

```env
# 여러 API 키 (쉼표로 구분)
GEMINI_API_KEYS=key1,key2,key3

# 또는 단일 키
GEMINI_API_KEY=your_api_key_here
```

## 실행 방법

```bash
# gradio_test 폴더에서 실행
cd gradio_test
python app.py
```

또는:

```bash
# 상위 폴더에서 실행
python gradio_test/app.py
```

실행 후 브라우저에서 `http://localhost:7860`으로 접속하세요.

## 사용 방법

### 1. 시나리오 생성

1. **시나리오 이름 입력**: 예) "헤르미온이가 슬리데린에 배정되었다면?"
2. **캐릭터 선택**: 드롭다운에서 캐릭터 선택
3. **변경사항 설정** (선택사항):
   - **캐릭터 속성 변경**: 캐릭터의 성격, 능력, 배경 등 변경
   - **사건 변경**: 원작에서 일어난 사건을 다르게 변경
   - **배경 변경**: 시간, 장소 등 배경 설정 변경
4. **시나리오 생성** 버튼 클릭

### 2. 시나리오 대화

1. **첫 메시지 입력**: 시나리오에 맞는 질문이나 인사
2. **대화 진행**: 최대 5턴까지 대화 가능
3. **대화 저장/취소**: 5턴 완료 후 저장 또는 취소 선택

## 사용 가능한 캐릭터

- Victor Frankenstein (Frankenstein)
- Elizabeth Bennet (Pride and Prejudice)
- Jay Gatsby (The Great Gatsby)
- Romeo Montague (Romeo and Juliet)
- Tom Sawyer (The Adventures of Tom Sawyer)
- Sherlock Holmes (The Adventures of Sherlock Holmes)

## 시나리오 예시

### 예시 1: 캐릭터 속성 변경
- **시나리오 이름**: "헤르미온이가 슬리데린에 배정되었다면?"
- **캐릭터**: Hermione Granger (Harry Potter 시리즈)
- **변경사항**: 그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해짐

### 예시 2: 사건 변경
- **시나리오 이름**: "게츠비가 데이지를 만나지 않았다면?"
- **캐릭터**: Jay Gatsby
- **변경사항**: 데이지와의 첫 만남이 없었던 경우

### 예시 3: 배경 변경
- **시나리오 이름**: "오만과 편견이 2024년 서울에서 일어났다면?"
- **캐릭터**: Elizabeth Bennet
- **변경사항**: 19세기 영국에서 2024년 서울로 배경 변경

## 주의사항

1. **File Search Store 설정**: 서비스를 사용하기 전에 File Search Store가 설정되어 있어야 합니다.
   ```bash
   # 상위 폴더에서 실행
   python scripts/setup_file_search.py
   ```

2. **데이터 파일**: `data/characters.json` 파일이 있어야 합니다.

3. **API 키**: Gemini API 키가 올바르게 설정되어 있어야 합니다.

4. **대화 턴 제한**: 첫 대화는 최대 5턴까지 가능합니다. 5턴 완료 후 저장하거나 취소해야 합니다.

## 문제 해결

### 서비스 초기화 실패
- `.env` 파일에 API 키가 올바르게 설정되어 있는지 확인
- `data/file_search_store_info.json` 파일이 있는지 확인

### 캐릭터를 찾을 수 없음
- `data/characters.json` 파일이 있는지 확인
- 캐릭터 이름이 정확한지 확인

### 시나리오 생성 실패
- File Search Store가 올바르게 설정되어 있는지 확인
- API 키 할당량을 확인
- 변경사항 설명이 너무 모호하거나 구체적이지 않은지 확인

### 대화 생성 실패
- 시나리오가 올바르게 생성되었는지 확인
- API 키 할당량을 확인
- 네트워크 연결 상태 확인
