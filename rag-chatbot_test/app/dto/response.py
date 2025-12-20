"""
Standard API Response DTOs
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """표준 API 응답 형식"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """표준 에러 응답 형식"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

def success_response(data: Any = None, message: str = None) -> dict:
    """성공 응답 생성"""
    return ApiResponse(
        success=True,
        data=data,
        message=message
    ).model_dump(mode='json')

def error_response(error_code: str, message: str, details: dict = None) -> dict:
    """에러 응답 생성"""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details
    ).model_dump(mode='json')

