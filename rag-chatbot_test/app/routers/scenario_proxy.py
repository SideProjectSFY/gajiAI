from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBearer
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
import httpx
import structlog
import json

from app.services.spring_boot_client import spring_boot_client
from app.services.scenario_management_service import ScenarioManagementService
from app.middleware.jwt_auth import jwt_auth, get_jwt_token, security
from app.exceptions import (
    GajiException, 
    ErrorCode, 
    ServiceUnavailableException,
    NotFoundException
)
from app.dto.response import success_response

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios-proxy"])
internal_router = APIRouter(prefix="/api/internal/scenarios", tags=["internal-scenarios"])

class ScenarioCreateProxyRequest(BaseModel):
    novelId: UUID
    scenarioTitle: str = Field(..., max_length=255)
    baseScenarioId: Optional[UUID] = None
    characterChanges: Optional[str] = None
    eventAlterations: Optional[str] = None
    settingModifications: Optional[str] = None
    description: Optional[str] = Field(None, max_length=5000)
    whatIfQuestion: Optional[str] = Field(None, max_length=2000)
    isPrivate: bool = False
    scenarioType: Optional[str] = None

@router.post("/analyze", summary="시나리오 분석 (Gemini 분석만 수행, 저장하지 않음)")
async def analyze_scenario(
    request: ScenarioCreateProxyRequest,
    req: Request,
    user: dict = Depends(jwt_auth)
):
    """
    시나리오 분석 요청 처리 (저장하지 않음)
    
    - FastAPI에서 Gemini를 사용하여 자연어 설명을 구조화된 데이터로 분석
    - 분석 결과만 반환 (Spring Boot에서 저장)
    """
    try:
        jwt_token = get_jwt_token(req)
        user_id = user.get("sub")
        
        # Novel 정보 조회 (book_title, character_name 필요)
        novel_data = await spring_boot_client.get_novel(str(request.novelId), jwt_token)
        book_title = novel_data.get("title") if novel_data else None
        
        if not book_title:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": f"Novel not found: {request.novelId}"}
            )
        
        # 캐릭터 정보 조회 (character_name 필요)
        characters_list = await spring_boot_client.get_characters_by_novel(str(request.novelId), jwt_token)
        if not characters_list:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": f"No characters found for novel: {request.novelId}"}
            )
        
        # 주인공 캐릭터 우선 선택
        main_characters = [c for c in characters_list if c.get("isMainCharacter")]
        character_data = main_characters[0] if main_characters else characters_list[0]
        character_name = character_data.get("commonName")
        
        if not character_name:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": "Character name not found"}
            )
        
        # Gemini를 사용하여 자연어 설명을 구조화된 데이터로 분석
        scenario_service = ScenarioManagementService()
        analyzed_data = {}
        
        # 캐릭터 속성 변경 분석
        if request.characterChanges:
            try:
                parsed = scenario_service._parse_character_property_changes(
                    request.characterChanges,
                    book_title,
                    character_name
                )
                analyzed_data["characterChanges"] = json.dumps(parsed, ensure_ascii=False)
            except Exception as e:
                logger.warning("character_changes_analysis_failed", error=str(e))
                analyzed_data["characterChanges"] = request.characterChanges
        
        # 사건 변경 분석
        if request.eventAlterations:
            try:
                parsed = scenario_service._parse_event_alterations(
                    request.eventAlterations,
                    book_title
                )
                analyzed_data["eventAlterations"] = json.dumps(parsed, ensure_ascii=False)
            except Exception as e:
                logger.warning("event_alterations_analysis_failed", error=str(e))
                analyzed_data["eventAlterations"] = request.eventAlterations
        
        # 배경 변경 분석
        if request.settingModifications:
            try:
                parsed = scenario_service._parse_setting_modifications(
                    request.settingModifications,
                    book_title
                )
                analyzed_data["settingModifications"] = json.dumps(parsed, ensure_ascii=False)
            except Exception as e:
                logger.warning("setting_modifications_analysis_failed", error=str(e))
                analyzed_data["settingModifications"] = request.settingModifications
        
        return success_response(
            data=analyzed_data,
            message="Scenario analyzed successfully"
        )
        
    except httpx.HTTPStatusError as e:
        logger.error("spring_boot_api_error", status_code=e.response.status_code, error=str(e))
        raise GajiException(
            ErrorCode.SCENARIO_CREATION_FAILED,
            details={"error": f"Spring Boot API error: {e.response.status_code}"}
        )
    except Exception as e:
        logger.error("scenario_analysis_failed", error=str(e))
        raise GajiException(
            ErrorCode.SCENARIO_CREATION_FAILED,
            details={"error": f"Scenario analysis failed: {str(e)}"}
        )

