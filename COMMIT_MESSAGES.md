# Git Commit 메시지 가이드

## 커밋 전략

변경 사항이 많으므로 **논리적으로 그룹화하여 여러 커밋**으로 나누는 것을 권장합니다.

---

## 커밋 1: Spring Boot 통합 및 프록시 엔드포인트

```bash
git add rag-chatbot_test/app/routers/scenario_proxy.py
git add rag-chatbot_test/app/services/spring_boot_client.py
git add rag-chatbot_test/app/config/
git add rag-chatbot_test/app/dto/
git add rag-chatbot_test/app/exceptions.py
git add rag-chatbot_test/app/middleware/
git add rag-chatbot_test/app/main.py
git add rag-chatbot_test/app/routers/__init__.py
git add rag-chatbot_test/requirements.txt

git commit -m "feat: Spring Boot 통합 및 API Gateway 프록시 구현

- Spring Boot API Gateway와 통신하는 프록시 엔드포인트 추가
  - scenario_proxy.py: 시나리오 CRUD 프록시 (Phase 1)
  - spring_boot_client.py: Spring Boot 내부 API 클라이언트
- FastAPI 표준 응답 형식 (success, data, message, timestamp) 적용
- JWT 인증 미들웨어 및 예외 처리 추가
- DTO 및 설정 모듈 구조화
- 내부 API 엔드포인트 추가 (/api/internal/scenarios/analyze)

Related: Epic 0 (Story 0.1), Epic 1 (Phase 1 통합)"
```

---

## 커밋 2: Redis 기반 임시 대화 저장

```bash
git add rag-chatbot_test/app/config/redis_client.py
git add rag-chatbot_test/app/services/scenario_chat_service.py
git add rag-chatbot_test/app/services/character_chat_service.py

git commit -m "feat: Redis 기반 임시 대화 저장으로 전환

- 로컬 파일 저장 → Redis 저장으로 전환
  - temp_conversations 디렉토리 제거
  - Redis TTL 자동 관리 (1시간)
- scenario_chat_service.py: Redis 임시 대화 저장/조회
- character_chat_service.py: Redis 임시 대화 저장/조회
- 동시성 개선: 여러 사용자 동시 사용 지원
- 서버 재시작 후에도 데이터 유지

Related: Epic 4 (Conversation System)"
```

---

## 커밋 3: 캐릭터 및 시나리오 대화 서비스

```bash
git add rag-chatbot_test/app/routers/character_chat.py
git add rag-chatbot_test/app/routers/scenario_chat.py
git add rag-chatbot_test/app/services/character_chat_service.py
git add rag-chatbot_test/app/services/scenario_chat_service.py
git add rag-chatbot_test/app/services/base_chat_service.py
git add rag-chatbot_test/app/services/character_data_loader.py
git add rag-chatbot_test/app/services/scenario_management_service.py

git commit -m "feat: 캐릭터 및 시나리오 기반 AI 대화 서비스 구현

- 캐릭터 대화 서비스 (CharacterChatService)
  - Gemini File Search 기반 RAG 대화
  - 캐릭터 페르소나 및 말투 적용
  - 다국어 지원 (ko, en, ja, zh)
- 시나리오 대화 서비스 (ScenarioChatService)
  - What If 시나리오 기반 대화
  - whatIfQuestion 핵심 전제 반영
  - Spring Boot PostgreSQL 연동 (JWT 인증)
- BaseChatService: 공통 API 호출 및 에러 처리
- ScenarioManagementService: Gemini 기반 시나리오 분석

Related: Epic 2 (AI Character Adaptation), Epic 1 (What If Scenarios)"
```

---

## 커밋 4: Celery 비동기 작업 처리

```bash
git add rag-chatbot_test/app/celery_app.py
git add rag-chatbot_test/app/tasks/
git add rag-chatbot_test/app/routers/character_extraction.py
git add rag-chatbot_test/app/routers/novel_ingestion.py
git add rag-chatbot_test/app/routers/tasks.py
git add rag-chatbot_test/app/services/character_extractor.py
git add rag-chatbot_test/scripts/start_celery_worker.*

git commit -m "feat: Celery 기반 비동기 작업 처리

- Celery 워커 설정 및 태스크 정의
- 캐릭터 추출 비동기 작업 (character_extraction.py)
- 소설 수집 비동기 작업 (novel_ingestion.py)
- Long Polling을 위한 작업 상태 조회 API
- Redis 브로커 연동

Related: Epic 0 (Infrastructure)"
```

---

## 커밋 5: VectorDB 및 검색 기능

```bash
git add rag-chatbot_test/app/services/vectordb_client.py
git add rag-chatbot_test/app/routers/semantic_search.py
git add rag-chatbot_test/app/routers/scenario.py

git commit -m "feat: VectorDB 클라이언트 및 시맨틱 검색 구현

- ChromaDB 클라이언트 (vectordb_client.py)
- 시맨틱 검색 API (semantic_search.py)
- 시나리오 관리 라우터 (scenario.py)
- 5개 컬렉션 지원 (novel_passages, characters, locations, events, themes)

Related: Epic 0 (VectorDB Setup)"
```

