"""
Celery Application Configuration

비동기 작업 큐 설정
"""

from celery import Celery
from app.config import settings

# Celery 앱 생성
celery_app = Celery(
    "gaji_ai_backend",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend(),
    include=[
        "app.tasks.conversation_generation",
        "app.tasks.novel_ingestion",
    ]
)

# Celery 설정
import sys

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # 작업 시작 시간 추적
    task_time_limit=300,  # 작업 최대 실행 시간 (5분)
    task_soft_time_limit=240,  # 작업 소프트 타임아웃 (4분, Windows에서는 지원 안 됨)
    worker_prefetch_multiplier=1,  # Worker가 한 번에 가져올 작업 수
    worker_max_tasks_per_child=50,  # Worker 재시작 전 최대 작업 수 (메모리 누수 방지, Windows에서는 적용 안 됨)
    result_expires=3600,  # 결과 저장 시간 (1시간)
    broker_connection_retry_on_startup=True,  # Celery 6.0+ 호환성
)

# Windows에서는 prefork를 사용할 수 없으므로 solo 풀 사용
if sys.platform == "win32":
    celery_app.conf.worker_pool = "solo"

# Task 라우팅 설정
celery_app.conf.task_routes = {
    "app.tasks.conversation_generation.*": {"queue": "conversations"},
    "app.tasks.novel_ingestion.*": {"queue": "ingestion"},
}