@router.post("", summary="시나리오 생성 (Gemini 분석 + Spring Boot 저장)")
async def create_scenario_proxy(
    request: ScenarioCreateProxyRequest,
    req: Request,
    user: dict = Depends(jwt_auth)
):
    """
    시나리오 생성 요청 처리
    
    - FastAPI에서 Gemini를 사용하여 자연어 설명을 구조화된 데이터로 분석
    - 분석 결과를 Spring Boot로 전달하여 PostgreSQL에 저장
    """
    try:
        jwt_token = get_jwt_token(req)
        user_id = user.get("sub")
        
        logger.info(
            "scenario_create_proxy",
            user_id=user_id,
            novel_id=str(request.novelId),
            has_character_changes=bool(request.characterChanges),
            has_event_alterations=bool(request.eventAlterations),
            has_setting_modifications=bool(request.settingModifications)
        )
        
        # Novel 정보 조회 (book_title, character_name 필요)
        novel_data = await spring_boot_client.get_novel(str(request.novelId), jwt_token)
        book_title = novel_data.get("title") if novel_data else None
        
        if not book_title:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": f"Novel not found: {request.novelId}"}
            )
        
        # 캐릭터 정보 조회 (character_name 필요)
        characters_list = await spring_boot_client.get_characters_by_novel(str(request.novelId), jwt_token)
        if not characters_list:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": f"No characters found for novel: {request.novelId}"}
            )
        
        # 주인공 캐릭터 우선 선택
        main_characters = [c for c in characters_list if c.get("isMainCharacter")]
        character_data = main_characters[0] if main_characters else characters_list[0]
        character_name = character_data.get("commonName")
        
        if not character_name:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": "Character name not found"}
            )
        
        # Gemini를 사용하여 자연어 설명을 구조화된 데이터로 분석
        scenario_service = ScenarioManagementService()
        analyzed_data = {}
        
        # Store 정보 로깅 (structlog 사용)
        logger.info(
            "scenario_service_created",
            has_store_name=bool(scenario_service.store_name),
            store_name=scenario_service.store_name,
            character_name=character_name,
            book_title=book_title
        )
        
        # 캐릭터 속성 변경 분석
        if request.characterChanges:
            logger.info("starting_character_changes_analysis", description_preview=request.characterChanges[:100] if request.characterChanges else None)
            try:
                import json as json_module
                parsed = scenario_service._parse_character_property_changes(
                    request.characterChanges,
                    book_title,
                    character_name
                )
                # 분석 결과를 JSON 문자열로 변환 (Spring Boot가 JSON 문자열로 저장)
                analyzed_data["characterChanges"] = json_module.dumps(parsed, ensure_ascii=False)
                logger.info("character_changes_analysis_success", changes_count=len(parsed.get("changes", [])))
            except Exception as e:
                logger.warning("character_changes_analysis_failed", error=str(e), error_type=type(e).__name__)
                # 분석 실패 시 원본 텍스트 사용
                analyzed_data["characterChanges"] = request.characterChanges
        
        # 사건 변경 분석
        if request.eventAlterations:
            try:
                import json as json_module
                parsed = scenario_service._parse_event_alterations(
                    request.eventAlterations,
                    book_title
                )
                # 분석 결과를 JSON 문자열로 변환
                analyzed_data["eventAlterations"] = json_module.dumps(parsed, ensure_ascii=False)
            except Exception as e:
                logger.warning("event_alterations_analysis_failed", error=str(e))
                # 분석 실패 시 원본 텍스트 사용
                analyzed_data["eventAlterations"] = request.eventAlterations
        
        # 배경 변경 분석
        if request.settingModifications:
            logger.info("starting_setting_modifications_analysis", description_preview=request.settingModifications[:100] if request.settingModifications else None)
            try:
                import json as json_module
                parsed = scenario_service._parse_setting_modifications(
                    request.settingModifications,
                    book_title
                )
                # 분석 결과를 JSON 문자열로 변환
                analyzed_data["settingModifications"] = json_module.dumps(parsed, ensure_ascii=False)
                logger.info("setting_modifications_analysis_success", modifications_count=len(parsed.get("modifications", [])))
            except Exception as e:
                logger.warning("setting_modifications_analysis_failed", error=str(e), error_type=type(e).__name__)
                # 분석 실패 시 원본 텍스트 사용
                analyzed_data["settingModifications"] = request.settingModifications
        
        # Spring Boot로 전달할 데이터 준비 (분석된 데이터 + 원본 데이터)
        scenario_data = request.model_dump(mode="json")
        
        # 분석된 데이터로 명시적으로 업데이트 (JSON 문자열로 저장된 분석 결과)
        # analyzed_data에 있는 키들을 명시적으로 설정하여 원본 텍스트를 덮어씀
        if "characterChanges" in analyzed_data:
            scenario_data["characterChanges"] = analyzed_data["characterChanges"]
        if "eventAlterations" in analyzed_data:
            scenario_data["eventAlterations"] = analyzed_data["eventAlterations"]
        if "settingModifications" in analyzed_data:
            scenario_data["settingModifications"] = analyzed_data["settingModifications"]
        
        result = await spring_boot_client.create_scenario(
            scenario_data=scenario_data,
            jwt_token=jwt_token,
            user_id=user_id
        )
        
        return success_response(
            data=result,
            message="Scenario created successfully"
        )
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise NotFoundException(
                ErrorCode.SCENARIO_NOT_FOUND,
                details={"novel_id": str(request.novelId)}
            )
        raise ServiceUnavailableException(
            ErrorCode.SPRING_BOOT_ERROR,
            details={"status_code": e.response.status_code, "detail": e.response.text}
        )
    except httpx.TimeoutException:
        raise ServiceUnavailableException(ErrorCode.SPRING_BOOT_TIMEOUT)
    except httpx.RequestError as e:
        raise ServiceUnavailableException(
            ErrorCode.SPRING_BOOT_CONNECTION_ERROR,
            details={"error": str(e)}
        )

