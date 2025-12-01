"""
Novel Ingestion API Router

소설 임베딩 및 VectorDB 업로드 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict
from uuid import UUID
import uuid
from datetime import datetime, timezone

from app.tasks.novel_ingestion import embed_novel_task
from app.config.redis_client import get_task_status

router = APIRouter(prefix="/api/ai/novels", tags=["novel-ingestion"])


class NovelIngestRequest(BaseModel):
    """소설 임베딩 요청"""
    novel_file_path: str = Field(..., description="소설 텍스트 파일 경로")
    metadata: Dict = Field(..., description="소설 메타데이터 (title, author, publication_year, genre 등)")


class NovelIngestResponse(BaseModel):
    """소설 임베딩 응답"""
    job_id: str
    status: str
    estimated_duration_minutes: Optional[int] = None
    message: str


class NovelStatusResponse(BaseModel):
    """소설 임베딩 상태 응답"""
    job_id: str
    status: str
    novel_id: Optional[str] = None
    progress: Optional[Dict] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/ingest",
    response_model=NovelIngestResponse,
    status_code=202,
    summary="소설 임베딩 시작",
    description="Project Gutenberg 데이터셋에서 소설을 배치 임포트합니다. 비동기 작업으로 처리됩니다."
)
async def ingest_novel(
    request: NovelIngestRequest
):
    """
    소설 임베딩 시작
    
    Args:
        request: 소설 파일 경로 및 메타데이터
    
    Returns:
        작업 ID 및 상태
    """
    try:
        # 작업 ID 생성
        job_id = f"ingest-{uuid.uuid4()}"
        
        # Celery 태스크 시작
        # TODO: 실제 구현 시 Spring Boot Internal API를 통해 novel_id 생성
        # novel_id = await create_novel_metadata(request.metadata)
        
        task = embed_novel_task.delay(
            task_id=job_id,
            novel_id="",  # TODO: Spring Boot에서 받은 novel_id 사용
            novel_file_path=request.novel_file_path,
            metadata=request.metadata
        )
        
        return NovelIngestResponse(
            job_id=job_id,
            status="processing",
            estimated_duration_minutes=15,
            message=f"Novel ingestion started. Check status at /api/ai/novels/status/{job_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"소설 임베딩 시작 실패: {str(e)}")


@router.get(
    "/status/{job_id}",
    response_model=NovelStatusResponse,
    summary="소설 임베딩 상태 조회",
    description="소설 임베딩 작업의 진행 상태를 조회합니다."
)
async def get_ingestion_status(job_id: str):
    """
    소설 임베딩 상태 조회
    
    Args:
        job_id: 작업 ID
    
    Returns:
        작업 상태 및 진행률
    """
    try:
        status = get_task_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"작업을 찾을 수 없습니다: {job_id}")
        
        return NovelStatusResponse(
            job_id=job_id,
            status=status.get("status", "unknown"),
            novel_id=status.get("novel_id"),
            progress=status.get("progress"),
            completed_at=status.get("completed_at"),
            error=status.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")