---

## 커밋 6: Docker 및 인프라 설정

```bash
git add rag-chatbot_test/Dockerfile.dev
git add rag-chatbot_test/.dockerignore
git add rag-chatbot_test/docker-compose.yml
git add rag-chatbot_test/scripts/start_redis.*

git commit -m "feat: Docker 및 개발 환경 설정

- Dockerfile.dev: FastAPI 개발 환경
- docker-compose.yml: 로컬 개발용 서비스 오케스트레이션
- Redis 시작 스크립트 추가
- .dockerignore: 불필요한 파일 제외

Related: Epic 0 (Infrastructure)"
```

---

## 커밋 7: 유틸리티 및 메트릭

```bash
git add rag-chatbot_test/app/utils/
git add rag-chatbot_test/app/routers/metrics.py
git add rag-chatbot_test/app/services/api_key_manager.py

git commit -m "feat: 유틸리티 및 모니터링 기능

- API 키 관리자 (다중 키 로테이션)
- 메트릭 수집 및 조회 API
- Redis 유틸리티 (비동기 작업 상태 관리)
- 로깅 및 에러 처리 유틸리티

Related: Epic 0 (Infrastructure)"
```

---

## 커밋 8: 스크립트 및 데이터 처리

```bash
git add rag-chatbot_test/scripts/setup_file_search.py
git add rag-chatbot_test/scripts/embed_novels_to_vectordb.py
git add rag-chatbot_test/scripts/generate_character_personas.py
git add rag-chatbot_test/scripts/migrate_scenarios_to_db.py
git add rag-chatbot_test/scripts/convert_to_csv.py
git add rag-chatbot_test/scripts/download_dataset.py
git add rag-chatbot_test/scripts/collect_data.py

git commit -m "feat: 데이터 처리 및 마이그레이션 스크립트

- Gemini File Search Store 설정 스크립트
- VectorDB 임베딩 생성 스크립트
- 캐릭터 페르소나 생성 스크립트
- 시나리오 DB 마이그레이션 스크립트
- 데이터 수집 및 변환 유틸리티

Related: Epic 0 (Data Import)"
```

---

## 커밋 9: 테스트 및 문서

```bash
git add rag-chatbot_test/tests/
git add rag-chatbot_test/pytest.ini
git add .github/
git add docs/
git add rag-chatbot_test/README.md

git commit -m "docs: 테스트 코드 및 문서 추가

- 통합 테스트 코드 (test_phase1_integration.py)
- pytest 설정
- GitHub Actions 워크플로우
- 프로젝트 문서 (docs/)
- README 업데이트 (Spring Boot 통합 가이드)

Related: Epic 0 (Documentation)"
```

---

## 커밋 10: 레거시 코드 제거

```bash
git rm rag-chatbot_test/app/routers/chat.py
git rm rag-chatbot_test/app/services/question_classifier.py
git rm rag-chatbot_test/app/services/rag_service.py
git rm rag-chatbot_test/scripts/generate_embeddings.py
git rm rag-chatbot_test/scripts/import_to_chromadb.py
git rm rag-chatbot_test/scripts/preprocess_text.py

git commit -m "refactor: 레거시 코드 제거

- chat.py: 통합된 character_chat.py로 대체
- question_classifier.py: 더 이상 사용하지 않음
- rag_service.py: base_chat_service.py로 통합
- 구버전 임베딩/전처리 스크립트 제거

Related: Epic 0 (Code Cleanup)"
```

---

## 커밋 11: Git 설정 업데이트

```bash
git add rag-chatbot_test/.gitignore

git commit -m "chore: .gitignore 업데이트

- data/ 디렉토리 제외 (대용량 파일)
- ChromaDB 데이터 제외
- 임시 파일 및 캐시 제외

Related: Epic 0 (Configuration)"
```

---

## 전체 커밋 한 번에 (권장하지 않음)

만약 모든 변경사항을 한 번에 커밋하려면:

```bash
git add -A

git commit -m "feat: Spring Boot 통합 및 AI 대화 서비스 구현

주요 변경사항:
- Spring Boot API Gateway 통합 (scenario_proxy, spring_boot_client)
- Redis 기반 임시 대화 저장 (동시성 개선)
- 캐릭터 및 시나리오 기반 AI 대화 서비스
- Celery 비동기 작업 처리
- VectorDB 클라이언트 및 시맨틱 검색
- Docker 개발 환경 설정
- 레거시 코드 제거 및 리팩토링

Related: Epic 0 (Story 0.1), Epic 1 (Phase 1), Epic 2, Epic 4"
```

---

## 커밋 순서 권장사항

1. **인프라 먼저**: Docker, Redis, Celery 설정
2. **핵심 기능**: Spring Boot 통합, 대화 서비스
3. **보조 기능**: 유틸리티, 메트릭, 스크립트
4. **정리**: 레거시 코드 제거, 문서 업데이트

이 순서로 커밋하면 리뷰와 롤백이 용이합니다.

