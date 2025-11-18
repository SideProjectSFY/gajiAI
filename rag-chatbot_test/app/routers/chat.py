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
        chroma_path=os.getenv("CHROMA_PATH", "./chroma_data"),
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

