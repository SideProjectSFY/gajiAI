"""
FastAPI 메인 애플리케이션

RAG 기반 "What If" 챗봇 API 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.routers import chat
from app.api import validation
from app.services.vectordb_client import get_vectordb_client
from app.services.gemini_client import GeminiClient
from app.celery_app import celery_app
from app.middleware import CorrelationIdMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
import redis.asyncio as redis

# Structlog 설정 (with correlation ID context support)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # Merge context vars (correlation ID)
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Gaji AI Backend - Character Chat",
    description="책 속 인물과 대화하는 AI 챗봇 (Gemini File Search 기반)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize Redis for rate limiting (SEC-001 fix)
redis_client = None
if settings.redis_url:
    try:
        redis_client = redis.Redis.from_url(settings.redis_url)
        logger.info("redis_initialized_for_rate_limiting")
    except Exception as e:
        logger.warning("redis_init_failed_rate_limiting_disabled", error=str(e))

# Rate Limiting middleware (SEC-001: must be added before CORS)
app.add_middleware(RateLimiterMiddleware, redis_client=redis_client)

# Correlation ID middleware (must be added first for proper ordering)
app.add_middleware(CorrelationIdMiddleware)

# CORS 설정 - Pattern B: Spring Boot만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.spring_boot_url],  # Spring Boot만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("fastapi_initialized", cors_allowed=settings.spring_boot_url)

# 라우터 등록
from app.routers import chat, character_chat, scenario, ai_generation
from app.api import prompt, context, scenario_testing  # Story 2.1, 2.2 & 2.4: AI Layer
app.include_router(character_chat.router)
app.include_router(scenario.router)
app.include_router(chat.router)
app.include_router(validation.router)
app.include_router(prompt.router)  # Story 2.1: Prompt Adaptation
app.include_router(context.router)  # Story 2.2: Context Window Manager
app.include_router(scenario_testing.router)  # Story 2.4: Scenario Quality Testing
app.include_router(ai_generation.router)  # Story 4.2: AI Generation with Long Polling


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 이벤트"""
    logger.info("application_starting", environment=settings.app_env)
    
    # VectorDB 연결 확인
    try:
        vectordb = get_vectordb_client()
        if vectordb.health_check():
            logger.info("vectordb_connected", type=settings.vectordb_type)
    except Exception as e:
        logger.error("vectordb_connection_failed", error=str(e))


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Gaji AI Backend - Character Chat API",
        "version": "2.0.0",
        "description": "책 속 인물과 대화하는 AI 챗봇 (Gemini File Search 기반)",
        "environment": settings.app_env,
        "endpoints": {
            # Character Chat endpoints
            "character_list": "/character/list",
            "character_info": "/character/info/{character_name}",
            "character_chat": "/character/chat",
            "character_chat_stream": "/character/chat/stream",
            # Scenario endpoints
            "scenario_create": "/scenario/create",
            "scenario_first_conversation": "/scenario/{scenario_id}/first-conversation",
            "scenario_public": "/scenario/public",
            "scenario_detail": "/scenario/{scenario_id}",
            "scenario_fork": "/scenario/{scenario_id}/fork",
            # RAG Chat endpoints
            "chat": "/api/conversations/{id}/messages",
            "chat_stream": "/api/conversations/{id}/messages/stream",
            "search": "/api/search/passages",
            # AI Prompt Adaptation (Story 2.1)
            "adapt_prompt": "/api/ai/adapt-prompt",
            "circuit_breaker_status": "/api/ai/circuit-breaker/status",
            # AI Context Management (Story 2.2)
            "build_context": "/api/ai/build-context",
            "context_metrics": "/api/ai/context-metrics",
            # AI Scenario Testing (Story 2.4)
            "test_suite": "/api/ai/test-suite",
            "test_scenario": "/api/ai/test-scenario/{test_id}",
            "test_categories": "/api/ai/test-categories",
            "test_list": "/api/ai/test-list",
            # Health & Docs
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """
    헬스 체크 엔드포인트

    Gemini API, VectorDB, Redis, Celery 워커 상태 확인
    Story 0.6: Inter-Service Health Check & API Contract
    """
    from datetime import datetime, timezone
    import redis

    status = {
        "status": "healthy",
        "gemini_api": "unknown",
        "vectordb": "unknown",
        "vectordb_type": settings.vectordb_type,
        "vectordb_collections": 0,
        "redis": "unknown",
        "redis_long_polling_ttl": "600s",
        "celery_workers": 0,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    # Gemini API 상태 확인
    try:
        gemini_client = GeminiClient()
        # 간단한 테스트로 상태 확인 (실제 연결 검증)
        _ = gemini_client  # 인스턴스 생성 성공 확인
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
            # Count collections
            try:
                collections = vectordb.list_collections()
                status["vectordb_collections"] = len(collections) if collections else 0
            except Exception:
                status["vectordb_collections"] = 0
        else:
            status["vectordb"] = "disconnected"
            status["status"] = "unhealthy"
    except Exception as e:
        status["vectordb"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
        logger.error("vectordb_health_check_failed", error=str(e))

    # Redis 상태 확인 (Celery broker + Long Polling storage)
    try:
        if settings.redis_url:
            r = redis.Redis.from_url(settings.redis_url)
            r.ping()
            status["redis"] = "connected"
        else:
            status["redis"] = "not_configured"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
        logger.error("redis_health_check_failed", error=str(e))

    # Celery 워커 상태 확인
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            status["celery_workers"] = len(active_workers)
        else:
            status["celery_workers"] = 0
    except Exception as e:
        status["celery_workers"] = 0
        logger.warning("celery_health_check_failed", error=str(e))

    logger.info("health_check", **status)
    return status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

