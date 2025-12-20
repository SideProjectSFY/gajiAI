"""
Metrics API Router

메트릭 조회 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
import structlog

from app.utils.metrics import get_metrics

router = APIRouter(prefix="/api/metrics", tags=["metrics"])
logger = structlog.get_logger()


@router.get(
    "",
    summary="메트릭 조회",
    description="애플리케이션 메트릭을 조회합니다. (요청 수, 대화 수, 시나리오 수 등)"
)
async def get_application_metrics() -> Dict:
    """
    애플리케이션 메트릭 조회
    
    Returns:
        메트릭 정보
    """
    try:
        metrics = get_metrics()
        logger.info("metrics_queried")
        return metrics
    except Exception as e:
        logger.error("metrics_query_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"메트릭 조회 실패: {str(e)}"
        )

