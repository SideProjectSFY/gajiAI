# Merge Conflict 해결 가이드

## 충돌 원인

현재 브랜치(`refactor/spring-boot-integration`)와 `main` 브랜치가 서로 다른 방향으로 발전하여 충돌이 발생했습니다.

## 해결 방법

### 방법 1: GitHub 웹 에디터 사용 (가장 간단)

1. GitHub PR 페이지에서 **"Resolve conflicts"** 버튼 클릭
2. 각 충돌 파일에서:
   - **현재 브랜치 버전을 선택** (우측 "Accept incoming change" 또는 수동으로 `<<<<<<<`, `=======`, `>>>>>>>` 제거)
   - 이유: 현재 브랜치가 최신 구조로 리팩토링되었기 때문
3. **"Mark as resolved"** 클릭
4. 모든 충돌 해결 후 **"Commit merge"** 클릭

### 방법 2: 로컬에서 해결 (더 정확한 제어)

```bash
# 1. main 브랜치 최신화
git fetch origin
git checkout main
git pull origin main

# 2. 현재 브랜치로 돌아가기
git checkout refactor/spring-boot-integration

# 3. main 병합 시작
git merge origin/main --no-commit

# 4. 충돌 파일들을 현재 브랜치 버전으로 선택
git checkout --ours rag-chatbot_test/app/config/settings.py
git checkout --ours rag-chatbot_test/app/config/redis_client.py
git checkout --ours rag-chatbot_test/app/main.py
git checkout --ours rag-chatbot_test/README.md
git checkout --ours rag-chatbot_test/requirements.txt
git checkout --ours rag-chatbot_test/Dockerfile.dev
git checkout --ours rag-chatbot_test/app/routers/scenario.py
git checkout --ours rag-chatbot_test/app/services/base_chat_service.py
git checkout --ours rag-chatbot_test/app/services/character_chat_service.py
git checkout --ours rag-chatbot_test/app/services/scenario_chat_service.py
git checkout --ours rag-chatbot_test/app/services/scenario_management_service.py

# 5. main에만 있는 config.py 삭제 (이미 config/ 디렉토리로 구조화됨)
git rm rag-chatbot_test/app/config.py 2>$null

# 6. 변경사항 스테이징
git add .

# 7. merge 커밋
git commit -m "merge: main 브랜치 병합 (refactor/spring-boot-integration 변경사항 우선)

- config.py → config/ 디렉토리 구조로 통합
- Spring Boot 통합 및 Redis 기반 임시 대화 저장 적용
- 모든 충돌을 현재 브랜치 버전으로 해결"

# 8. 원격 저장소에 푸시
git push origin refactor/spring-boot-integration
```

### 방법 3: Rebase 사용 (히스토리 정리)

```bash
# 1. main 최신화
git fetch origin
git checkout refactor/spring-boot-integration

# 2. Rebase 시작
git rebase origin/main

# 3. 충돌 발생 시 (각 파일마다)
git checkout --ours <충돌파일>
git add <충돌파일>
git rebase --continue

# 4. 모든 충돌 해결 후
git push origin refactor/spring-boot-integration --force-with-lease
```

## 각 파일별 충돌 해결 가이드

### 1. `app/config/settings.py`
- **선택**: 현재 브랜치 버전 (config/ 디렉토리 구조)
- **이유**: 더 구조화된 설정 관리

### 2. `app/config/redis_client.py`
- **선택**: 현재 브랜치 버전
- **이유**: Redis 임시 대화 저장 기능 포함

### 3. `app/main.py`
- **선택**: 현재 브랜치 버전
- **이유**: Spring Boot 통합 및 새로운 라우터 등록

### 4. `app/services/*.py`
- **선택**: 현재 브랜치 버전
- **이유**: Redis 기반 저장, Spring Boot 통합 등 최신 기능

### 5. `README.md`
- **선택**: 현재 브랜치 버전
- **이유**: Spring Boot 통합 가이드 포함

### 6. `requirements.txt`
- **주의**: 두 버전을 비교하여 필요한 패키지 모두 포함
- **권장**: 현재 브랜치 버전 + main의 추가 패키지 확인

### 7. `Dockerfile.dev`
- **선택**: 현재 브랜치 버전
- **이유**: 최신 Docker 설정

## 주의사항

⚠️ **`--force` 사용 시 주의**: 
- Rebase 후 force push는 팀원과 협의 필요
- `--force-with-lease` 사용 권장 (안전한 force push)

## 검증

충돌 해결 후:
1. 로컬에서 테스트 실행
2. 서비스 시작 확인
3. PR 리뷰 요청

