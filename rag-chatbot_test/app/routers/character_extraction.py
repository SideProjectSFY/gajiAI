"""
Character Extraction API Router

소설에서 캐릭터 추출 API
chargraph 기능 활용
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
import uuid
import json
from pathlib import Path
import structlog

from app.tasks.character_extraction import extract_characters_task
from app.config.redis_client import get_task_status

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/ai/characters", tags=["character-extraction"])


class CharacterExtractRequest(BaseModel):
    """캐릭터 추출 요청"""
    novel_id: str = Field(..., description="소설 ID (Gutenberg ID 또는 UUID)")
    extraction_mode: str = Field("full", description="추출 모드 (full, quick)")
    iterations: Optional[int] = Field(1, description="반복 횟수 (기본값: 1)")
    desc_sentences: Optional[int] = Field(2, description="캐릭터 설명 문장 수 (기본값: 2)")
    max_main_characters: Optional[int] = Field(None, description="최대 주인공 수 (None이면 모든 캐릭터)")


class CharacterExtractResponse(BaseModel):
    """캐릭터 추출 응답"""
    job_id: str
    status: str
    estimated_duration_minutes: Optional[int] = None
    message: Optional[str] = None


class CharacterExtractionStatusResponse(BaseModel):
    """캐릭터 추출 상태 응답"""
    job_id: str
    status: str  # pending, processing, completed, failed
    novel_id: Optional[str] = None
    progress: Dict = Field(default_factory=dict)
    characters_count: Optional[int] = None
    relations_count: Optional[int] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


def _find_novel_file_path(novel_id: str) -> Optional[str]:
    """
    novel_id로 소설 파일 경로 찾기
    
    Args:
        novel_id: 소설 ID (Gutenberg ID)
    
    Returns:
        파일 경로 또는 None
    """
    try:
        # 프로젝트 루트 찾기
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        saved_books_info = project_root / "data" / "origin_txt" / "saved_books_info.json"
        origin_txt_dir = project_root / "data" / "origin_txt"
        
        if not saved_books_info.exists():
            logger.warning("saved_books_info_not_found", path=str(saved_books_info))
            return None
        
        # saved_books_info.json에서 novel_id로 파일 경로 찾기
        with open(saved_books_info, 'r', encoding='utf-8') as f:
            books_info = json.load(f)
        
        # novel_id가 Gutenberg ID인 경우
        for book in books_info:
            if str(book.get('gutenberg_id', '')) == str(novel_id):
                filepath = book.get('filepath', '')
                if filepath:
                    # 절대 경로 또는 상대 경로 처리
                    if Path(filepath).is_absolute():
                        return filepath
                    else:
                        # origin_txt 디렉토리 기준으로 찾기
                        full_path = origin_txt_dir / filepath
                        if full_path.exists():
                            return str(full_path)
                        # 파일명만 있는 경우
                        filename = Path(filepath).name
                        txt_file = origin_txt_dir / filename
                        if txt_file.exists():
                            return str(txt_file)
        
        # novel_id가 파일명인 경우 직접 찾기
        txt_file = origin_txt_dir / f"{novel_id}.txt"
        if txt_file.exists():
            return str(txt_file)
        
        logger.warning("novel_file_not_found", novel_id=novel_id)
        return None
        
    except Exception as e:
        logger.error("find_novel_file_path_error", novel_id=novel_id, error=str(e))
        return None


@router.post(
    "/extract",
    response_model=CharacterExtractResponse,
    status_code=202,
    summary="캐릭터 추출 시작",
    description="Gemini 2.5 Flash를 사용하여 소설에서 캐릭터 엔티티 및 특성을 추출합니다. chargraph 기능을 활용합니다."
)
async def extract_characters(request: CharacterExtractRequest):
    """
    캐릭터 추출 시작
    
    Args:
        request: 소설 ID 및 추출 모드
    
    Returns:
        작업 ID 및 상태
    """
    try:
        # 소설 파일 경로 찾기
        novel_file_path = _find_novel_file_path(request.novel_id)
        if not novel_file_path:
            raise HTTPException(
                status_code=404,
                detail=f"소설 파일을 찾을 수 없습니다: {request.novel_id}"
            )
        
        # 작업 ID 생성
        job_id = f"extract-chars-{uuid.uuid4().hex[:12]}"
        
        logger.info(
            "character_extraction_started",
            job_id=job_id,
            novel_id=request.novel_id,
            extraction_mode=request.extraction_mode,
            novel_file_path=novel_file_path
        )
        
        # Celery 태스크 시작
        task = extract_characters_task.delay(
            task_id=job_id,
            novel_id=request.novel_id,
            novel_file_path=novel_file_path,
            extraction_mode=request.extraction_mode,
            iterations=request.iterations,
            desc_sentences=request.desc_sentences,
            max_main_characters=request.max_main_characters
        )
        
        estimated_minutes = 20 if request.extraction_mode == "full" else 5
        
        return CharacterExtractResponse(
            job_id=job_id,
            status="processing",
            estimated_duration_minutes=estimated_minutes,
            message=f"Character extraction started. Check status at /api/ai/characters/status/{job_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("character_extraction_start_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"캐릭터 추출 시작 실패: {str(e)}")


@router.get(
    "/status/{job_id}",
    response_model=CharacterExtractionStatusResponse,
    summary="캐릭터 추출 상태 조회",
    description="진행 중인 캐릭터 추출 작업의 상태를 조회합니다."
)
async def check_extraction_status(job_id: str):
    """
    캐릭터 추출 상태 조회
    
    Args:
        job_id: 작업 ID
    
    Returns:
        작업 상태 정보
    """
    try:
        task_status = get_task_status(job_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail=f"작업을 찾을 수 없습니다: {job_id}")
        
        # result_data가 JSON 문자열로 저장되어 있을 수 있으므로 파싱
        result_data = task_status.get("result_data")
        if isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except json.JSONDecodeError:
                result_data = {}
        
        return CharacterExtractionStatusResponse(
            job_id=job_id,
            status=task_status.get("status", "unknown"),
            novel_id=task_status.get("entity_id"),
            progress={
                "percentage": task_status.get("progress", 0)
            },
            characters_count=result_data.get("characters_count") if isinstance(result_data, dict) else None,
            relations_count=result_data.get("relations_count") if isinstance(result_data, dict) else None,
            completed_at=task_status.get("updated_at") if task_status.get("status") == "COMPLETED" else None,
            error_message=task_status.get("error_message")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("character_extraction_status_check_failed", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"추출 상태 조회 실패: {str(e)}")

