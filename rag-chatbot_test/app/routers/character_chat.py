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

router = APIRouter(prefix="/character", tags=["character-chat"])

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

@router.get("/list", response_model=CharacterListResponse)
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

@router.get("/info/{character_name}")
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

@router.post("/chat", response_model=ChatResponse)
async def chat_with_character(
    request: ChatRequest,
    service: CharacterChatService = Depends(get_character_service)
):
    """
    캐릭터와 대화
    
    Args:
        request: 대화 요청 (캐릭터 이름, 메시지, 대화 기록)
    
    Returns:
        캐릭터의 응답
    """
    try:
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
            
            result = scenario_chat_service.chat_with_scenario(
                scenario_id=request.scenario_id,
                user_message=request.message,
                conversation_history=request.conversation_history,
                output_language=request.output_language,
                is_forked=request.forked_scenario_id is not None,
                forked_scenario_id=request.forked_scenario_id,
                conversation_id=request.conversation_id,
                user_id=request.user_id or "default_user",
                conversation_partner_type=conversation_partner_type,
                other_main_character=other_main_character
            )
            
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
            
            result = service.chat(
                character_name=request.character_name,
                user_message=request.message,
                conversation_history=request.conversation_history,
                book_title=request.book_title,
                output_language=request.output_language,
                conversation_partner_type=conversation_partner_type,
                other_main_character=other_main_character,
                conversation_id=request.conversation_id
            )
            
            if 'error' in result:
                raise HTTPException(status_code=400, detail=result['error'])
            
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
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.get("/health")
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

