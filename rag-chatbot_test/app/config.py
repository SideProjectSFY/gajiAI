"""
Application Configuration

환경 변수 관리 및 설정 클래스
Story 1.3 기본 설정에 맞게 통합
"""

import os
from typing import Literal, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Gemini API
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_api_keys: str = Field(default="", env="GEMINI_API_KEYS")  # 여러 키 지원
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
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    
    # Spring Boot (Pattern B: API Gateway)
    spring_boot_url: str = Field(default="http://localhost:8080", env="SPRING_BOOT_URL")
    
    # CORS
    cors_allowed_origins: str = Field(default="http://localhost:8080", env="CORS_ALLOWED_ORIGINS")
    
    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    port: int = Field(default=8000, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="console", env="LOG_FORMAT")  # "json" or "console"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_gemini_api_key(self) -> str:
        """Gemini API 키 반환 (단일 키 우선, 없으면 여러 키에서 첫 번째)"""
        if self.gemini_api_key:
            return self.gemini_api_key
        
        if self.gemini_api_keys:
            keys = self.get_gemini_api_keys()
            if keys:
                return keys[0]
        
        return ""
    
    def get_gemini_api_keys(self) -> List[str]:
        """Gemini API 키 리스트 반환"""
        if self.gemini_api_keys:
            keys = [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]
            if keys:
                return keys
        
        if self.gemini_api_key:
            return [self.gemini_api_key]
        
        return []
    
    def get_redis_url(self) -> str:
        """Redis URL 생성"""
        if self.redis_url:
            return self.redis_url
        
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_cors_origins(self) -> List[str]:
        """CORS 허용 origin 리스트 반환"""
        if not self.cors_allowed_origins:
            return [self.spring_boot_url]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


# Global settings instance
settings = Settings()

