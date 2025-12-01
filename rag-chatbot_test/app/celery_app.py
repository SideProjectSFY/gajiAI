"""
Celery Application Configuration

비동기 작업 큐 설정
Redis is OPTIONAL - falls back to in-memory backend if unavailable
"""

from celery import Celery
from app.config import settings
import structlog
import sys

logger = structlog.get_logger()

# Redis가 설정되어 있으면 Redis 사용, 없으면 메모리 백엔드 사용
try:
    redis_url = settings.get_redis_url()
    if redis_url and redis_url.startswith("redis://"):
        broker_url = f"{redis_url}/0"  # Redis DB 0 (broker)
        backend_url = f"{redis_url}/1"  # Redis DB 1 (result backend)
        logger.info("celery_using_redis", broker=broker_url)
    else:
        raise ValueError("Redis URL not configured")
except (AttributeError, ValueError) as e:
    # Redis 없으면 메모리 백엔드 사용 (개발용)
    broker_url = "memory://"
    backend_url = "cache+memory://"
    logger.warning("celery_using_memory_backend", 
                   reason=str(e),
                   message="Using in-memory backend (not suitable for production)")

# Celery 앱 초기화
celery_app = Celery(
    "gaji_ai_backend",
    broker=broker_url,
    backend=backend_url,
    include=[
        "app.tasks.conversation_generation",
        "app.tasks.novel_ingestion",
        "app.tasks.character_extraction",
    ]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,  # 작업 시작 시간 추적
    task_time_limit=600,  # 작업 최대 실행 시간 (10분)
    task_soft_time_limit=540,  # 작업 소프트 타임아웃 (9분, Windows에서는 지원 안 됨)
    worker_prefetch_multiplier=4,  # Worker가 한 번에 가져올 작업 수
    worker_max_tasks_per_child=1000,  # Worker 재시작 전 최대 작업 수 (메모리 누수 방지, Windows에서는 적용 안 됨)
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

