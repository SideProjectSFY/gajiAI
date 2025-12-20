import httpx
from typing import Optional, Dict, Any, List
from app.config.settings import settings
import structlog

logger = structlog.get_logger()

class SpringBootClient:
    """Spring Boot Internal API 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.spring_boot_base_url
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        
    async def _request(
        self,
        method: str,
        endpoint: str,
        jwt_token: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """공통 요청 로직"""
        headers = kwargs.pop("headers", {})
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{endpoint}",
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "spring_boot_api_error",
                    status=e.response.status_code,
                    endpoint=endpoint,
                    body=e.response.text if hasattr(e.response, 'text') else None
                )
                raise
            except httpx.RequestError as e:
                logger.error(
                    "spring_boot_connection_error",
                    endpoint=endpoint,
                    error=str(e)
                )
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Spring Boot Health Check"""
        return await self._request("GET", "/actuator/health")
    
    async def get_scenario(self, scenario_id: str, jwt_token: str) -> Dict[str, Any]:
        """시나리오 조회"""
        return await self._request(
            "GET",
            f"/api/v1/scenarios/{scenario_id}",
            jwt_token=jwt_token
        )
    
    async def create_scenario(
        self,
        scenario_data: Dict[str, Any],
        jwt_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """시나리오 생성"""
        headers = {"X-User-Id": user_id}
        return await self._request(
            "POST",
            "/api/v1/scenarios",
            jwt_token=jwt_token,
            headers=headers,
            json=scenario_data
        )
    
    async def update_scenario(
        self,
        scenario_id: str,
        scenario_data: Dict[str, Any],
        jwt_token: str
    ) -> Dict[str, Any]:
        """시나리오 수정"""
        return await self._request(
            "PUT",
            f"/api/v1/scenarios/{scenario_id}",
            jwt_token=jwt_token,
            json=scenario_data
        )
    
    async def delete_scenario(
        self,
        scenario_id: str,
        jwt_token: str
    ) -> None:
        """시나리오 삭제"""
        await self._request(
            "DELETE",
            f"/api/v1/scenarios/{scenario_id}",
            jwt_token=jwt_token
        )
    
    async def get_conversation(
        self,
        conversation_id: str,
        jwt_token: str
    ) -> Dict[str, Any]:
        """대화 조회"""
        return await self._request(
            "GET",
            f"/api/v1/conversations/{conversation_id}",
            jwt_token=jwt_token
        )
    
    async def create_conversation(
        self,
        conversation_data: Dict[str, Any],
        jwt_token: str,
        user_id: str
    ) -> Dict[str, Any]:
        """대화 생성"""
        headers = {"X-User-Id": user_id}
        return await self._request(
            "POST",
            "/api/v1/conversations",
            jwt_token=jwt_token,
            headers=headers,
            json=conversation_data
        )
    
    async def save_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        user_id: str,
        jwt_token: str
    ) -> Dict[str, Any]:
        """단일 메시지 저장"""
        headers = {"X-User-Id": user_id}
        return await self._request(
            "POST",
            f"/api/v1/conversations/{conversation_id}/messages",
            jwt_token=jwt_token,
            headers=headers,
            json={"content": content, "role": role}
        )
    
    async def save_messages(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        jwt_token: str
    ) -> Dict[str, Any]:
        """메시지 저장 (레거시, 단일 메시지 저장으로 대체 권장)"""
        return await self._request(
            "POST",
            f"/api/v1/conversations/{conversation_id}/messages",
            jwt_token=jwt_token,
            json={"messages": messages}
        )
    
    async def create_novel(
        self,
        novel_data: Dict[str, Any],
        jwt_token: str
    ) -> Dict[str, Any]:
        """소설 메타데이터 생성 (Internal API)"""
        return await self._request(
            "POST",
            "/api/v1/internal/novels",
            jwt_token=jwt_token,
            json=novel_data
        )
    
    async def get_novel(
        self,
        novel_id: str,
        jwt_token: str
    ) -> Dict[str, Any]:
        """소설 메타데이터 조회 (Internal API)"""
        return await self._request(
            "GET",
            f"/api/v1/internal/novels/{novel_id}",
            jwt_token=jwt_token
        )
    
    async def get_characters_by_novel(
        self,
        novel_id: str,
        jwt_token: str
    ) -> List[Dict[str, Any]]:
        """소설의 캐릭터 목록 조회 (Internal API)"""
        response = await self._request(
            "GET",
            f"/api/v1/internal/novels/{novel_id}/characters",
            jwt_token=jwt_token
        )
        # 응답이 리스트인 경우 그대로 반환, 딕셔너리인 경우 리스트로 변환
        if isinstance(response, list):
            return response
        return response.get("data", []) if isinstance(response, dict) else []
    
    async def get_novel_internal(
        self,
        novel_id: str
    ) -> Dict[str, Any]:
        """소설 메타데이터 조회 (내부 전용, JWT 토큰 불필요)"""
        return await self._request(
            "GET",
            f"/api/v1/internal/novels/{novel_id}",
            jwt_token=None
        )
    
    async def get_characters_by_novel_internal(
        self,
        novel_id: str
    ) -> List[Dict[str, Any]]:
        """소설의 캐릭터 목록 조회 (내부 전용, JWT 토큰 불필요)"""
        response = await self._request(
            "GET",
            f"/api/v1/internal/novels/{novel_id}/characters",
            jwt_token=None
        )
        # 응답이 리스트인 경우 그대로 반환, 딕셔너리인 경우 리스트로 변환
        if isinstance(response, list):
            return response
        return response.get("data", []) if isinstance(response, dict) else []

spring_boot_client = SpringBootClient()

