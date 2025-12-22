"""
Application Settings (Pydantic Settings)

환경 변수를 타입 안전하게 관리합니다.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Gemini API
    gemini_api_keys: str = ""
    
    # CORS
    cors_allowed_origins: str = "http://localhost:8080"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_socket_timeout: int = 5
    
    # Celery
    celery_broker_url: str = ""  # 빈 값이면 redis://{host}:{port}/{db}로 자동 생성
    celery_result_backend: str = ""  # 빈 값이면 redis://{host}:{port}/{db}로 자동 생성
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "console"  # "json" or "console"
    
    # Application
    app_env: str = "development"  # "development" or "production"
    
    # VectorDB
    vectordb_type: str = "chromadb"  # "chromadb" or "pinecone"
    chromadb_path: str = "./chroma_data"
    pinecone_api_key: str = ""  # 프로덕션용
    pinecone_environment: str = ""  # 프로덕션용
    
    # FastAPI
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    
    # Spring Boot Integration
    spring_boot_base_url: str = "http://host.docker.internal:8080"  # Access host machine from container
    spring_boot_timeout: int = 30
    
    # JWT Authentication
    jwt_secret_key: str = ""  # Spring Boot와 동일한 키 사용
    jwt_algorithm: str = "HS256"  # Spring Boot와 동일한 알고리즘 (JJWT 기본값)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 정의되지 않은 환경 변수 무시
    
    def get_cors_origins(self) -> List[str]:
        """CORS 허용 origin 리스트 반환"""
        if not self.cors_allowed_origins:
            return ["http://localhost:8080"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
    
    def get_redis_url(self) -> str:
        """Redis URL 생성"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_celery_broker_url(self) -> str:
        """Celery 브로커 URL 반환 (설정이 없으면 Redis URL 사용)"""
        if self.celery_broker_url:
            return self.celery_broker_url
        return self.get_redis_url()
    
    def get_celery_result_backend(self) -> str:
        """Celery 결과 백엔드 URL 반환 (설정이 없으면 Redis URL 사용)"""
        if self.celery_result_backend:
            return self.celery_result_backend
        return self.get_redis_url()
    
    def get_gemini_api_keys(self) -> List[str]:
        """Gemini API 키 리스트 반환"""
        if not self.gemini_api_keys:
            # 레거시: GEMINI_API_KEY 환경 변수 확인
            legacy_key = os.getenv("GEMINI_API_KEY")
            if legacy_key:
                return [legacy_key]
            return []
        
        keys = [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]
        return keys


# 전역 설정 인스턴스
settings = Settings()

