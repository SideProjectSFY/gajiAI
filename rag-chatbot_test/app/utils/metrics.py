"""
Metrics Collection

간단한 메트릭 수집 유틸리티
"""

from typing import Dict, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

# 인메모리 메트릭 저장 (프로덕션에서는 Redis나 Prometheus 사용 권장)
_metrics: Dict[str, any] = {
    "requests": {
        "total": 0,
        "by_endpoint": {},
        "errors": 0
    },
    "conversations": {
        "total": 0,
        "by_type": {"character": 0, "scenario": 0}
    },
    "scenarios": {
        "created": 0,
        "forked": 0
    },
    "start_time": datetime.utcnow().isoformat() + "Z"
}


def increment_request(endpoint: str, success: bool = True):
    """
    요청 메트릭 증가
    
    Args:
        endpoint: 엔드포인트 경로
        success: 성공 여부
    """
    _metrics["requests"]["total"] += 1
    
    if endpoint not in _metrics["requests"]["by_endpoint"]:
        _metrics["requests"]["by_endpoint"][endpoint] = {"total": 0, "errors": 0}
    
    _metrics["requests"]["by_endpoint"][endpoint]["total"] += 1
    
    if not success:
        _metrics["requests"]["errors"] += 1
        _metrics["requests"]["by_endpoint"][endpoint]["errors"] += 1
    
    logger.debug("metric_incremented", metric="request", endpoint=endpoint, success=success)


def increment_conversation(conversation_type: str):
    """
    대화 메트릭 증가
    
    Args:
        conversation_type: 대화 타입 ("character" or "scenario")
    """
    _metrics["conversations"]["total"] += 1
    
    if conversation_type in _metrics["conversations"]["by_type"]:
        _metrics["conversations"]["by_type"][conversation_type] += 1
    else:
        _metrics["conversations"]["by_type"][conversation_type] = 1
    
    logger.debug("metric_incremented", metric="conversation", type=conversation_type)


def increment_scenario_created():
    """시나리오 생성 메트릭 증가"""
    _metrics["scenarios"]["created"] += 1
    logger.debug("metric_incremented", metric="scenario_created")


def increment_scenario_forked():
    """시나리오 Fork 메트릭 증가"""
    _metrics["scenarios"]["forked"] += 1
    logger.debug("metric_incremented", metric="scenario_forked")


def get_metrics() -> Dict:
    """
    현재 메트릭 조회
    
    Returns:
        메트릭 딕셔너리
    """
    return _metrics.copy()


def reset_metrics():
    """메트릭 초기화 (테스트용)"""
    global _metrics
    _metrics = {
        "requests": {
            "total": 0,
            "by_endpoint": {},
            "errors": 0
        },
        "conversations": {
            "total": 0,
            "by_type": {"character": 0, "scenario": 0}
        },
        "scenarios": {
            "created": 0,
            "forked": 0
        },
        "start_time": datetime.utcnow().isoformat() + "Z"
    }
    logger.info("metrics_reset")

