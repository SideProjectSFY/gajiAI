"""
Health Check API

서비스 상태 확인 엔드포인트
"""

from fastapi import APIRouter
import structlog

from app.services.vectordb_client import get_vectordb_client
from app.services.gemini_client import GeminiClient
from app.celery_app import celery_app
from app.models.schemas import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = structlog.get_logger()


@router.get("", response_model=HealthCheckResponse)
async def health_check():
    """
    헬스 체크 엔드포인트
    
    Returns:
        서비스 상태 정보
    """
    status = {
        "status": "healthy",
        "gemini_api": "unknown",
        "vectordb": "unknown",
        "celery_workers": 0
    }
    
    # Gemini API 상태 확인
    try:
        _ = GeminiClient()
        status["gemini_api"] = "connected"
    except Exception as e:
        status["gemini_api"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
        logger.error("gemini_health_check_failed", error=str(e))
    
    # VectorDB 상태 확인
    try:
        vectordb = get_vectordb_client()
        if vectordb.health_check():
            status["vectordb"] = "connected"
        else:
            status["vectordb"] = "disconnected"
            status["status"] = "unhealthy"
    except Exception as e:
        status["vectordb"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
        logger.error("vectordb_health_check_failed", error=str(e))
    
    # Celery 워커 상태 확인
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            status["celery_workers"] = len(active_workers)
    except Exception as e:
        logger.warning("celery_health_check_failed", error=str(e))
    
    return status
