"""
캐릭터 대화 API 라우터

책 속 인물과 대화하는 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from uuid import UUID
import json

from app.services.character_chat_service import CharacterChatService
from app.services.api_key_manager import get_api_key_manager

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

class ChatResponse(BaseModel):
    """대화 응답"""
    response: str
    character_name: str
    book_title: str
    grounding_metadata: Optional[Dict] = None

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
    service: CharacterChatService = Depends(get_character_service)
):
    """
    특정 캐릭터 상세 정보 조회
    
    Args:
        character_name: 캐릭터 이름
    
    Returns:
        캐릭터 상세 정보
    """
    try:
        character = service.get_character_info(character_name)
        if not character:
            raise HTTPException(
                status_code=404,
                detail=f"캐릭터를 찾을 수 없습니다: {character_name}"
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
        result = service.chat(
            character_name=request.character_name,
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.post("/chat/stream")
async def stream_chat_with_character(
    request: ChatRequest,
    service: CharacterChatService = Depends(get_character_service)
):
    """
    캐릭터와 스트리밍 대화
    
    Args:
        request: 대화 요청 (캐릭터 이름, 메시지, 대화 기록)
    
    Returns:
        Server-Sent Events 스트림
    """
    async def generate():
        try:
            for chunk in service.stream_chat(
                character_name=request.character_name,
                user_message=request.message,
                conversation_history=request.conversation_history
            ):
                if 'error' in chunk:
                    yield f"data: {json.dumps({'error': chunk['error']}, ensure_ascii=False)}\n\n"
                    break
                
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

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

