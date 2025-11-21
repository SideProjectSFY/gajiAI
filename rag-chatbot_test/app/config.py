"""
Application Configuration

환경 변수 관리 및 설정 클래스
"""

import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Gemini API
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    
    # VectorDB
    vectordb_type: Literal["chromadb", "pinecone"] = Field(default="chromadb", env="VECTORDB_TYPE")
    chroma_path: str = Field(default="./chroma_data", env="CHROMA_PATH")
    chroma_collection: str = Field(default="novel_passages", env="CHROMA_COLLECTION")
    
    # Pinecone (Production)
    pinecone_api_key: str = Field(default="", env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default="us-west1-gcp", env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="gaji-ai-vectors", env="PINECONE_INDEX_NAME")
    
    # Redis (OPTIONAL - falls back to no-op cache if not configured)
    redis_url: str = Field(default="", env="REDIS_URL")
    
    # Spring Boot
    spring_boot_url: str = Field(default="http://localhost:8080", env="SPRING_BOOT_URL")
    
    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
