"""
Ingestion API

소설 임포트 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog
from uuid import uuid4

from app.services.novel_ingestion import ingest_novel_task
from app.utils.redis_client import get_redis_client
from app.models.schemas import TaskStatusResponse

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])
logger = structlog.get_logger()


class NovelIngestionRequest(BaseModel):
    """소설 임포트 요청"""
    book_id: str
    text: str


@router.post("/novels")
async def ingest_novel(request: NovelIngestionRequest):
    """
    소설 임포트 (비동기 작업)
    
    Args:
        request: 소설 데이터
    
    Returns:
        작업 ID
    """
    try:
        # Celery 작업 생성
        task = ingest_novel_task.delay(request.book_id, request.text)
        task_id = str(task.id)
        
        # Redis에 초기 상태 저장
        redis_client = get_redis_client()
        await redis_client.store_task_result(
            task_id=task_id,
            status="processing",
            result={"book_id": request.book_id}
        )
        
        logger.info("novel_ingestion_started", task_id=task_id, book_id=request.book_id)
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Novel ingestion started"
        }
    
    except Exception as e:
        logger.error("novel_ingestion_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    작업 상태 조회 (Long Polling)
    
    Args:
        task_id: 작업 ID
    
    Returns:
        작업 상태
    """
    try:
        redis_client = get_redis_client()
        status = await redis_client.get_task_status(task_id)
        return status
    
    except Exception as e:
        logger.error("task_status_error", error=str(e), task_id=task_id)
        raise HTTPException(status_code=500, detail=str(e))
