"""
Pydantic Models & Schemas

API 요청/응답 모델 정의
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID


# Request Models
class MessageRequest(BaseModel):
    """메시지 요청 모델"""
    content: str = Field(..., description="사용자 메시지 내용")
    scenario_id: Optional[UUID] = Field(None, description="시나리오 ID")
    scenario_context: Optional[str] = Field(None, description="시나리오 컨텍스트")
    book_id: Optional[str] = Field(None, description="책 ID")
    conversation_history: Optional[List[Dict]] = Field(None, description="대화 히스토리")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "What if Harry Potter chose Slytherin?",
                "scenario_context": "Year 1 at Hogwarts",
                "book_id": "harry_potter_1",
                "conversation_history": []
            }
        }


# Response Models
class MessageResponse(BaseModel):
    """메시지 응답 모델"""
    message_id: str = Field(..., description="메시지 ID")
    content: str = Field(..., description="생성된 응답 내용")
    relevant_passages: Optional[List[Dict]] = Field(None, description="관련 청크")
    metadata: Optional[Dict] = Field(None, description="메타데이터 (RAG 사용 여부 등)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "If Harry had chosen Slytherin...",
                "metadata": {
                    "rag_used": True,
                    "question_type": "story_extension",
                    "passages_count": 3
                }
            }
        }


class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str = Field(..., description="검색 쿼리")
    book_id: Optional[str] = Field(None, description="책 ID 필터")
    top_k: int = Field(5, ge=1, le=20, description="반환할 결과 수")


class SearchResponse(BaseModel):
    """검색 응답 모델"""
    query: str
    results: List[Dict]
    count: int


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str = Field(..., description="서비스 상태")
    gemini_api: str = Field(..., description="Gemini API 상태")
    vectordb: str = Field(..., description="VectorDB 상태")
    celery_workers: int = Field(..., description="Celery 워커 수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "gemini_api": "connected",
                "vectordb": "connected",
                "celery_workers": 2
            }
        }


class TaskStatusResponse(BaseModel):
    """작업 상태 응답 모델 (Long Polling)"""
    status: str = Field(..., description="작업 상태: processing|completed|failed")
    result: Optional[Dict] = Field(None, description="작업 결과")
    error: Optional[str] = Field(None, description="에러 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "result": {
                    "book_id": "123",
                    "chunks_count": 500
                },
                "error": None
            }
        }
