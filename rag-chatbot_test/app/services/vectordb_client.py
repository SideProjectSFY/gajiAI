"""
VectorDB Client

ChromaDB와 Pinecone을 추상화한 VectorDB 클라이언트
Updated for ChromaDB >= 1.3.5 and Pinecone >= 8.0.0
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import chromadb
import structlog

from app.config import settings

logger = structlog.get_logger()


class VectorDBClient(ABC):
    """VectorDB 추상 인터페이스"""
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        collection_name: str,
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """벡터 검색"""
        pass
    
    @abstractmethod
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """문서 추가"""
        pass
    
    @abstractmethod
    def get_or_create_collection(self, name: str, **kwargs):
        """컬렉션 생성 또는 가져오기"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """연결 상태 확인"""
        pass


class ChromaDBClient(VectorDBClient):
    """ChromaDB 클라이언트 (개발 환경) - ChromaDB 1.3.5+ compatible"""
    
    def __init__(self, path: str = "./chroma_data"):
        """
        Args:
            path: ChromaDB 데이터 저장 경로
        """
        # ChromaDB 1.3.5+에서는 Settings 클래스 없이 직접 설정
        self.client = chromadb.PersistentClient(
            path=path
        )
        logger.info("chromadb_initialized", path=path, version="1.3.5+")
    
    def get_or_create_collection(self, name: str, **kwargs):
        """컬렉션 생성 또는 가져오기"""
        return self.client.get_or_create_collection(
            name=name,
            metadata=kwargs.get("metadata", {})
        )
    
    def search(
        self,
        query_embedding: List[float],
        collection_name: str,
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        벡터 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            collection_name: 컬렉션 이름
            top_k: 반환할 결과 수
            where: 메타데이터 필터
        
        Returns:
            검색 결과 리스트
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            
            logger.info("chromadb_search", collection=collection_name, results=len(formatted_results))
            return formatted_results
        
        except Exception as e:
            logger.error("chromadb_search_error", error=str(e), collection=collection_name)
            raise
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """문서 추가"""
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("chromadb_documents_added", collection=collection_name, count=len(documents))
        except Exception as e:
            logger.error("chromadb_add_error", error=str(e))
            raise
    
    def health_check(self) -> bool:
        """연결 상태 확인"""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error("chromadb_health_check_failed", error=str(e))
            return False


class PineconeClient(VectorDBClient):
    """Pinecone 클라이언트 (프로덕션 환경) - Pinecone 8.0+ compatible"""
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        """
        Args:
            api_key: Pinecone API 키
            environment: Pinecone 환경 (deprecated in v8.0+)
            index_name: 인덱스 이름
        """
        try:
            from pinecone import Pinecone
            
            # Pinecone 8.0+ 새 API 초기화
            pc = Pinecone(api_key=api_key)
            
            # 인덱스 존재 확인
            indexes = pc.list_indexes()
            index_names = [idx.name for idx in indexes]
            
            if index_name not in index_names:
                raise ValueError(f"Pinecone index '{index_name}' not found")
            
            self.index = pc.Index(index_name)
            self.index_name = index_name
            logger.info("pinecone_initialized", index=index_name, version="8.0+")
        
        except ImportError:
            logger.error("pinecone_not_installed")
            raise ImportError("pinecone not installed. Run: pip install pinecone")
        except Exception as e:
            logger.error("pinecone_init_error", error=str(e))
            raise
    
    def get_or_create_collection(self, name: str, **kwargs):
        """Pinecone은 namespace를 사용"""
        return name  # namespace로 사용
    
    def search(
        self,
        query_embedding: List[float],
        collection_name: str,
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """벡터 검색"""
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=collection_name,
                filter=where,
                include_metadata=True
            )
            
            formatted_results = []
            for match in results['matches']:
                formatted_results.append({
                    'id': match['id'],
                    'document': match['metadata'].get('text', ''),
                    'metadata': match['metadata'],
                    'distance': match['score']
                })
            
            logger.info("pinecone_search", namespace=collection_name, results=len(formatted_results))
            return formatted_results
        
        except Exception as e:
            logger.error("pinecone_search_error", error=str(e))
            raise
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """문서 추가"""
        try:
            vectors = []
            for i, (doc_id, embedding, metadata) in enumerate(zip(ids, embeddings, metadatas)):
                metadata['text'] = documents[i]
                vectors.append((doc_id, embedding, metadata))
            
            self.index.upsert(vectors=vectors, namespace=collection_name)
            logger.info("pinecone_documents_added", namespace=collection_name, count=len(vectors))
        except Exception as e:
            logger.error("pinecone_add_error", error=str(e))
            raise
    
    def health_check(self) -> bool:
        """연결 상태 확인"""
        try:
            self.index.describe_index_stats()
            return True
        except Exception as e:
            logger.error("pinecone_health_check_failed", error=str(e))
            return False


def get_vectordb_client() -> VectorDBClient:
    """
    설정에 따라 VectorDB 클라이언트 반환
    
    Returns:
        VectorDB 클라이언트 인스턴스
    """
    if settings.vectordb_type == "chromadb":
        return ChromaDBClient(path=settings.chroma_path)
    elif settings.vectordb_type == "pinecone":
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required for Pinecone mode")
        return PineconeClient(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment,
            index_name=settings.pinecone_index_name
        )
    else:
        raise ValueError(f"Unsupported vectordb_type: {settings.vectordb_type}")
