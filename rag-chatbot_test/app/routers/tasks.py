"""
Task Management API Router

Long Polling 및 비동기 작업 상태 조회 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict
import structlog

from app.utils.redis_client import get_redis_client
from app.config.redis_client import get_task_status as get_sync_task_status

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
logger = structlog.get_logger()


class TaskStatusResponse(BaseModel):
    """작업 상태 응답"""
    task_id: str
    status: str  # "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "not_found"
    progress: int = Field(default=0, ge=0, le=100, description="진행률 (0-100)")
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    task_type: Optional[str] = None
    user_id: Optional[str] = None
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get(
    "/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="작업 상태 조회",
    description="비동기 작업의 현재 상태를 조회합니다. Long Polling을 위해 2초 간격으로 호출하세요."
)
async def get_task_status(
    task_id: str
):
    """
    작업 상태 조회 (Long Polling용)
    
    Args:
        task_id: 작업 ID
    
    Returns:
        작업 상태 정보
    
    Note:
        - Redis가 없으면 "not_found" 상태 반환
        - 작업이 완료되거나 실패하면 결과 데이터 포함
        - 작업이 만료되면 (TTL 초과) "not_found" 반환
        - Long Polling을 위해 2초 간격으로 호출 권장
    """
    try:
        # 동기 Redis 클라이언트 사용 (Celery tasks에서 사용하는 것과 동일)
        task_status = get_sync_task_status(task_id)
        
        if not task_status:
            return TaskStatusResponse(
                task_id=task_id,
                status="not_found",
                progress=0
            )
        
        # progress를 int로 변환
        progress = task_status.get("progress", 0)
        if isinstance(progress, str):
            try:
                progress = int(progress)
            except ValueError:
                progress = 0
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_status.get("status", "unknown"),
            progress=progress,
            entity_id=task_status.get("entity_id"),
            entity_type=task_status.get("entity_type"),
            task_type=task_status.get("task_type"),
            user_id=task_status.get("user_id"),
            result_data=task_status.get("result_data"),
            error_message=task_status.get("error_message"),
            created_at=task_status.get("created_at"),
            updated_at=task_status.get("updated_at")
        )
        
    except Exception as e:
        logger.error("task_status_query_failed", task_id=task_id, error=str(e))
        # Redis 연결 실패 시에도 에러 대신 not_found 반환 (선택적이므로)
        return TaskStatusResponse(
            task_id=task_id,
            status="not_found",
            progress=0,
            error_message=f"Redis 연결 실패: {str(e)}"
        )


@router.delete(
    "/{task_id}",
    summary="작업 상태 삭제",
    description="작업 상태를 Redis에서 삭제합니다. 완료된 작업의 상태를 정리할 때 사용합니다."
)
async def delete_task_status(
    task_id: str
):
    """
    작업 상태 삭제
    
    Args:
        task_id: 작업 ID
    
    Returns:
        삭제 성공 여부
    """
    try:
        from app.config.redis_client import delete_task_status
        
        deleted = delete_task_status(task_id)
        
        if deleted:
            logger.info("task_status_deleted", task_id=task_id)
            return {"task_id": task_id, "deleted": True, "message": "작업 상태가 삭제되었습니다."}
        else:
            return {"task_id": task_id, "deleted": False, "message": "작업 상태를 찾을 수 없습니다."}
            
    except Exception as e:
        logger.error("task_status_delete_failed", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"작업 상태 삭제 실패: {str(e)}"
        )

