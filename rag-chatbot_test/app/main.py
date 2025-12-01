"""
FastAPI 메인 애플리케이션

RAG 기반 "What If" 챗봇 API 서버
Story 1.3 기본 설정에 맞게 업데이트
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import structlog

from app.config import settings
from app.middleware import CorrelationIdMiddleware

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
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    - 시작 시: VectorDB 연결 확인
    - 종료 시: 리소스 정리
    """
    # 시작 시
    logger.info("application_starting", environment=settings.app_env)
    
    # VectorDB 연결 확인
    try:
        from app.services.vectordb_client import get_vectordb_client
        vectordb = get_vectordb_client()
        if vectordb.health_check():
            logger.info("vectordb_connected", type=settings.vectordb_type)
    except Exception as e:
        logger.error("vectordb_connection_failed", error=str(e))
    
    yield
    
    # 종료 시
    logger.info("application_shutting_down")


app = FastAPI(
    title="Gaji AI Backend - Character Chat",
    description="RAG 기반 What If 챗봇 API (Internal-Only Service)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Correlation ID middleware (must be added first for proper ordering)
app.add_middleware(CorrelationIdMiddleware)

# CORS 설정 - Pattern B: Spring Boot만 허용
cors_origins = settings.get_cors_origins()
logger.info("fastapi_initialized", cors_allowed=cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Spring Boot만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from app.routers import (
    character_chat, 
    scenario, 
    tasks, 
    metrics,
    novel_ingestion,
    semantic_search,
    character_extraction
)
app.include_router(character_chat.router)
app.include_router(scenario.router)  # 시나리오는 기존 기능 유지
app.include_router(tasks.router)
app.include_router(metrics.router)
app.include_router(novel_ingestion.router)
app.include_router(semantic_search.router)
app.include_router(character_extraction.router)


@app.get("/", tags=["health"], summary="API 정보", description="API 기본 정보 및 엔드포인트 목록을 반환합니다.")
async def root():
    """루트 엔드포인트 - API 정보"""
    return {
        "message": "Gaji AI Backend - Character Chat API",
        "version": "2.0.0",
        "description": "책 속 인물과 대화하는 AI 챗봇 (Gemini File Search 기반)",
        "docs": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "endpoints": {
            "character_list": "/api/ai/characters",
            "character_info": "/api/ai/characters/{vectordb_id}",
            "character_info_by_name": "/api/ai/characters/info/{character_name}",
            "conversation": "/api/ai/conversations/{conversation_id}/messages",
            "novel_ingest": "/api/ai/novels/ingest",
            "novel_status": "/api/ai/novels/status/{job_id}",
            "semantic_search": "/api/ai/search/passages",
            "character_extract": "/api/ai/characters/extract",
            "health": "/health",
            "scenario_create": "/api/scenarios",
            "scenario_list": "/api/scenarios",
            "scenario_detail": "/api/scenarios/{id}",
            "scenario_fork": "/api/scenarios/{id}/fork",
            "scenario_chat": "/api/scenarios/{scenario_id}/chat",
            "task_status": "/api/tasks/{task_id}/status"
        }
    }


@app.get("/health", tags=["health"])
async def health():
    """
    헬스 체크 엔드포인트

    Gemini API, VectorDB, Redis, Celery 워커 상태 확인
    Story 0.6: Inter-Service Health Check & API Contract
    """
    import redis
    from app.celery_app import celery_app
    
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
        from app.services.api_key_manager import get_api_key_manager
        api_key_manager = get_api_key_manager()
        if api_key_manager.api_keys:
            status["gemini_api"] = "connected"
        else:
            status["gemini_api"] = "no_keys_configured"
            status["status"] = "unhealthy"
    except Exception as e:
        status["gemini_api"] = f"error: {str(e)}"
        status["status"] = "unhealthy"
        logger.error("gemini_health_check_failed", error=str(e))

    # VectorDB 상태 확인
    try:
        from app.services.vectordb_client import get_vectordb_client
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
        redis_url = settings.get_redis_url()
        if redis_url and redis_url.startswith("redis://"):
            r = redis.Redis.from_url(redis_url)
            r.ping()
            status["redis"] = "connected"
        else:
            status["redis"] = "not_configured"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        # Redis는 선택적이므로 unhealthy로 표시하지 않음
        logger.warning("redis_health_check_failed", error=str(e))

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

