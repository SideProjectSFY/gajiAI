"""
Conversation Generation Tasks

대화 생성 비동기 작업
"""

from app.celery_app import celery_app
from app.config.redis_client import set_task_status, update_task_progress
from app.services.character_chat_service import CharacterChatService
from app.services.scenario_chat_service import ScenarioChatService
import structlog

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.conversation_generation.generate_conversation")
def generate_conversation_task(
    self,
    task_id: str,
    conversation_type: str,  # "character" or "scenario"
    user_id: str,
    **kwargs
):
    """
    대화 생성 비동기 작업
    
    Args:
        task_id: 작업 ID (Redis에서 상태 추적용)
        conversation_type: 대화 타입 ("character" or "scenario")
        user_id: 사용자 ID
        **kwargs: 대화 생성에 필요한 파라미터
            - character_name, message, book_title 등 (character 타입)
            - scenario_id, message 등 (scenario 타입)
    
    Returns:
        생성된 대화 응답
    """
    try:
        # 작업 상태 업데이트
        set_task_status(
            task_id=task_id,
            status="IN_PROGRESS",
            progress=10,
            entity_id=kwargs.get("conversation_id"),
            entity_type="conversation",
            task_type="conversation_generation",
            user_id=user_id
        )
        
        logger.info(
            "conversation_generation_started",
            task_id=task_id,
            conversation_type=conversation_type,
            user_id=user_id
        )
        
        # 진행률 업데이트
        update_task_progress(task_id, 30)
        
        # 대화 타입에 따라 서비스 선택
        if conversation_type == "character":
            service = CharacterChatService()
            result = service.chat(
                character_name=kwargs.get("character_name"),
                user_message=kwargs.get("message"),
                conversation_history=kwargs.get("conversation_history"),
                book_title=kwargs.get("book_title"),
                output_language=kwargs.get("output_language", "ko"),
                conversation_partner_type=kwargs.get("conversation_partner_type", "stranger"),
                other_main_character=kwargs.get("other_main_character"),
                conversation_id=kwargs.get("conversation_id")
            )
        elif conversation_type == "scenario":
            service = ScenarioChatService()
            result = service.chat_with_scenario(
                scenario_id=kwargs.get("scenario_id"),
                user_message=kwargs.get("message"),
                conversation_history=kwargs.get("conversation_history"),
                output_language=kwargs.get("output_language", "ko"),
                is_forked=kwargs.get("forked_scenario_id") is not None,
                forked_scenario_id=kwargs.get("forked_scenario_id"),
                conversation_id=kwargs.get("conversation_id"),
                user_id=user_id,
                conversation_partner_type=kwargs.get("conversation_partner_type", "stranger"),
                other_main_character=kwargs.get("other_main_character")
            )
        else:
            raise ValueError(f"Unknown conversation type: {conversation_type}")
        
        # 진행률 업데이트
        update_task_progress(task_id, 80)
        
        # 최종 상태 업데이트
        set_task_status(
            task_id=task_id,
            status="COMPLETED",
            progress=100,
            result_data={
                "response": result.get("response"),
                "character_name": result.get("character_name"),
                "book_title": result.get("book_title"),
                "conversation_id": result.get("conversation_id")
            }
        )
        
        logger.info(
            "conversation_generation_completed",
            task_id=task_id,
            conversation_id=result.get("conversation_id")
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "conversation_generation_failed",
            task_id=task_id,
            error=str(e),
            exc_info=True
        )
        
        # 실패 상태 업데이트
        set_task_status(
            task_id=task_id,
            status="FAILED",
            progress=0,
            error_message=str(e)
        )
        
        raise

