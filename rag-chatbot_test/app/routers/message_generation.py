"""
메시지 생성 라우터

Spring Boot에서 호출하는 /api/ai/generate 엔드포인트
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import structlog
import asyncio

from app.services.scenario_chat_service import ScenarioChatService
from app.dto.response import success_response
from app.exceptions import GajiException, ErrorCode

logger = structlog.get_logger()

router = APIRouter(prefix="/api/ai", tags=["message-generation"])


class MessageHistory(BaseModel):
    """메시지 히스토리"""
    role: str
    content: str
    
    class Config:
        # Spring Boot에서 camelCase로 보내므로 alias 설정
        populate_by_name = True


class GenerationRequest(BaseModel):
    """AI 생성 요청"""
    conversation_id: str = Field(..., alias="conversationId", description="대화 ID")
    scenario_id: str = Field(..., alias="scenarioId", description="시나리오 ID")
    
    # What If 시나리오 정보
    what_if_question: Optional[str] = Field(None, alias="whatIfQuestion", description="What If 질문")
    character_changes: Optional[str] = Field(None, alias="characterChanges", description="캐릭터 변경사항")
    event_alterations: Optional[str] = Field(None, alias="eventAlterations", description="이벤트 변경사항")
    setting_modifications: Optional[str] = Field(None, alias="settingModifications", description="설정 변경사항")
    
    # 캐릭터 정보
    character_name: Optional[str] = Field(None, alias="characterName", description="캐릭터 이름")
    character_persona: Optional[str] = Field(None, alias="characterPersona", description="캐릭터 페르소나")
    character_speaking_style: Optional[str] = Field(None, alias="characterSpeakingStyle", description="캐릭터 말투")
    
    # 책 정보
    book_title: Optional[str] = Field(None, alias="bookTitle", description="책 제목")
    book_author: Optional[str] = Field(None, alias="bookAuthor", description="책 저자")
    
    scenario_context: str = Field(..., alias="scenarioContext", description="시나리오 컨텍스트")
    user_message: str = Field(..., alias="userMessage", description="사용자 메시지")
    history: Optional[List[MessageHistory]] = Field(default_factory=list, description="대화 히스토리")
    
    class Config:
        # Spring Boot에서 camelCase로 보내므로 alias 허용
        populate_by_name = True


async def process_ai_generation(
    conversation_id: str,
    scenario_id: str,
    what_if_question: Optional[str],
    character_changes: Optional[str],
    event_alterations: Optional[str],
    setting_modifications: Optional[str],
    character_name: Optional[str],
    character_persona: Optional[str],
    character_speaking_style: Optional[str],
    book_title: Optional[str],
    book_author: Optional[str],
    scenario_context: str,
    user_message: str,
    history: List[MessageHistory]
):
    """
    AI 생성 백그라운드 작업
    """
    import redis
    from app.config import settings
    
    try:
        # Redis에 초기 상태 저장
        redis_url = settings.get_redis_url()
        if redis_url:
            r = redis.Redis.from_url(redis_url, decode_responses=True)
            
            status_key = f"task:{conversation_id}:status"
            content_key = f"task:{conversation_id}:content"
            error_key = f"task:{conversation_id}:error"
            
            # 초기 상태 저장
            r.setex(status_key, 600, "processing")
            
            try:
                from app.services.base_chat_service import BaseChatService
                
                logger.info(
                    "Processing AI generation",
                    conversation_id=conversation_id,
                    has_character=bool(character_name),
                    has_book=bool(book_title)
                )
                
                # 프롬프트 생성 - Spring Boot에서 받은 데이터 사용
                # 캐릭터 정보가 있으면 상세 프롬프트, 없으면 기본 프롬프트
                if character_name and book_title:
                    system_prompt = f"""You are {character_name} from '{book_title}'.
"""
                    
                    if character_persona:
                        system_prompt += f"""
【Original Persona - CRITICAL】
{character_persona}
"""
                    
                    if character_speaking_style:
                        system_prompt += f"""
【Original Speaking Style - CRITICAL - MUST STRICTLY FOLLOW】
{character_speaking_style}

CRITICAL INSTRUCTION: Your speaking style is ESSENTIAL to your character identity. You MUST maintain the exact speaking style described above.
"""
                else:
                    system_prompt = """You are a character in a 'What If' scenario conversation.

