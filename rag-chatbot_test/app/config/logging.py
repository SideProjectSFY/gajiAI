"""
Structured Logging Configuration

structlog를 사용한 구조화된 로깅 설정
"""

import structlog
import logging
import sys
from app.config import settings


def configure_logging():
    """
    구조화된 로깅 설정
    
    - 개발 환경: 콘솔 포맷터 (가독성 좋은 출력)
    - 프로덕션 환경: JSON 포맷터 (로그 수집 시스템과 호환)
    """
    # 기본 로깅 설정
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    
    # structlog 프로세서 체인 설정
    processors = [
        structlog.contextvars.merge_contextvars,  # 컨텍스트 변수 병합
        structlog.processors.add_log_level,  # 로그 레벨 추가
        structlog.processors.StackInfoRenderer(),  # 스택 정보 렌더링
        structlog.processors.format_exc_info,  # 예외 정보 포맷팅
    ]
    
    # 포맷터 선택
    if settings.log_format.lower() == "json":
        # JSON 포맷터 (프로덕션)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # 콘솔 포맷터 (개발)
        processors.extend([
            structlog.processors.TimeStamper(fmt="iso"),  # ISO 8601 타임스탬프
            structlog.dev.ConsoleRenderer()  # 컬러 콘솔 출력
        ])
    
    # structlog 설정
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """
    구조화된 로거 반환
    
    Args:
        name: 로거 이름 (None이면 호출 모듈 이름 사용)
    
    Returns:
        structlog.BoundLogger 인스턴스
    
    Usage:
        logger = get_logger(__name__)
        logger.info("event_name", key="value", user_id="123")
    """
    return structlog.get_logger(name)


# 애플리케이션 시작 시 로깅 설정
configure_logging()

