"""
Character Extraction Tasks

소설에서 캐릭터 추출 비동기 작업
chargraph 기능 활용
"""

from app.celery_app import celery_app
from app.config.redis_client import set_task_status, update_task_progress
from app.services.character_extractor import CharacterExtractorService
from app.services.vectordb_client import get_vectordb_client
import structlog
from pathlib import Path
import json
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.character_extraction.extract_characters")
def extract_characters_task(
    self,
    task_id: str,
    novel_id: str,
    novel_file_path: str,
    extraction_mode: str = "full",
    **kwargs
):
    """
    캐릭터 추출 비동기 작업
    
    Args:
        task_id: 작업 ID
        novel_id: 소설 ID (Gutenberg ID 또는 UUID)
        novel_file_path: 소설 텍스트 파일 경로
        extraction_mode: 추출 모드 ("full" 또는 "quick")
        **kwargs: 추가 옵션
            - iterations: 반복 횟수 (기본값: 1)
            - desc_sentences: 캐릭터 설명 문장 수 (기본값: 2)
            - max_main_characters: 최대 주인공 수 (기본값: None, 모든 캐릭터)
    
    Returns:
        추출 결과
    """
    try:
        set_task_status(
            task_id=task_id,
            status="IN_PROGRESS",
            progress=0,
            entity_id=novel_id,
            entity_type="novel",
            task_type="character_extraction"
        )
        
        logger.info(
            "character_extraction_started",
            task_id=task_id,
            novel_id=novel_id,
            extraction_mode=extraction_mode
        )
        
        # 소설 텍스트 읽기
        novel_file = Path(novel_file_path)
        if not novel_file.exists():
            raise FileNotFoundError(f"Novel file not found: {novel_file_path}")
        
        with open(novel_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        update_task_progress(task_id, 10)
        logger.info("character_extraction_text_loaded", novel_id=novel_id, text_length=len(text))
        
        # 추출 옵션 설정
        iterations = kwargs.get('iterations', 1)
        desc_sentences = kwargs.get('desc_sentences', 2)
        max_main_characters = kwargs.get('max_main_characters', None)
        
        if extraction_mode == "quick":
            iterations = 1
            max_main_characters = max_main_characters or 20
        
        # CharacterExtractorService로 캐릭터 추출
        extractor = CharacterExtractorService()
        update_task_progress(task_id, 20)
        
        logger.info(
            "character_extraction_processing",
            novel_id=novel_id,
            iterations=iterations,
            max_main_characters=max_main_characters
        )
        
        result = extractor.extract_characters(
            text=text,
            previous_json=None,
            iterations=iterations,
            desc_sentences=desc_sentences,
            generate_portraits=False,
            copies=1,
            temperature=1.0,
            max_main_characters=max_main_characters
        )
        
        update_task_progress(task_id, 70)
        logger.info(
            "character_extraction_completed",
            novel_id=novel_id,
            characters_count=len(result.get("characters", [])),
            relations_count=len(result.get("relations", []))
        )
        
        # VectorDB에 저장
        vectordb = get_vectordb_client()
        characters_saved = _save_characters_to_vectordb(
            vectordb=vectordb,
            novel_id=novel_id,
            characters=result.get("characters", []),
            relations=result.get("relations", [])
        )
        
        update_task_progress(task_id, 90)
        logger.info(
            "character_extraction_vectordb_saved",
            novel_id=novel_id,
            characters_saved=characters_saved
        )
        
        # char_graph 디렉토리에 JSON 파일로도 저장 (호환성)
        _save_char_graph_json(novel_id, result)
        
        update_task_progress(task_id, 100)
        
        set_task_status(
            task_id=task_id,
            status="COMPLETED",
            progress=100,
            result_data={
                "novel_id": novel_id,
                "characters_count": len(result.get("characters", [])),
                "relations_count": len(result.get("relations", [])),
                "characters_saved": characters_saved
            }
        )
        
        logger.info(
            "character_extraction_task_completed",
            task_id=task_id,
            novel_id=novel_id
        )
        
        return {
            "novel_id": novel_id,
            "characters_count": len(result.get("characters", [])),
            "relations_count": len(result.get("relations", [])),
            "characters_saved": characters_saved
        }
        
    except Exception as e:
        logger.error(
            "character_extraction_failed",
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


def _save_characters_to_vectordb(
    vectordb,
    novel_id: str,
    characters: List[Dict[str, Any]]
) -> int:
    """
    캐릭터를 VectorDB에 저장
    
    Args:
        vectordb: VectorDB 클라이언트
        novel_id: 소설 ID
        characters: 캐릭터 리스트
    
    Returns:
        저장된 캐릭터 수
    """
    try:
        # VectorDBClient의 add_characters 메서드 사용
        success = vectordb.add_characters(
            novel_id=novel_id,
            characters=characters,
            embeddings=None  # 나중에 임베딩 생성 가능
        )
        
        if success:
            saved_count = len(characters)
            logger.info(
                "characters_saved_to_vectordb",
                novel_id=novel_id,
                saved_count=saved_count,
                total_count=len(characters)
            )
            return saved_count
        else:
            logger.error("characters_save_failed", novel_id=novel_id)
            return 0
        
    except Exception as e:
        logger.error(
            "vectordb_save_error",
            novel_id=novel_id,
            error=str(e),
            exc_info=True
        )
        return 0


def _save_char_graph_json(novel_id: str, result: Dict[str, Any]):
    """
    char_graph 디렉토리에 JSON 파일로 저장 (호환성)
    
    Args:
        novel_id: 소설 ID
        result: 추출 결과
    """
    try:
        from pathlib import Path
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        char_graph_dir = project_root / "data" / "char_graph"
        char_graph_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        output_file = char_graph_dir / f"{novel_id}_characters.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(
            "char_graph_json_saved",
            novel_id=novel_id,
            file_path=str(output_file)
        )
    except Exception as e:
        logger.warning(
            "char_graph_json_save_failed",
            novel_id=novel_id,
            error=str(e)
        )

