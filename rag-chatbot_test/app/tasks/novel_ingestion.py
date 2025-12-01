"""
Novel Ingestion Tasks

소설 임베딩 비동기 작업
"""

from app.celery_app import celery_app
from app.config.redis_client import set_task_status, update_task_progress
import structlog

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.novel_ingestion.embed_novel")
def embed_novel_task(
    self,
    task_id: str,
    novel_id: str,
    novel_file_path: str,
    **kwargs
):
    """
    소설 임베딩 비동기 작업
    
    Args:
        task_id: 작업 ID
        novel_id: 소설 ID (Gutenberg ID)
        novel_file_path: 소설 텍스트 파일 경로
        **kwargs: 임베딩 옵션
            - batch_size: 배치 크기
            - chunk_size: 청크 크기
            - reset: 기존 데이터 삭제 여부
    
    Returns:
        임베딩 결과
    """
    try:
        set_task_status(
            task_id=task_id,
            status="IN_PROGRESS",
            progress=0,
            entity_id=novel_id,
            entity_type="novel",
            task_type="novel_ingestion"
        )
        
        logger.info(
            "novel_ingestion_started",
            task_id=task_id,
            novel_id=novel_id
        )
        
        # TODO: 실제 임베딩 로직 구현
        # embed_novels_to_vectordb.py의 로직을 여기로 이동
        update_task_progress(task_id, 50)
        
        # 임베딩 처리...
        # ...
        
        update_task_progress(task_id, 100)
        
        set_task_status(
            task_id=task_id,
            status="COMPLETED",
            progress=100,
            result_data={"novel_id": novel_id, "status": "embedded"}
        )
        
        logger.info(
            "novel_ingestion_completed",
            task_id=task_id,
            novel_id=novel_id
        )
        
        return {"novel_id": novel_id, "status": "embedded"}
        
    except Exception as e:
        logger.error(
            "novel_ingestion_failed",
            task_id=task_id,
            novel_id=novel_id,
            error=str(e),
            exc_info=True
        )
        
        set_task_status(
            task_id=task_id,
            status="FAILED",
            progress=0,
            error_message=str(e)
        )
        
        raise

