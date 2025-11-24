# 데이터셋 다운로드 가이드

## 개요

이 프로젝트는 **Gutenberg 영어 데이터셋**을 사용합니다. 
데이터셋을 다운로드하여 로컬에 저장한 후, 원하는 책을 검색하고 텍스트 파일로 저장할 수 있습니다.

## 데이터셋 정보

- **데이터셋 이름**: `sedthh/gutenberg_english`
- **출처**: Hugging Face Datasets
- **크기**: 수 GB (전체 데이터셋)
- **책 개수**: 약 48,000+ 권의 영어 고전 문학 작품

## 다운로드 방법

### 1. 기본 다운로드

```bash
# rag-chatbot_test 폴더에서 실행
python scripts/download_dataset.py
```

### 2. 자동 실행 (확인 메시지 없이)

```bash
python scripts/download_dataset.py --yes
```

### 3. 저장 경로 지정

```bash
python scripts/download_dataset.py --save-path "원하는/경로"
```

### 4. 기존 데이터셋 덮어쓰기

```bash
python scripts/download_dataset.py --force --yes
```

## 주의사항

### ⚠️ 중요

1. **디스크 공간**: 최소 10GB 이상의 여유 공간이 필요합니다
2. **다운로드 시간**: 네트워크 속도에 따라 수십 분에서 수 시간이 걸릴 수 있습니다
3. **인터넷 연결**: 안정적인 인터넷 연결이 필요합니다
4. **Hugging Face 계정**: 일부 데이터셋은 로그인이 필요할 수 있습니다

### 다운로드 중단 시

- 부분적으로 다운로드된 파일은 다음 실행 시 재개될 수 있습니다
- 완전히 다시 시작하려면 `--force` 옵션을 사용하세요

## 다운로드 후 사용 방법

데이터셋 다운로드가 완료되면, 다음 스크립트를 사용하여 원하는 책을 검색하고 저장할 수 있습니다:

```bash
# 예시: Frankenstein 검색 및 저장
python scripts/collect_data.py --search "Frankenstein" --yes

# 여러 책 한 번에 검색
python scripts/collect_data.py --search "Frankenstein" "Pride and Prejudice" "The Great Gatsby" --yes
```

## 저장 위치

기본 저장 위치:
```
data/origin_dataset/sedthh___gutenberg_english/
```

이 경로에 데이터셋이 저장되며, `collect_data.py` 스크립트가 이 경로를 기본값으로 사용합니다.

## 문제 해결

### 다운로드 실패 시

1. **인터넷 연결 확인**
   ```bash
   ping huggingface.co
   ```

2. **Hugging Face 로그인** (필요한 경우)
   ```bash
   huggingface-cli login
   ```

3. **디스크 공간 확인**
   ```bash
   # Windows
   dir
   
   # Linux/Mac
   df -h
   ```

4. **부분 다운로드 파일 삭제 후 재시도**
   ```bash
   # 저장 경로의 불완전한 파일 삭제 후
   python scripts/download_dataset.py --force --yes
   ```

### 대안: 작은 샘플 데이터셋 사용

전체 데이터셋이 너무 크다면, 다른 작은 Gutenberg 데이터셋을 사용할 수도 있습니다:

```bash
python scripts/download_dataset.py --dataset-name "다른_데이터셋_이름" --yes
```

## 다음 단계

1. ✅ 데이터셋 다운로드 완료
2. 📚 원하는 책 검색 및 저장 (`collect_data.py`)
3. 🔍 File Search Store 설정 (`setup_file_search.py`)
4. 🎭 챗봇 테스트 (`gradio_test/app.py`)


