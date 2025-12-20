"""
FastAPI 메인 애플리케이션

RAG 기반 "What If" 챗봇 API 서버
Story 1.3 기본 설정에 맞게 업데이트
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import structlog

from app.config import settings
from app.middleware import CorrelationIdMiddleware
from app.exceptions import GajiException, ErrorCode
from app.dto.response import error_response

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
    scenario_proxy,  # Phase 1: Spring Boot 통합
    scenario_chat,  # Phase 4: AI 대화 통합
    tasks, 
    metrics,
    novel_ingestion,
    semantic_search,
    character_extraction
)
app.include_router(character_chat.router)
app.include_router(scenario.router)  # 시나리오는 기존 기능 유지
app.include_router(scenario_proxy.router)  # Phase 1: Spring Boot 위임
app.include_router(scenario_proxy.internal_router)  # 내부 전용 엔드포인트 (JWT 인증 없음)
app.include_router(scenario_chat.router)  # Phase 4: AI 대화 통합
app.include_router(tasks.router)
app.include_router(metrics.router)
app.include_router(novel_ingestion.router)
app.include_router(semantic_search.router)
app.include_router(character_extraction.router)


# OpenAPI 스키마 커스터마이징 (JWT Bearer 인증 추가)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # JWT Bearer 인증 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token from Spring Boot /api/v1/auth/login"
        }
    }
    
    # 모든 엔드포인트에 JWT 인증 적용 (jwt_auth를 사용하는 엔드포인트만)
    for path_data in openapi_schema.get("paths", {}).values():
        for operation in path_data.values():
            if isinstance(operation, dict) and "operationId" in operation:
                # jwt_auth dependency를 사용하는 엔드포인트에만 보안 적용
                # scenario_proxy, character_chat 등의 보호된 엔드포인트
                operation["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


# 전역 예외 핸들러
@app.exception_handler(GajiException)
async def gaji_exception_handler(request: Request, exc: GajiException):
    """커스텀 예외 핸들러"""
    logger.warning(
        "gaji_exception",
        error_code=exc.error_code.code,
        message=exc.error_code.message,
        details=exc.details,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            error_code=exc.error_code.code,
            message=exc.error_code.message if not exc.detail.get("message") else exc.detail["message"],
            details=exc.details
        )
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """입력 검증 실패 핸들러"""
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            error_code=ErrorCode.INVALID_INPUT.code,
            message="Input validation failed",
            details={"errors": exc.errors()}
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러 (catch-all)"""
    logger.error(
        "unexpected_error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            error_code=ErrorCode.INTERNAL_SERVER_ERROR.code,
            message="An unexpected error occurred",
            details={"error_type": type(exc).__name__}
        )
    )


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

