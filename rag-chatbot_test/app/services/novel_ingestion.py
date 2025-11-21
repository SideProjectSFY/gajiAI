"""
Novel Ingestion Service

Gutenberg 소설 파싱 및 VectorDB 저장
"""

from typing import List, Dict, Optional
import structlog
from app.celery_app import celery_app
from app.services.vectordb_client import get_vectordb_client
from app.services.gemini_client import GeminiClient

logger = structlog.get_logger()


class NovelIngestionService:
    """소설 임포트 서비스"""
    
    def __init__(self):
        self.vectordb = get_vectordb_client()
        self.gemini_client = GeminiClient()
    
    def parse_gutenberg_book(self, book_id: str, text: str) -> List[Dict]:
        """
        Gutenberg 책 파싱
        
        Args:
            book_id: 책 ID
            text: 책 전체 텍스트
        
        Returns:
            청크 리스트
        """
        # TODO: 실제 파싱 로직 구현
        # - 문장 단위 분할
        # - 청크 크기 조절 (500-1000 토큰)
        # - 메타데이터 추출
        
        chunks = []
        # 간단한 예시 구현
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 50:  # 최소 길이
                chunks.append({
                    'id': f"{book_id}_chunk_{i}",
                    'text': para.strip(),
                    'metadata': {
                        'book_id': book_id,
                        'chunk_index': i
                    }
                })
        
        return chunks
    
    def ingest_chunks(
        self,
        chunks: List[Dict],
        collection_name: str = "novel_passages"
    ):
        """
        청크를 VectorDB에 저장
        
        Args:
            chunks: 청크 리스트
            collection_name: 컬렉션 이름
        """
        documents = [chunk['text'] for chunk in chunks]
        ids = [chunk['id'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # 임베딩 생성
        embeddings = []
        for doc in documents:
            embedding = self.gemini_client.generate_embedding(doc)
            embeddings.append(embedding)
        
        # VectorDB에 저장
        self.vectordb.add_documents(
            collection_name=collection_name,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info("chunks_ingested", count=len(chunks), collection=collection_name)


@celery_app.task(name="ingest_novel_task")
def ingest_novel_task(book_id: str, text: str) -> Dict:
    """
    소설 임포트 비동기 작업
    
    Args:
        book_id: 책 ID
        text: 책 전체 텍스트
    
    Returns:
        작업 결과
    """
    try:
        service = NovelIngestionService()
        chunks = service.parse_gutenberg_book(book_id, text)
        service.ingest_chunks(chunks)
        
        return {
            "status": "success",
            "book_id": book_id,
            "chunks_count": len(chunks)
        }
    except Exception as e:
        logger.error("ingest_novel_error", error=str(e), book_id=book_id)
        return {
            "status": "failed",
            "error": str(e)
        }