@router.get("/{scenario_id}", summary="시나리오 조회 (Spring Boot 위임)")
async def get_scenario_proxy(
    scenario_id: str,
    req: Request,
    user: dict = Depends(jwt_auth)
):
    """
    시나리오 조회 요청을 Spring Boot로 전달
    """
    try:
        jwt_token = get_jwt_token(req)
        
        logger.info("scenario_get_proxy", scenario_id=scenario_id)
        
        result = await spring_boot_client.get_scenario(
            scenario_id=scenario_id,
            jwt_token=jwt_token
        )
        
        return success_response(data=result)
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise NotFoundException(
                ErrorCode.SCENARIO_NOT_FOUND,
                details={"scenario_id": scenario_id}
            )
        raise ServiceUnavailableException(
            ErrorCode.SPRING_BOOT_ERROR,
            details={"status_code": e.response.status_code}
        )
    except httpx.TimeoutException:
        raise ServiceUnavailableException(ErrorCode.SPRING_BOOT_TIMEOUT)
    except httpx.RequestError as e:
        raise ServiceUnavailableException(
            ErrorCode.SPRING_BOOT_CONNECTION_ERROR,
            details={"error": str(e)}
        )

@router.delete("/{scenario_id}", summary="시나리오 삭제 (Spring Boot 위임)")
async def delete_scenario_proxy(
    scenario_id: str,
    req: Request,
    user: dict = Depends(jwt_auth)
):
    """
    시나리오 삭제 요청을 Spring Boot로 전달
    """
    try:
        jwt_token = get_jwt_token(req)
        
        logger.info("scenario_delete_proxy", scenario_id=scenario_id)
        
        await spring_boot_client.delete_scenario(
            scenario_id=scenario_id,
            jwt_token=jwt_token
        )
        
        return success_response(
            data={"scenario_id": scenario_id},
            message="Scenario deleted successfully"
        )
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise NotFoundException(
                ErrorCode.SCENARIO_NOT_FOUND,
                details={"scenario_id": scenario_id}
            )
        raise ServiceUnavailableException(
            ErrorCode.SPRING_BOOT_ERROR,
            details={"status_code": e.response.status_code}
        )
    except httpx.TimeoutException:
        raise ServiceUnavailableException(ErrorCode.SPRING_BOOT_TIMEOUT)
    except httpx.RequestError as e:
        raise ServiceUnavailableException(
            ErrorCode.SPRING_BOOT_CONNECTION_ERROR,
            details={"error": str(e)}
        )

