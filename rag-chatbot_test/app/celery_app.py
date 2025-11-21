"""
Celery Application Configuration

비동기 작업 큐 설정
Redis is OPTIONAL - falls back to in-memory backend if unavailable
"""

from celery import Celery
from app.config import settings
import structlog

logger = structlog.get_logger()

# Redis가 설정되어 있으면 Redis 사용, 없으면 메모리 백엔드 사용
try:
    # Redis URL이 설정되어 있는지 확인
    if settings.redis_url and settings.redis_url != "redis://localhost:6379":
        broker_url = f"{settings.redis_url}/0"  # Redis DB 0 (broker)
        backend_url = f"{settings.redis_url}/1"  # Redis DB 1 (result backend)
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
    "gaji_ai_tasks",
    broker=broker_url,
    backend=backend_url
)

# Celery 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10분 제한
    task_soft_time_limit=540,  # 9분 소프트 제한
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# 작업 자동 검색
celery_app.autodiscover_tasks(['app.services'])


@celery_app.task(name="test_task")
def test_task(message: str) -> str:
    """테스트 작업"""
    return f"Task completed: {message}"
