"""
캐릭터 대화 API 라우터

책 속 인물과 대화하는 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID
import json

from app.services.character_chat_service import CharacterChatService
from app.services.api_key_manager import get_api_key_manager
from app.services.character_data_loader import CharacterDataLoader
from app.utils.metrics import increment_request, increment_conversation

router = APIRouter(prefix="/api/ai", tags=["ai-conversation"])

# 요청/응답 모델
class CharacterListResponse(BaseModel):
    """캐릭터 목록 응답"""
    characters: List[Dict]
    total: int

class ChatRequest(BaseModel):
    """대화 요청"""
    character_name: str
    message: str
    conversation_history: Optional[List[Dict]] = None
    book_title: Optional[str] = None  # 책 제목 (같은 책의 여러 캐릭터 구분용)
    output_language: Optional[str] = "ko"  # 출력 언어 (기본값: "ko", 지원: "ko", "en", "ja", "zh" 등)
    scenario_id: Optional[str] = None  # 시나리오 ID (시나리오 기반 대화용)
    forked_scenario_id: Optional[str] = None  # Fork된 시나리오 ID
    conversation_id: Optional[str] = None  # 기존 대화 ID
    user_id: Optional[str] = None  # 사용자 ID (대화 저장용)
    conversation_partner_type: Optional[str] = Field(
        "stranger", 
        description="대화 상대 유형: 'stranger' (제3의 인물) 또는 'other_main_character' (다른 주인공)"
    )
    other_main_character: Optional[Dict] = Field(
        None,
        description="다른 주인공 정보 (conversation_partner_type이 'other_main_character'일 때 필수). character_name과 book_title 포함"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "character_name": "Sherlock Holmes",
                "message": "안녕하세요",
                "book_title": "The Adventures of Sherlock Holmes",
                "conversation_partner_type": "stranger",
                "other_main_character": None
            }
        }

class ChatResponse(BaseModel):
    """대화 응답"""
    response: str
    character_name: str
    book_title: str
    output_language: Optional[str] = None  # 사용된 출력 언어
    grounding_metadata: Optional[Dict] = None
    conversation_id: Optional[str] = None  # 임시 대화 ID (이어서 대화할 때 사용)
    turn_count: Optional[int] = None  # 현재 턴 수
    max_turns: Optional[int] = None  # 최대 턴 수

# 의존성: CharacterChatService 인스턴스
def get_character_service() -> CharacterChatService:
    """CharacterChatService 인스턴스 반환"""
    from app.services.api_key_manager import get_api_key_manager
    
    try:
        manager = get_api_key_manager()
        api_key = manager.get_current_key()
        return CharacterChatService(api_key=api_key)
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"API Key Manager 초기화 실패: {str(e)}"
        )

@router.get(
    "/characters",
    response_model=CharacterListResponse,
    summary="캐릭터 목록 조회",
    description="사용 가능한 모든 캐릭터 목록을 반환합니다."
)
async def list_characters(service: CharacterChatService = Depends(get_character_service)):
    """
    사용 가능한 캐릭터 목록 조회
    
    Returns:
        캐릭터 목록
    """
    try:
        characters = service.get_available_characters()
        return CharacterListResponse(
            characters=characters,
            total=len(characters)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐릭터 목록 조회 실패: {str(e)}")

@router.get(
    "/characters/{vectordb_id}",
    summary="캐릭터 정보 조회 (Internal API)",
    description="VectorDB ID로 특정 캐릭터의 상세 정보를 조회합니다."
)
async def get_character_by_vectordb_id(
    vectordb_id: str,
    service: CharacterChatService = Depends(get_character_service)
):
    """
    VectorDB ID로 캐릭터 정보 조회 (Internal API)
    
    Args:
        vectordb_id: VectorDB 캐릭터 ID
    
    Returns:
        캐릭터 상세 정보
    """
    try:
        # vectordb_id를 character_name으로 사용 (실제 구현에서는 VectorDB에서 조회)
        character = service.get_character_info(vectordb_id)
        if not character:
            raise HTTPException(
                status_code=404,
                detail=f"캐릭터를 찾을 수 없습니다: {vectordb_id}"
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐릭터 정보 조회 실패: {str(e)}")

@router.get(
    "/characters/info/{character_name}",
    summary="캐릭터 정보 조회 (이름으로)",
    description="특정 캐릭터의 상세 정보(페르소나, 말투, 배경 등)를 조회합니다."
)
async def get_character_info(
    character_name: str,
    book_title: Optional[str] = None,
    service: CharacterChatService = Depends(get_character_service)
):
    """
    특정 캐릭터 상세 정보 조회
    
    Args:
        character_name: 캐릭터 이름
        book_title: 책 제목 (선택, 같은 책의 여러 캐릭터 구분용)
    
    Returns:
        캐릭터 상세 정보
    """
    try:
        character = service.get_character_info(character_name, book_title)
        if not character:
            error_msg = f"캐릭터를 찾을 수 없습니다: {character_name}"
            if book_title:
                error_msg += f" (책: {book_title})"
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )
        return character
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"캐릭터 정보 조회 실패: {str(e)}")

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
    summary="AI 캐릭터와 대화",
    description="책 속 인물과 실시간 대화를 진행합니다. RAG + Gemini 2.5 Flash를 사용합니다."
)
async def send_message_to_ai_character(
    conversation_id: str,
    request: ChatRequest,
    service: CharacterChatService = Depends(get_character_service)
):
    """
    AI 캐릭터와 대화 (RAG + Gemini 2.5 Flash)
    
    Args:
        conversation_id: 대화 ID
        request: 대화 요청 (캐릭터 이름, 메시지, 대화 기록)
    
    Returns:
        캐릭터의 응답
    """
    try:
        # 메트릭: 요청 증가
        increment_request("/api/ai/conversations/{conversation_id}/messages", success=True)
        
        # 시나리오 기반 대화인지 확인
        if request.scenario_id:
            from app.services.scenario_chat_service import ScenarioChatService
            from app.services.scenario_management_service import ScenarioManagementService
            scenario_chat_service = ScenarioChatService()
            scenario_service = ScenarioManagementService()
            
            # 시나리오 정보 가져오기 (다른 주인공 찾기용)
            scenario = scenario_service.get_scenario(request.scenario_id)
            
            # 대화 상대 타입 처리
            conversation_partner_type = request.conversation_partner_type or "stranger"
            other_main_character = request.other_main_character
            
            # conversation_partner_type이 "other_main_character"인데 other_main_character가 없으면 자동으로 찾기
            if conversation_partner_type == "other_main_character" and not other_main_character and scenario:
                characters = CharacterDataLoader.load_characters()
                other_main_character = CharacterDataLoader.get_other_main_character(
                    characters,
                    scenario.get('character_name', ''),
                    scenario.get('book_title', '')
                )
                if not other_main_character:
                    # 다른 주인공이 없으면 제3의 인물로 변경
                    conversation_partner_type = "stranger"
            
            # 경로의 conversation_id를 우선 사용, 없으면 본문의 conversation_id 사용
            effective_conversation_id = conversation_id or request.conversation_id
            
            result = scenario_chat_service.chat_with_scenario(
                scenario_id=request.scenario_id,
                user_message=request.message,
                conversation_history=request.conversation_history,
                output_language=request.output_language,
                is_forked=request.forked_scenario_id is not None,
                forked_scenario_id=request.forked_scenario_id,
                conversation_id=effective_conversation_id,
                user_id=request.user_id or "default_user",
                conversation_partner_type=conversation_partner_type,
                other_main_character=other_main_character
            )
            
            # 메트릭: 시나리오 대화 증가
            increment_conversation("scenario")
            
            return ChatResponse(
                response=result["response"],
                character_name=result["character_name"],
                book_title=result["book_title"],
                output_language=result.get("output_language")
            )
        else:
            # 일반 대화
            # 대화 상대 타입 처리
            conversation_partner_type = request.conversation_partner_type or "stranger"
            other_main_character = request.other_main_character
            
            # conversation_partner_type이 "other_main_character"인데 other_main_character가 없으면 자동으로 찾기
            if conversation_partner_type == "other_main_character" and not other_main_character:
                characters = CharacterDataLoader.load_characters()
                other_main_character = CharacterDataLoader.get_other_main_character(
                    characters,
                    request.character_name,
                    request.book_title or ""
                )
                if not other_main_character:
                    # 다른 주인공이 없으면 제3의 인물로 변경
                    conversation_partner_type = "stranger"
            
            # 경로의 conversation_id를 우선 사용, 없으면 본문의 conversation_id 사용
            effective_conversation_id = conversation_id or request.conversation_id
            
            result = service.chat(
                character_name=request.character_name,
                user_message=request.message,
                conversation_history=request.conversation_history,
                book_title=request.book_title,
                output_language=request.output_language,
                conversation_partner_type=conversation_partner_type,
                other_main_character=other_main_character,
                conversation_id=effective_conversation_id
            )
            
            if 'error' in result:
                increment_request("/character/chat", success=False)
                # 할당량 초과 에러는 429로 반환
                if result.get('error_code') == 'QUOTA_EXCEEDED':
                    raise HTTPException(status_code=429, detail=result['error'])
                raise HTTPException(status_code=400, detail=result['error'])
            
            # 메트릭: 캐릭터 대화 증가
            increment_conversation("character")
            
            # ChatResponse에 맞게 변환 (conversation_id, turn_count, max_turns 포함)
            return ChatResponse(
                response=result.get('response', ''),
                character_name=result.get('character_name', ''),
                book_title=result.get('book_title', ''),
                output_language=result.get('output_language'),
                grounding_metadata=result.get('grounding_metadata'),
                conversation_id=result.get('conversation_id'),
                turn_count=result.get('turn_count'),
                max_turns=result.get('max_turns')
            )
        
    except HTTPException:
        increment_request("/api/ai/conversations/{conversation_id}/messages", success=False)
        raise
    except Exception as e:
        increment_request("/api/ai/conversations/{conversation_id}/messages", success=False)
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.get(
    "/health",
    tags=["health"],
    summary="캐릭터 채팅 서비스 헬스 체크",
    description="캐릭터 채팅 서비스의 상태를 확인합니다."
)
async def health_check():
    """헬스 체크"""
    try:
        manager = get_api_key_manager()
        return {
            "status": "healthy",
            "service": "character-chat",
            "api_key_status": manager.get_status()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "character-chat",
            "error": str(e)
        }

