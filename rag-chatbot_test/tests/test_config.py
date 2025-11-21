"""
Test Configuration

환경 설정 테스트
"""

import pytest
from app.config import Settings


def test_settings_load_from_env(mock_env):
    """환경 변수에서 설정 로드 테스트"""
    settings = Settings()
    
    assert settings.gemini_api_key == "test_key"
    assert settings.vectordb_type == "chromadb"
    assert settings.chroma_path == "./test_chroma_data"
    assert settings.redis_url == "redis://localhost:6379"


def test_settings_defaults(monkeypatch):
    """기본값 테스트 - Redis는 optional"""
    # GEMINI_API_KEY는 필수이므로 설정
    monkeypatch.setenv("GEMINI_API_KEY", "test_key_required")
    
    # .env 파일 읽기를 방지하기 위해 env_file을 무시
    settings = Settings(_env_file=None)
    
    # 기본값 확인
    assert settings.gemini_model == "gemini-2.5-flash"
    assert settings.vectordb_type == "chromadb"
    assert settings.redis_url == ""  # Redis는 optional, 기본값 빈 문자열
    assert settings.app_env == "development"


def test_vectordb_type_validation():
    """VectorDB 타입 검증 테스트"""
    settings = Settings(
        gemini_api_key="test_key",
        vectordb_type="chromadb"
    )
    assert settings.vectordb_type in ["chromadb", "pinecone"]
