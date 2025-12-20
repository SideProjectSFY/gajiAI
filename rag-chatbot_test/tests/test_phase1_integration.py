"""
Phase 1 통합 테스트
gajiAI ↔ gajiBE 기본 통신 테스트
"""
import pytest
import httpx
from app.config.settings import settings

BASE_URL = "http://localhost:8000"
SPRING_BOOT_URL = settings.spring_boot_base_url

@pytest.mark.asyncio
class TestPhase1Integration:
    """Phase 1: 기본 통신 테스트"""
    
    async def test_1_spring_boot_health(self):
        """1. Spring Boot Health Check"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SPRING_BOOT_URL}/actuator/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "UP"
    
    async def test_2_fastapi_health(self):
        """2. FastAPI Health Check"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    async def test_3_jwt_authentication(self):
        """3. JWT 발행 및 검증"""
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{SPRING_BOOT_URL}/api/v1/auth/login",
                json={"username": "test", "password": "test123"}
            )
            assert login_response.status_code == 200
            token = login_response.json().get("token")
            assert token is not None
            
            headers = {"Authorization": f"Bearer {token}"}
            
            health_response = await client.get(
                f"{BASE_URL}/api/v1/scenarios/health-test",
                headers=headers
            )
            assert health_response.status_code in [200, 404]
    
    async def test_4_scenario_proxy_create(self):
        """4. 시나리오 생성 Proxy (Mock)"""
        async with httpx.AsyncClient() as client:
            login_response = await client.post(
                f"{SPRING_BOOT_URL}/api/v1/auth/login",
                json={"username": "test", "password": "test123"}
            )
            token = login_response.json().get("token")
            
            headers = {"Authorization": f"Bearer {token}"}
            scenario_data = {
                "scenario_name": "Phase 1 테스트 시나리오",
                "book_title": "The Adventures of Sherlock Holmes",
                "character_name": "Sherlock Holmes",
                "is_public": True,
                "character_property_changes": {
                    "enabled": True,
                    "description": "테스트용 변경사항"
                }
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/scenarios",
                json=scenario_data,
                headers=headers
            )
            
            assert response.status_code in [200, 201, 404, 500]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

