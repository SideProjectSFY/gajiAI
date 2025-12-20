"""
시나리오 API 라우터

What if 시나리오 생성, 조회, Fork 기능을 제공하는 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json

from app.services.scenario_management_service import ScenarioManagementService
from app.services.scenario_chat_service import ScenarioChatService
from app.services.character_data_loader import CharacterDataLoader
from app.utils.metrics import increment_request, increment_scenario_created, increment_scenario_forked, increment_conversation

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

# 요청/응답 모델
class ChangeDescription(BaseModel):
    """변경사항 설명 모델"""
    enabled: bool = Field(..., description="변경사항 활성화 여부")
    description: Optional[str] = Field(None, description="변경사항 자연어 설명 (enabled가 true일 때 필수)")

class ScenarioCreateRequest(BaseModel):
    """시나리오 생성 요청"""
    scenario_name: str = Field(..., description="시나리오 이름")
    book_title: str = Field(..., description="책 제목")
    character_name: str = Field(..., description="캐릭터 이름")
    is_public: bool = Field(False, description="공개 여부")
    character_property_changes: Optional[ChangeDescription] = Field(
        None, 
        description="캐릭터 속성 변경 설명 (null이면 사용 안 함)"
    )
    event_alterations: Optional[ChangeDescription] = Field(
        None, 
        description="사건 변경 설명 (null이면 사용 안 함)"
    )
    setting_modifications: Optional[ChangeDescription] = Field(
        None, 
        description="배경 변경 설명 (null이면 사용 안 함)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenario_name": "셜록홈즈가 현대사회에서 활동한다면?",
                "book_title": "The Adventures of Sherlock Holmes",
                "character_name": "Sherlock Holmes",
                "is_public": True,
                "character_property_changes": {
                    "enabled": True,
                    "description": "이성적이고 논리적인 추리를 중시하지만 사람의 감정 역시 추리에 중요한 요소라고 생각한다."
                },
                "event_alterations": None,
                "setting_modifications": {
                    "enabled": True,
                    "description": "2025년 한국 현대사회를 배경으로 최신 과학기술들을 사용한다."
                }
            }
        }

class ScenarioChatRequest(BaseModel):
    """시나리오 대화 요청 (원본 시나리오용)"""
    message: Optional[str] = Field(
        None,
        description="대화 메시지 (action이 없을 때 필수, action이 있으면 무시됨)"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="임시 대화 ID (이어서 대화할 때 사용, 없으면 새 대화 시작)"
    )
    action: Optional[str] = Field(
        None,
        description="액션: 'save' 또는 'cancel' (5턴 완료 후 최종 저장/취소, action이 있으면 message는 무시됨)"
    )
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
                "message": "안녕하세요",
                "conversation_id": None,
                "conversation_partner_type": "stranger",
                "other_main_character": None
            }
        }

class ForkedScenarioChatRequest(BaseModel):
    """Fork된 시나리오 대화 요청 (conversation_partner_type은 Fork 시 저장된 값 사용)"""
    message: Optional[str] = Field(
        None,
        description="대화 메시지 (action이 없을 때 필수, action이 있으면 무시됨)"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="임시 대화 ID (이어서 대화할 때 사용, 없으면 새 대화 시작)"
    )
    action: Optional[str] = Field(
        None,
        description="액션: 'save' 또는 'cancel' (5턴 완료 후 최종 저장/취소, action이 있으면 message는 무시됨)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "안녕하세요",
                "conversation_id": None
            }
        }

class ForkRequest(BaseModel):
    """Fork 요청 (시나리오 복사만 처리, 대화는 별도 엔드포인트에서 처리)"""
    conversation_partner_type: str = Field(
        ...,
        description="대화 상대 유형: 'stranger' (제3의 인물) 또는 'other_main_character' (다른 주인공)"
    )
    other_main_character: Optional[Dict] = Field(
        None,
        description="다른 주인공 정보 (conversation_partner_type이 'other_main_character'일 때 필수). character_name과 book_title 포함"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_partner_type": "stranger",
                "other_main_character": None
            }
        }


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

@router.post(
    "",
    summary="시나리오 생성",
    description="What If 시나리오를 생성합니다. 캐릭터 속성, 사건, 배경 중 하나 이상을 변경해야 합니다."
)
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
    
    Note:
        변경사항이 없는 시나리오는 생성할 수 없습니다.
        기본 캐릭터 대화는 /character/chat 엔드포인트를 사용하세요.
    """
    try:
        # 메트릭: 요청 증가
        increment_request("/scenario/create", success=True)
        
        # 변경사항이 있는지 확인
        has_any_changes = (
            (request.character_property_changes and request.character_property_changes.enabled) or
            (request.event_alterations and request.event_alterations.enabled) or
            (request.setting_modifications and request.setting_modifications.enabled)
        )
        
        if not has_any_changes:
            raise HTTPException(
                status_code=400,
                detail="변경사항이 있는 시나리오만 생성할 수 있습니다. 기본 캐릭터 대화는 /character/chat 엔드포인트를 사용하세요."
            )
        
        # Pydantic 모델을 딕셔너리로 변환
        descriptions = {
            "character_property_changes": (
                request.character_property_changes.model_dump() 
                if request.character_property_changes 
                else {"enabled": False}
            ),
            "event_alterations": (
                request.event_alterations.model_dump() 
                if request.event_alterations 
                else {"enabled": False}
            ),
            "setting_modifications": (
                request.setting_modifications.model_dump() 
                if request.setting_modifications 
                else {"enabled": False}
            )
        }
        
        result = service.create_scenario(
            scenario_name=request.scenario_name,
            book_title=request.book_title,
            character_name=request.character_name,
            descriptions=descriptions,
            creator_id=creator_id,
            is_public=request.is_public
        )
        
        # 메트릭: 시나리오 생성 증가
        increment_scenario_created()
        
        return result
    except Exception as e:
        increment_request("/api/scenarios", success=False)
        raise HTTPException(status_code=500, detail=f"시나리오 생성 실패: {str(e)}")

