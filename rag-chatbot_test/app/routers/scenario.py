"""
시나리오 API 라우터

What if 시나리오 생성, 조회, Fork 기능을 제공하는 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.scenario_management_service import ScenarioManagementService
from app.services.scenario_chat_service import ScenarioChatService

router = APIRouter(prefix="/scenario", tags=["scenario"])

# 요청/응답 모델
class ScenarioCreateRequest(BaseModel):
    """시나리오 생성 요청"""
    scenario_name: str
    book_title: str
    character_name: str
    is_public: bool = False
    character_property_changes: Optional[Dict] = None
    event_alterations: Optional[Dict] = None
    setting_modifications: Optional[Dict] = None

class FirstConversationRequest(BaseModel):
    """첫 대화 요청"""
    initial_message: str
    conversation_id: Optional[str] = None

class FirstConversationContinueRequest(BaseModel):
    """첫 대화 계속 요청"""
    conversation_id: str
    message: str

class FirstConversationConfirmRequest(BaseModel):
    """첫 대화 컨펌 요청"""
    conversation_id: str
    action: str  # "save" or "cancel"

class ForkRequest(BaseModel):
    """Fork 요청"""
    initial_message: str

class ForkConversationConfirmRequest(BaseModel):
    """Fork된 시나리오 대화 컨펌 요청"""
    conversation_id: str
    action: str  # "save" or "cancel"

# 의존성: 싱글톤 인스턴스
_scenario_service_instance = None
_scenario_chat_service_instance = None

def get_scenario_service() -> ScenarioManagementService:
    """ScenarioManagementService 싱글톤 인스턴스 반환"""
    global _scenario_service_instance
    if _scenario_service_instance is None:
        _scenario_service_instance = ScenarioManagementService()
    return _scenario_service_instance

def get_scenario_chat_service() -> ScenarioChatService:
    """ScenarioChatService 싱글톤 인스턴스 반환"""
    global _scenario_chat_service_instance
    if _scenario_chat_service_instance is None:
        _scenario_chat_service_instance = ScenarioChatService()
    return _scenario_chat_service_instance

@router.post("/create")
async def create_scenario(
    request: ScenarioCreateRequest,
    creator_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    service: ScenarioManagementService = Depends(get_scenario_service)
):
    """
    시나리오 생성
    
    Args:
        request: 시나리오 생성 요청
        creator_id: 생성자 ID (임시, 실제로는 인증에서 가져옴)
    
    Returns:
        생성된 시나리오 정보
    """
    try:
        descriptions = {
            "character_property_changes": request.character_property_changes or {"enabled": False},
            "event_alterations": request.event_alterations or {"enabled": False},
            "setting_modifications": request.setting_modifications or {"enabled": False}
        }
        
        result = service.create_scenario(
            scenario_name=request.scenario_name,
            book_title=request.book_title,
            character_name=request.character_name,
            descriptions=descriptions,
            creator_id=creator_id,
            is_public=request.is_public
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시나리오 생성 실패: {str(e)}")

@router.post("/{scenario_id}/first-conversation")
async def start_first_conversation(
    scenario_id: str,
    request: FirstConversationRequest,
    creator_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    첫 대화 시작 (원본 시나리오 생성자용)
    
    Args:
        scenario_id: 시나리오 ID
        request: 첫 대화 요청
        creator_id: 생성자 ID
    
    Returns:
        대화 응답
    """
    try:
        result = chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=request.initial_message,
            output_language="ko",
            is_creator=True,
            conversation_id=request.conversation_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.post("/{scenario_id}/first-conversation/continue")
