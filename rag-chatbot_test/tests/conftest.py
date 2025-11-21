"""
Test Configuration

pytest 설정 및 fixture
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from app.main import app
from app.routers.chat import get_rag_service


@pytest.fixture
def mock_rag_service():
    """Mock RAG Service - 모든 테스트에서 재사용 가능한 기본 mock"""
    mock = Mock()
    mock.generate_hybrid_response.return_value = (
        "Mock AI response",
        {"rag_used": True}
    )
    mock.generate_response_stream.return_value = iter(["Mock ", "stream"])
    mock.generate_response_without_rag.return_value = "Mock response without RAG"
    mock.search_relevant_passages.return_value = [
        {"text": "Mock passage", "similarity": 0.9}
    ]
    return mock


@pytest.fixture
def client(mock_rag_service):
    """FastAPI 테스트 클라이언트 with mocked RAG service dependency"""
    # Override FastAPI dependency injection
    app.dependency_overrides[get_rag_service] = lambda: mock_rag_service
    
    test_client = TestClient(app)
    yield test_client
    
    # Cleanup after each test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_env(monkeypatch):
    """테스트용 환경 변수 설정"""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    monkeypatch.setenv("VECTORDB_TYPE", "chromadb")
    monkeypatch.setenv("CHROMA_PATH", "./test_chroma_data")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("SPRING_BOOT_URL", "http://localhost:8080")