@router.post(
    "/{scenario_id}/chat",
    summary="시나리오 대화 (FastAPI 내부)",
    description="시나리오 기반 대화를 진행합니다. 첫 대화 시작, 대화 이어가기, 저장/취소 기능을 제공합니다. (참고: 실제 대화는 POST /api/ai/conversations/{conversation_id}/messages 사용)"
)
async def scenario_chat(
    scenario_id: str,
    request: ScenarioChatRequest,
    creator_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    service: ScenarioManagementService = Depends(get_scenario_service),
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    시나리오 대화 (통합 엔드포인트)
    
    - action이 없고 conversation_id가 없으면: 첫 대화 시작
    - action이 없고 conversation_id가 있으면: 대화 이어가기
    - action이 있으면: 저장/취소 처리 (5턴 완료 후)
    
    Args:
        scenario_id: 시나리오 ID
        request: 대화 요청
        creator_id: 생성자 ID
    
    Returns:
        대화 응답 또는 컨펌 결과
    """
    try:
        # 메트릭: 요청 증가
        increment_request("/api/scenarios/{scenario_id}/chat", success=True)
        
        # action이 있으면 저장/취소 처리
        if request.action:
            if request.action not in ["save", "cancel"]:
                raise HTTPException(status_code=400, detail="action은 'save' 또는 'cancel'이어야 합니다.")
            
            if not request.conversation_id:
                raise HTTPException(status_code=400, detail="action을 사용할 때는 conversation_id가 필수입니다.")
            
            result = chat_service.confirm_first_conversation(
                scenario_id=scenario_id,
                conversation_id=request.conversation_id,
                action=request.action
            )
            return result
        
        # action이 없으면 대화 처리
        if not request.message:
            raise HTTPException(status_code=400, detail="message가 필요합니다.")
        
        # 시나리오 조회 및 생성자 검증
        scenario = service.get_scenario(scenario_id, user_id=creator_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        # 생성자 검증 (공개 시나리오는 제외)
        if not scenario.get('is_public', False) and scenario.get('creator_id') != creator_id:
            raise HTTPException(
                status_code=403, 
                detail=f"이 시나리오에 대한 접근 권한이 없습니다. 생성자만 접근할 수 있습니다."
            )
        
        # 대화 상대 타입 처리
        conversation_partner_type = request.conversation_partner_type
        other_main_character = request.other_main_character
        
        # 기존 first_conversation이 있으면 그 설정을 우선 사용 (이어서 대화할 때)
        if request.conversation_id:
            # 임시 대화 파일에서 설정 가져오기
            temp_conv_file = chat_service.temp_conversations_dir / f"{request.conversation_id}.json"
            if temp_conv_file.exists():
                with open(temp_conv_file, 'r', encoding='utf-8') as f:
                    temp_conv = json.load(f)
                if conversation_partner_type is None:
                    conversation_partner_type = temp_conv.get("conversation_partner_type", "stranger")
                if other_main_character is None:
                    other_main_character = temp_conv.get("other_main_character")
        
        # 여전히 없으면 기본값 또는 자동 찾기
        if conversation_partner_type is None:
            conversation_partner_type = "stranger"
        
        if conversation_partner_type == "other_main_character" and not other_main_character:
            characters = CharacterDataLoader.load_characters()
            other_main_character = CharacterDataLoader.get_other_main_character(
                characters,
                scenario.get('character_name', ''),
                scenario.get('book_title', '')
            )
            if not other_main_character:
                # 다른 주인공이 없으면 제3의 인물로 변경
                conversation_partner_type = "stranger"
        
        # 대화 처리
        result = await chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=request.message,
            output_language="ko",
            is_creator=True,
            conversation_id=request.conversation_id,
            conversation_partner_type=conversation_partner_type,
            other_main_character=other_main_character
        )
        
        # 메트릭: 시나리오 대화 증가
        increment_conversation("scenario")
        
        return result
        
    except HTTPException:
        increment_request("/api/scenarios/{scenario_id}/chat", success=False)
        raise
    except ValueError as e:
        increment_request("/api/scenarios/{scenario_id}/chat", success=False)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        increment_request("/api/scenarios/{scenario_id}/chat", success=False)
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.post("/{scenario_id}/fork/{forked_scenario_id}/chat")
async def forked_scenario_chat(
    forked_scenario_id: str,
    request: ForkedScenarioChatRequest,
    user_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    chat_service: ScenarioChatService = Depends(get_scenario_chat_service)
):
    """
    Fork된 시나리오 대화 (통합 엔드포인트)
    
    - action이 없고 conversation_id가 없으면: 첫 대화 시작
    - action이 없고 conversation_id가 있으면: 대화 이어가기
    - action이 있으면: 저장/취소 처리 (5턴 완료 후)
    
    Args:
        forked_scenario_id: Fork된 시나리오 ID
        request: 대화 요청
        user_id: 사용자 ID
    
    Returns:
        대화 응답 또는 컨펌 결과
    """
    try:
        # 메트릭: 요청 증가
        increment_request("/api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat", success=True)
        
        # action이 있으면 저장/취소 처리
        if request.action:
            if request.action not in ["save", "cancel"]:
                raise HTTPException(status_code=400, detail="action은 'save' 또는 'cancel'이어야 합니다.")
            
            if not request.conversation_id:
                raise HTTPException(status_code=400, detail="action을 사용할 때는 conversation_id가 필수입니다.")
            
            result = chat_service.confirm_forked_conversation(
                forked_scenario_id=forked_scenario_id,
                conversation_id=request.conversation_id,
                action=request.action,
                user_id=user_id
            )
            return result
        
        # action이 없으면 대화 처리
        if not request.message:
            raise HTTPException(status_code=400, detail="message가 필요합니다.")
        
        # Fork된 시나리오 로드
        forked_scenario_file = chat_service.project_root / "data" / "scenarios" / "forked" / user_id / f"{forked_scenario_id}.json"
        if not forked_scenario_file.exists():
            raise HTTPException(status_code=404, detail=f"Fork된 시나리오를 찾을 수 없습니다: {forked_scenario_id}")
        
        with open(forked_scenario_file, 'r', encoding='utf-8') as f:
            forked_scenario = json.load(f)
        
        # Fork된 시나리오에서 원본 시나리오 ID 가져오기 (first_conversation 호출 시 사용)
        scenario_id = forked_scenario.get("original_scenario_id")
        if not scenario_id:
            raise HTTPException(status_code=400, detail="Fork된 시나리오에 원본 시나리오 ID가 없습니다.")
        
        # Fork 시 저장된 conversation_partner_type 사용 (요청에서 받지 않음)
        # reference_first_conversation이 있으면 그 안에 conversation_partner_type이 있음
        reference_first_conv = forked_scenario.get("reference_first_conversation")
        conversation_partner_type = forked_scenario.get("conversation_partner_type")
        other_main_character = forked_scenario.get("other_main_character")
        
        # reference_first_conversation이 있으면 그 안의 값 사용
        if reference_first_conv:
            conversation_partner_type = reference_first_conv.get("conversation_partner_type", "stranger")
            other_main_character = reference_first_conv.get("other_main_character")
        
        # 기본값 설정
        if not conversation_partner_type:
            conversation_partner_type = "stranger"
        
        # other_main_character 자동 찾기 (필요한 경우)
        if conversation_partner_type == "other_main_character" and not other_main_character:
            characters = CharacterDataLoader.load_characters()
            other_main_character = CharacterDataLoader.get_other_main_character(
                characters,
                forked_scenario.get('character_name', ''),
                forked_scenario.get('book_title', '')
            )
            if not other_main_character:
                # 다른 주인공이 없으면 제3의 인물로 변경
                conversation_partner_type = "stranger"
        
        # 대화 처리
        # reference_first_conversation이 있으면 그것을 사용, 없으면 None (기존 대화 맥락 사용 안 함)
        result = await chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=request.message,
            output_language="ko",
            is_creator=False,
            conversation_id=request.conversation_id,
            reference_first_conversation=reference_first_conv,
            conversation_partner_type=conversation_partner_type,
            other_main_character=other_main_character
        )
        
        # 메트릭: 시나리오 대화 증가
        increment_conversation("scenario")
        
        return result
        
    except HTTPException:
        increment_request("/api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat", success=False)
        raise
    except ValueError as e:
        increment_request("/api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat", success=False)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        increment_request("/api/scenarios/{scenario_id}/fork/{forked_scenario_id}/chat", success=False)
        raise HTTPException(status_code=500, detail=f"대화 생성 실패: {str(e)}")

@router.get(
    "",
    summary="시나리오 목록 조회",
    description="시나리오 목록을 조회합니다. 책 제목, 캐릭터 이름, 시나리오 타입으로 필터링할 수 있습니다."
)
async def list_scenarios(
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

@router.get(
    "/{id}",
    summary="시나리오 상세 조회",
    description="시나리오의 상세 정보를 조회합니다. Fork 전 미리보기로 사용할 수 있습니다."
)
async def get_scenario(
    id: str,
    user_id: Optional[str] = None,
    service: ScenarioManagementService = Depends(get_scenario_service)
):
    """
    시나리오 상세 조회 (Fork 전 미리보기)
    
    Args:
        id: 시나리오 ID
        user_id: 사용자 ID (비공개 시나리오 조회용)
    
    Returns:
        시나리오 상세 정보
    """
    try:
        scenario = service.get_scenario(id, user_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {id}")
        
        # can_fork 확인 (임시로 항상 True)
        scenario["can_fork"] = True
        
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시나리오 조회 실패: {str(e)}")

@router.post(
    "/{id}/fork",
    summary="시나리오 Fork",
    description="다른 사용자의 시나리오를 기반으로 새로운 시나리오를 생성합니다."
)
async def fork_scenario(
    id: str,
    request: ForkRequest,
    user_id: str = "default_user",  # TODO: 실제 인증에서 가져오기
    service: ScenarioManagementService = Depends(get_scenario_service)
):
    """
    시나리오 Fork (시나리오 복사만 처리)
    
    Args:
        id: 원본 시나리오 ID
        request: Fork 요청
        user_id: 사용자 ID
    
    Returns:
        Fork된 시나리오 정보
    """
    try:
        # 메트릭: 요청 증가
        increment_request("/api/scenarios/{id}/fork", success=True)
        
        # 원본 시나리오 확인
        original_scenario = service.get_scenario(id)
        if not original_scenario:
            raise HTTPException(status_code=404, detail=f"시나리오를 찾을 수 없습니다: {id}")
        
        # other_main_character 자동 찾기 (필요한 경우)
        other_main_character = request.other_main_character
        if request.conversation_partner_type == "other_main_character" and not other_main_character:
            characters = CharacterDataLoader.load_characters()
            other_main_character = CharacterDataLoader.get_other_main_character(
                characters,
                original_scenario.get('character_name', ''),
                original_scenario.get('book_title', '')
            )
            if not other_main_character:
                raise HTTPException(
                    status_code=400, 
                    detail="다른 주인공을 찾을 수 없습니다. conversation_partner_type을 'stranger'로 변경하거나 other_main_character를 명시해주세요."
                )
        
        # Fork 실행 (시나리오 복사만)
        forked_scenario = service.fork_scenario(
            scenario_id=id,
            user_id=user_id,
            conversation_partner_type=request.conversation_partner_type,
            other_main_character=other_main_character
        )
        forked_scenario_id = forked_scenario["forked_scenario_id"]
        
        # 메트릭: 시나리오 Fork 증가
        increment_scenario_forked()
        
        return {
            "id": forked_scenario_id,
            "base_story": original_scenario.get("book_title", ""),
            "parent_scenario_id": id,
            "scenario_type": original_scenario.get("scenario_type", "CHARACTER_CHANGE"),
            "parameters": original_scenario.get("parameters", {}),
            "quality_score": 0.0,
            "creator_id": user_id,
            "fork_count": 0,
            "created_at": forked_scenario.get("created_at", "")
        }
    except ValueError as e:
        increment_request("/api/scenarios/{id}/fork", success=False)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        increment_request("/api/scenarios/{id}/fork", success=False)
        raise HTTPException(status_code=500, detail=f"Fork 실패: {str(e)}")



