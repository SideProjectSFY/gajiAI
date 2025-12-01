"""
Semantic Search API Router

VectorDB를 사용한 의미 기반 검색 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import time

from app.services.vectordb_client import get_vectordb_client
from app.services.api_key_manager import get_api_key_manager

router = APIRouter(prefix="/api/ai/search", tags=["semantic-search"])


class PassageSearchRequest(BaseModel):
    """문장 검색 요청"""
    query: str = Field(..., description="검색 쿼리")
    novel_id: Optional[str] = Field(None, description="소설 ID (특정 소설만 검색)")
    top_k: int = Field(10, description="반환할 결과 수")
    filters: Optional[Dict] = Field(None, description="필터 (min_similarity 등)")


class PassageResult(BaseModel):
    """검색 결과 문장"""
    id: str
    text: str
    similarity_score: float
    chunk_index: Optional[int] = None
    metadata: Dict


class PassageSearchResponse(BaseModel):
    """문장 검색 응답"""
    passages: List[PassageResult]
    total_results: int
    query_embedding_time_ms: Optional[float] = None
    search_time_ms: Optional[float] = None


@router.post(
    "/passages",
    response_model=PassageSearchResponse,
    summary="유사 문장 검색",
    description="VectorDB cosine similarity를 사용한 의미 기반 문장 검색"
)
async def search_passages(request: PassageSearchRequest):
    """
    유사 문장 검색
    
    Args:
        request: 검색 쿼리 및 필터
    
    Returns:
        검색된 문장 목록
    """
    try:
        start_time = time.time()
        
        # Gemini Embedding API로 쿼리 임베딩 생성
        api_key_manager = get_api_key_manager()
        api_key = api_key_manager.get_current_key()
        
        # TODO: 실제 구현 시 Gemini Embedding API 호출
        # from app.services.embedding_service import generate_embedding
        # query_embedding = await generate_embedding(request.query, api_key)
        query_embedding = []  # Placeholder
        
        embedding_time = (time.time() - start_time) * 1000
        
        # VectorDB 검색
        search_start = time.time()
        vectordb = get_vectordb_client()
        
        # VectorDB에서 검색
        results = vectordb.search_passages(
            query_embedding=query_embedding,
            novel_id=request.novel_id,
            n_results=request.top_k
        )
        
        search_time = (time.time() - search_start) * 1000
        
        # 결과 포맷팅
        passage_results = []
        for i, result in enumerate(results):
            # similarity_score 계산 (distance를 score로 변환)
            distance = result.get("distance", 1.0)
            similarity_score = 1.0 - distance  # distance가 작을수록 유사도 높음
            
            # min_similarity 필터 적용
            if request.filters and request.filters.get("min_similarity"):
                if similarity_score < request.filters["min_similarity"]:
                    continue
            
            passage_results.append(PassageResult(
                id=result.get("metadata", {}).get("id", f"passage-{i}"),
                text=result.get("text", ""),
                similarity_score=similarity_score,
                chunk_index=result.get("metadata", {}).get("chunk_index"),
                metadata=result.get("metadata", {})
            ))
        
        return PassageSearchResponse(
            passages=passage_results,
            total_results=len(passage_results),
            query_embedding_time_ms=embedding_time,
            search_time_ms=search_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