async def continue_first_conversation(
    scenario_id: str,
    request: FirstConversationContinueRequest,
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    첫 대화 계속 (턴 2~5)
    
    Args:
        scenario_id: 시나리오 ID
        request: 대화 계속 요청
    
    Returns:
        대화 응답
    """
    try:
        result = chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=request.message,
            output_language="ko",
            is_creator=True,
            conversation_id=request.conversation_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.post("/{scenario_id}/fork/{forked_scenario_id}/continue")
async def continue_forked_conversation(
    scenario_id: str,
    forked_scenario_id: str,
    request: FirstConversationContinueRequest,
    user_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    Fork된 시나리오 대화 계속 (턴 2~5)
    
    Args:
        scenario_id: 원본 시나리오 ID
        forked_scenario_id: Fork된 시나리오 ID
        request: 대화 계속 요청
        user_id: 사용자 ID
    
    Returns:
        대화 응답
    """
    try:
        # 원본 시나리오 로드 (first_conversation 참조용)
        from app.services.scenario_management_service import ScenarioManagementService
        service = ScenarioManagementService()
        original_scenario = service.get_scenario(scenario_id)
        if not original_scenario:
            raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        result = chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=request.message,
            output_language="ko",
            is_creator=False,
            conversation_id=request.conversation_id,
            original_first_conversation=original_scenario.get("first_conversation")
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.post("/{scenario_id}/first-conversation/confirm")
async def confirm_first_conversation(
    scenario_id: str,
    request: FirstConversationConfirmRequest,
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    첫 대화 최종 컨펌 (5턴 완료 후)
    
    Args:
        scenario_id: 시나리오 ID
        request: 컨펌 요청
    
    Returns:
        컨펌 결과
    """
    try:
        if request.action not in ["save", "cancel"]:
            raise HTTPException(status_code=400, detail="action은 'save' 또는 'cancel'이어야 합니다.")
        
        result = chat_service.confirm_first_conversation(
            scenario_id=scenario_id,
            conversation_id=request.conversation_id,
            action=request.action
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨펌 실패: {str(e)}")

@router.get("/public")
async def get_public_scenarios(
    book_title: Optional[str] = None,
    character_name: Optional[str] = None,
    sort: str = "popular",
    service: ScenarioManagementService = Depends(get_scenario_service)
):
    """
    공개 시나리오 목록 조회
    
    Args:
        book_title: 책 제목 필터
        character_name: 캐릭터 이름 필터
        sort: 정렬 방식 ("popular", "recent")
    
    Returns:
        공개 시나리오 목록
    """
    try:
        scenarios = service.get_public_scenarios(
            book_title=book_title,
            character_name=character_name,
            sort=sort
        )
        return {
            "scenarios": scenarios,
            "total": len(scenarios)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시나리오 목록 조회 실패: {str(e)}")

@router.get("/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    user_id: Optional[str] = None,
    service: ScenarioManagementService = Depends(get_scenario_service)
):
    """
    시나리오 상세 조회 (Fork 전 미리보기)
    
    Args:
        scenario_id: 시나리오 ID
        user_id: 사용자 ID (비공개 시나리오 조회용)
    
    Returns:
        시나리오 상세 정보
    """
    try:
        scenario = service.get_scenario(scenario_id, user_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        # can_fork 확인 (임시로 항상 True)
        scenario["can_fork"] = True
        
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시나리오 조회 실패: {str(e)}")

@router.post("/{scenario_id}/fork")
async def fork_scenario(
    scenario_id: str,
    request: ForkRequest,
    user_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    service: ScenarioManagementService = Depends(get_scenario_service),
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    시나리오 Fork
    
    Args:
        scenario_id: 원본 시나리오 ID
        request: Fork 요청
        user_id: 사용자 ID
    
    Returns:
        Fork된 시나리오 정보 및 첫 응답
    """
    try:
        # 원본 시나리오 로드 (first_conversation 참조용)
        original_scenario = service.get_scenario(scenario_id)
        if not original_scenario:
            raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        # Fork 실행
        forked_scenario = service.fork_scenario(scenario_id, user_id)
        forked_scenario_id = forked_scenario["forked_scenario_id"]
        
        # 첫 대화 시작 (원본 first_conversation 참조)
        result = chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=request.initial_message,
            output_language="ko",
            is_creator=False,
            conversation_id=None,
            original_first_conversation=original_scenario.get("first_conversation")
        )
        
        return {
            "forked_scenario_id": forked_scenario_id,
            "original_scenario_id": scenario_id,
            "response": result["response"],
            "message": "시나리오를 fork했습니다. 대화를 시작하세요.",
            "conversation_id": result["conversation_id"],
            "turn_count": result["turn_count"],
            "max_turns": result["max_turns"],
            "is_regenerable": False,
            "is_saved": False,  # 임시 저장소에 저장됨, 최종 컨펌 필요
            "is_temporary": True
        }
    except HTTPException:
        # Re-raise HTTPException (e.g., 404 from get_scenario)
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fork 실패: {str(e)}")

@router.post("/{scenario_id}/fork/{forked_scenario_id}/confirm-conversation")
async def confirm_forked_conversation(
    scenario_id: str,
    forked_scenario_id: str,
    request: ForkConversationConfirmRequest,
    user_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    Fork된 시나리오 대화 최종 컨펌 (5턴 완료 후)
    
    Args:
        scenario_id: 원본 시나리오 ID
        forked_scenario_id: Fork된 시나리오 ID
        request: 컨펌 요청
        user_id: 사용자 ID
    
    Returns:
        컨펌 결과
    """
    try:
        if request.action not in ["save", "cancel"]:
            raise HTTPException(status_code=400, detail="action은 'save' 또는 'cancel'이어야 합니다.")
        
        result = chat_service.confirm_forked_conversation(
            forked_scenario_id=forked_scenario_id,
            conversation_id=request.conversation_id,
            action=request.action,
            user_id=user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨펌 실패: {str(e)}")


