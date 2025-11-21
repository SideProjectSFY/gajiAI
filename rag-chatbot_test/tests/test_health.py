"""
Test Health Check Endpoint

헬스 체크 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint_structure(client: TestClient):
    """헬스 체크 엔드포인트 구조 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "gemini_api" in data
    assert "vectordb" in data
    assert "celery_workers" in data


@pytest.mark.asyncio
async def test_cors_configuration(client: TestClient):
    """CORS 설정 테스트"""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # CORS 헤더 확인
    assert "access-control-allow-origin" in response.headers
