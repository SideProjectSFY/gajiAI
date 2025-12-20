"""
Custom exceptions and error codes
"""
from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class ErrorCode(Enum):
    """표준 에러 코드"""
    
    # 인증 관련 (AUTH)
    UNAUTHORIZED = ("AUTH001", "Unauthorized", status.HTTP_401_UNAUTHORIZED)
    INVALID_TOKEN = ("AUTH002", "Invalid or expired token", status.HTTP_401_UNAUTHORIZED)
    FORBIDDEN = ("AUTH003", "Forbidden", status.HTTP_403_FORBIDDEN)
    
    # 시나리오 관련 (SCENARIO)
    SCENARIO_NOT_FOUND = ("SCENARIO001", "Scenario not found", status.HTTP_404_NOT_FOUND)
    SCENARIO_CREATION_FAILED = ("SCENARIO002", "Failed to create scenario", status.HTTP_500_INTERNAL_SERVER_ERROR)
    SCENARIO_VALIDATION_FAILED = ("SCENARIO003", "Scenario validation failed", status.HTTP_400_BAD_REQUEST)
    
    # 대화 관련 (CONV)
    CONVERSATION_NOT_FOUND = ("CONV001", "Conversation not found", status.HTTP_404_NOT_FOUND)
    MESSAGE_GENERATION_FAILED = ("CONV002", "Failed to generate message", status.HTTP_500_INTERNAL_SERVER_ERROR)
    CONVERSATION_CREATION_FAILED = ("CONV003", "Failed to create conversation", status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # AI 서비스 관련 (AI)
    GEMINI_API_ERROR = ("AI001", "Gemini API error", status.HTTP_503_SERVICE_UNAVAILABLE)
    FILE_SEARCH_STORE_NOT_CONFIGURED = ("AI002", "File Search Store not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)
    VECTORDB_ERROR = ("AI003", "Vector database error", status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # 외부 서비스 연동 (EXT)
    SPRING_BOOT_ERROR = ("EXT001", "Spring Boot API error", status.HTTP_503_SERVICE_UNAVAILABLE)
    SPRING_BOOT_TIMEOUT = ("EXT002", "Spring Boot API timeout", status.HTTP_504_GATEWAY_TIMEOUT)
    SPRING_BOOT_CONNECTION_ERROR = ("EXT003", "Spring Boot connection error", status.HTTP_503_SERVICE_UNAVAILABLE)
    
    # 입력 검증 (VALIDATION)
    INVALID_INPUT = ("VALIDATION001", "Invalid input", status.HTTP_400_BAD_REQUEST)
    MISSING_REQUIRED_FIELD = ("VALIDATION002", "Missing required field", status.HTTP_400_BAD_REQUEST)
    
    # 시스템 에러 (SYSTEM)
    INTERNAL_SERVER_ERROR = ("SYSTEM001", "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    DATABASE_ERROR = ("SYSTEM002", "Database error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def __init__(self, code: str, message: str, http_status: int):
        self.code = code
        self.message = message
        self.http_status = http_status

class GajiException(HTTPException):
    """프로젝트 공통 예외"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        custom_message: Optional[str] = None
    ):
        self.error_code = error_code
        self.details = details
        
        # 커스텀 메시지가 있으면 사용, 없으면 기본 메시지
        message = custom_message if custom_message else error_code.message
        
        super().__init__(
            status_code=error_code.http_status,
            detail={
                "success": False,
                "error_code": error_code.code,
                "message": message,
                "details": details
            }
        )

class UnauthorizedException(GajiException):
    """인증 실패 예외"""
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.UNAUTHORIZED, details)

class ForbiddenException(GajiException):
    """권한 없음 예외"""
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.FORBIDDEN, details)

class NotFoundException(GajiException):
    """리소스를 찾을 수 없음 예외"""
    def __init__(self, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, details)

class ValidationException(GajiException):
    """입력 검증 실패 예외"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INVALID_INPUT, details, message)

class ServiceUnavailableException(GajiException):
    """외부 서비스 연동 실패 예외"""
    def __init__(self, error_code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(error_code, details)

