"""
챗봇 대화 API 엔드포인트

RAG 기반 "What If" 챗봇 대화를 위한 FastAPI 라우터
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
import os

from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/ai", tags=["chat"])

# RAG 서비스 인스턴스 (의존성 주입)
def get_rag_service() -> RAGService:
    """RAG 서비스 인스턴스 생성"""
    return RAGService(
        collection_name=os.getenv("CHROMA_COLLECTION", "novel_passages"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )


# 요청/응답 모델
class MessageRequest(BaseModel):
    """메시지 요청 모델"""
    content: str
    scenario_id: Optional[UUID] = None
    scenario_context: Optional[str] = None
    book_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = None


class MessageResponse(BaseModel):
    """메시지 응답 모델"""
    message_id: str
    content: str
    relevant_passages: Optional[List[dict]] = None
    metadata: Optional[dict] = None  # RAG 사용 여부, 분류 정보 등


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request: MessageRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    챗봇에 메시지 전송 (일반 응답)
    
    Args:
        conversation_id: 대화 ID
        request: 메시지 요청
        rag_service: RAG 서비스
    
    Returns:
        생성된 응답
    """
    try:
        # 하이브리드 모드 사용 (질문 유형에 따라 자동 선택)
        response_text, metadata = rag_service.generate_hybrid_response(
            user_message=request.content,
            scenario_context=request.scenario_context,
            book_id=request.book_id,
            conversation_history=request.conversation_history
        )
        
        return MessageResponse(
            message_id=str(conversation_id),
            content=response_text,
            metadata=metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")


@router.post("/conversations/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: UUID,
    request: MessageRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    챗봇에 메시지 전송 (스트리밍 응답 - SSE)
    
    Args:
        conversation_id: 대화 ID
        request: 메시지 요청
        rag_service: RAG 서비스
    
    Returns:
        Server-Sent Events 스트림
    """
    def generate():
        """SSE 스트림 생성"""
        try:
            # 스트리밍 응답 생성
            for token in rag_service.generate_response_stream(
                user_message=request.content,
                scenario_context=request.scenario_context,
                book_id=request.book_id,
                conversation_history=request.conversation_history,
                top_k=5
            ):
                # SSE 형식으로 전송
                yield f"data: {token}\n\n"
            
            # 완료 신호
            yield "data: [DONE]\n\n"
        
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/conversations/{conversation_id}/messages/no-rag")
async def send_message_without_rag(
    conversation_id: UUID,
    request: MessageRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    챗봇에 메시지 전송 (RAG 없이 - 비교용)
    
    Args:
        conversation_id: 대화 ID
        request: 메시지 요청
        rag_service: RAG 서비스
    
    Returns:
        생성된 응답 (RAG 없이)
    """
    try:
        response_text = rag_service.generate_response_without_rag(
            user_message=request.content,
            scenario_context=request.scenario_context,
            conversation_history=request.conversation_history
        )
        
        return MessageResponse(
            message_id=str(conversation_id),
            content=response_text
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")


@router.get("/search/passages")
async def search_passages(
    query: str,
    book_id: Optional[str] = None,
    top_k: int = 5,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    관련 청크 검색 (디버깅/테스트용)
    
    Args:
        query: 검색 쿼리
        book_id: 책 ID (선택)
        top_k: 반환할 상위 k개
        rag_service: RAG 서비스
    
    Returns:
        검색된 청크 리스트
    """
    try:
        passages = rag_service.search_relevant_passages(
            query=query,
            book_id=book_id,
            top_k=top_k
        )
        
        return {
            "query": query,
            "results": passages,
            "count": len(passages)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")


class ForkConversationRequest(BaseModel):
    """대화 포크 요청 모델 (Epic 4, Story 4.4)"""
    source_conversation_id: UUID
    fork_point_message_id: UUID
    new_scenario_id: UUID
    user_id: UUID
    scenario_context: str
    source_depth: Optional[int] = 0
    message_history: Optional[List[dict]] = None


class ForkConversationResponse(BaseModel):
    """대화 포크 응답 모델"""
    forked_conversation_id: str
    messages_copied: int
    new_depth: int
    scenario_context: str


@router.post("/conversations/fork")
async def fork_conversation(
    request: ForkConversationRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    대화 포크 생성 (Epic 4, Story 4.4)
    
    ROOT 대화에서만 포크 가능 (depth=0 → depth=1)
    메시지 히스토리는 min(6, total) 개수만큼 복사
    
    Args:
        request: 포크 요청 데이터
        rag_service: RAG 서비스
    
    Returns:
        포크된 대화 정보
    """
    try:
        # 1. Depth constraint: ROOT-only forking (max depth = 1)
        if request.source_depth >= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot fork from forked conversation. Only ROOT conversations (depth=0) can be forked."
            )
        
        # 2. Message history transfer: Copy min(6, total) messages
        message_history = request.message_history or []
        messages_to_copy = min(6, len(message_history))
        copied_messages = message_history[-messages_to_copy:] if messages_to_copy > 0 else []
        
        # 3. Generate new conversation ID (UUID v4)
        from uuid import uuid4
        forked_conversation_id = uuid4()
        
        # 4. Generate initial AI response with new scenario context
        # This establishes the new scenario context in the forked conversation
        initial_message = "Hello, I'm ready to explore this alternate scenario with you."
        
        # Use RAG service to generate context-aware initial response
        # This validates that the fork can be processed successfully
        _, _ = rag_service.generate_hybrid_response(
            user_message=initial_message,
            scenario_context=request.scenario_context,
            conversation_history=copied_messages
        )
        
        # 5. Return fork result
        return ForkConversationResponse(
            forked_conversation_id=str(forked_conversation_id),
            messages_copied=messages_to_copy,
            new_depth=request.source_depth + 1,
            scenario_context=request.scenario_context
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fork conversation: {str(e)}"
        )

