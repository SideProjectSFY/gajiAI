#!/bin/bash
# Celery Worker 실행 스크립트 (Linux/Mac)
# 사용법: ./scripts/start_celery_worker.sh

# 현재 스크립트의 디렉토리로 이동
cd "$(dirname "$0")/.."

# Celery Worker 실행 (Linux/Mac는 prefork 사용)
echo "Celery Worker를 시작합니다..."
echo "프로젝트 디렉토리: $(pwd)"
echo ""
celery -A app.celery_app worker --loglevel=info