"""
                    logger.warning(
                        "No character data available, using fallback prompt",
                        conversation_id=conversation_id
                    )
                
                # What If 시나리오 추가
                if what_if_question:
                    system_prompt += f"""
【What If Question - CRITICAL】
The core premise of this alternate timeline is: "{what_if_question}"

You MUST embody this alternate reality. Your responses must reflect how you would think, feel, and act in this changed timeline.
"""
                
                # 변경사항 추가
                if character_changes or event_alterations or setting_modifications:
                    system_prompt += "\n【Changes in this Timeline】\n"
                    if character_changes:
                        system_prompt += f"- Character Changes: {character_changes}\n"
                    if event_alterations:
                        system_prompt += f"- Event Alterations: {event_alterations}\n"
                    if setting_modifications:
                        system_prompt += f"- Setting Modifications: {setting_modifications}\n"
                
                system_prompt += """

【Response Guidelines】
- You must respond in Korean (한국어)
- Keep responses concise and natural (2-3 short paragraphs maximum, unless user specifically asks for detailed explanation)
- Respond naturally as if these changes are reality
- Avoid overly long or verbose responses unless requested
"""
                
                # BaseChatService로 직접 Gemini API 호출
                chat_service = BaseChatService()
                
                # 대화 히스토리를 Gemini API 형식으로 변환
                contents = []
                for msg in history:
                    # Gemini API는 "user"와 "model" 역할 사용
                    gemini_role = "model" if msg.role == "assistant" else "user"
                    contents.append({
                        "role": gemini_role,
                        "parts": [{"text": msg.content}]
                    })
                
                # 현재 사용자 메시지 추가
                contents.append({
                    "role": "user",
                    "parts": [{"text": user_message}]
                })
                
                logger.info(
                    "Calling Gemini API",
                    conversation_id=conversation_id,
                    history_count=len(history),
                    total_messages=len(contents)
                )
                
                response = chat_service._call_gemini_api(
                    contents=contents,
                    system_instruction=system_prompt,
                    model="gemini-2.5-flash",
                    temperature=0.8,
                    top_p=0.95,
                    max_output_tokens=1024  # 응답 길이 제한 (기존 4096에서 1024로)
                )
                
                result = chat_service._extract_response(response)
                ai_response = result.get("response", "")
                
                # Redis에 완료 상태 저장
                r.setex(status_key, 600, "completed")
                r.setex(content_key, 600, ai_response)
                
                logger.info(
                    "AI generation completed",
                    conversation_id=conversation_id,
                    response_length=len(ai_response)
                )
                
            except Exception as e:
                # 실패 상태 저장
                r.setex(status_key, 600, "failed")
                r.setex(error_key, 600, str(e))
                
                logger.error(
                    "AI generation failed",
                    conversation_id=conversation_id,
                    error=str(e),
                    exc_info=True
                )
                raise
        else:
            logger.warning(
                "Redis not configured, cannot save status",
                conversation_id=conversation_id
            )
            
    except Exception as e:
        logger.error(
            "Background task failed",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True
        )


@router.post("/generate", summary="AI 응답 생성 (Spring Boot 전용)")
async def generate_ai_response(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Spring Boot에서 호출하는 AI 응답 생성 엔드포인트
    
    비동기로 AI 응답을 생성하고 Redis에 상태를 저장합니다.
    Spring Boot는 폴링을 통해 결과를 확인합니다.
    """
    try:
        logger.info(
            "AI generation requested",
            conversation_id=request.conversation_id,
            scenario_id=request.scenario_id
        )
        
        # 백그라운드 태스크로 AI 생성 시작
        background_tasks.add_task(
            process_ai_generation,
            request.conversation_id,
            request.scenario_id,
            request.what_if_question,
            request.character_changes,
            request.event_alterations,
            request.setting_modifications,
            request.character_name,
            request.character_persona,
            request.character_speaking_style,
            request.book_title,
            request.book_author,
            request.scenario_context,
            request.user_message,
            request.history
        )
        
        return success_response(
            data={"status": "queued", "conversation_id": request.conversation_id},
            message="AI generation queued successfully"
        )
        
    except Exception as e:
        logger.error(
            "AI generation endpoint failed",
            conversation_id=request.conversation_id,
            error=str(e),
            exc_info=True
        )
        raise GajiException(
            ErrorCode.MESSAGE_GENERATION_FAILED,
            details={"error": str(e)}
        )