@internal_router.post("/analyze", summary="시나리오 분석 (내부 전용, JWT 인증 없음)")
async def analyze_scenario_internal(request: ScenarioCreateProxyRequest):
    """
    시나리오 분석 요청 처리 (내부 서비스 전용, JWT 인증 없음)
    
    - Spring Boot에서 호출하는 내부 전용 엔드포인트
    - FastAPI에서 Gemini를 사용하여 자연어 설명을 구조화된 데이터로 분석
    - 분석 결과만 반환 (Spring Boot에서 저장)
    """
    try:
        logger.info("scenario_analysis_internal", novel_id=str(request.novelId))
        
        # Novel 정보 조회 (내부 API 사용, JWT 토큰 불필요)
        novel_data = await spring_boot_client.get_novel_internal(str(request.novelId))
        book_title = novel_data.get("title") if novel_data else None
        
        if not book_title:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": f"Novel not found: {request.novelId}"}
            )
        
        # 캐릭터 정보 조회 (내부 API 사용, JWT 토큰 불필요)
        characters_list = await spring_boot_client.get_characters_by_novel_internal(str(request.novelId))
        if not characters_list:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": f"No characters found for novel: {request.novelId}"}
            )
        
        # 주인공 캐릭터 우선 선택
        main_characters = [c for c in characters_list if c.get("isMainCharacter")]
        character_data = main_characters[0] if main_characters else characters_list[0]
        character_name = character_data.get("commonName")
        
        if not character_name:
            raise GajiException(
                ErrorCode.SCENARIO_CREATION_FAILED,
                details={"error": "Character name not found"}
            )
        
        # Gemini를 사용하여 자연어 설명을 구조화된 데이터로 분석
        scenario_service = ScenarioManagementService()
        analyzed_data = {}
        
        logger.info("starting_gemini_analysis", book_title=book_title, character_name=character_name)
        
        # 캐릭터 속성 변경 분석
        if request.characterChanges:
            try:
                parsed = scenario_service._parse_character_property_changes(
                    request.characterChanges,
                    book_title,
                    character_name
                )
                analyzed_data["characterChanges"] = json.dumps(parsed, ensure_ascii=False)
                logger.info("character_changes_analysis_success")
            except Exception as e:
                logger.warning("character_changes_analysis_failed", error=str(e))
                analyzed_data["characterChanges"] = request.characterChanges
        
        # 사건 변경 분석
        if request.eventAlterations:
            try:
                parsed = scenario_service._parse_event_alterations(
                    request.eventAlterations,
                    book_title
                )
                analyzed_data["eventAlterations"] = json.dumps(parsed, ensure_ascii=False)
                logger.info("event_alterations_analysis_success")
            except Exception as e:
                logger.warning("event_alterations_analysis_failed", error=str(e))
                analyzed_data["eventAlterations"] = request.eventAlterations
        
        # 배경 변경 분석
        if request.settingModifications:
            try:
                parsed = scenario_service._parse_setting_modifications(
                    request.settingModifications,
                    book_title
                )
                analyzed_data["settingModifications"] = json.dumps(parsed, ensure_ascii=False)
                logger.info("setting_modifications_analysis_success")
            except Exception as e:
                logger.warning("setting_modifications_analysis_failed", error=str(e))
                analyzed_data["settingModifications"] = request.settingModifications
        
        logger.info("scenario_analysis_complete", analyzed_keys=list(analyzed_data.keys()))
        
        return success_response(
            data=analyzed_data,
            message="Scenario analyzed successfully"
        )
        
    except httpx.HTTPStatusError as e:
        logger.error("spring_boot_api_error", status_code=e.response.status_code, error=str(e))
        raise GajiException(
            ErrorCode.SCENARIO_CREATION_FAILED,
            details={"error": f"Spring Boot API error: {e.response.status_code}"}
        )
    except Exception as e:
        logger.error("scenario_analysis_failed", error=str(e))
        raise GajiException(
            ErrorCode.SCENARIO_CREATION_FAILED,
            details={"error": f"Scenario analysis failed: {str(e)}"}
        )

