"""
VectorDB 클라이언트 (ChromaDB)

ChromaDB를 사용하여 벡터 임베딩을 저장하고 검색합니다.
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class VectorDBClient:
    """ChromaDB 클라이언트 - 벡터 임베딩 저장 및 검색"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        VectorDB 클라이언트 초기화
        
        Args:
            persist_directory: ChromaDB 데이터 저장 디렉토리 (None이면 자동 설정)
        """
        # 프로젝트 루트 경로
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        
        # 저장 디렉토리 설정
        if persist_directory is None:
            persist_directory = str(project_root / "chroma_data")
        
        # ChromaDB 클라이언트 생성
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 5개 컬렉션 초기화 (나중을 위해)
        self.collections = {
            "novel_passages": None,
            "characters": None,
            "locations": None,
            "events": None,
            "themes": None
        }
        self._initialize_collections()
        
        logger.info(f"VectorDB 클라이언트 초기화 완료: {persist_directory}")
    
    def _initialize_collections(self):
        """컬렉션 초기화 (이미 있으면 가져오기, 없으면 생성)"""
        for name in self.collections.keys():
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={
                        "description": f"{name} collection for RAG system",
                        "embedding_dimension": 768  # Gemini Embedding 768차원
                    }
                )
                logger.info(f"컬렉션 '{name}' 준비 완료")
            except Exception as e:
                logger.error(f"컬렉션 '{name}' 초기화 실패: {e}")
                self.collections[name] = None
    
    def get_collection(self, name: str):
        """
        컬렉션 가져오기
        
        Args:
            name: 컬렉션 이름
            
        Returns:
            ChromaDB Collection 객체 또는 None
        """
        return self.collections.get(name)
    
    def add_passages(
        self,
        novel_id: str,
        passages: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        소설 문장들을 VectorDB에 추가
        
        Args:
            novel_id: 소설 ID (Gutenberg ID)
            passages: 문장 텍스트 리스트
            embeddings: 임베딩 벡터 리스트 (768차원)
            metadatas: 메타데이터 리스트 (선택)
            
        Returns:
            성공 여부
        """
        try:
            collection = self.get_collection("novel_passages")
            if collection is None:
                logger.error("novel_passages 컬렉션을 찾을 수 없습니다")
                return False
            
            # ID 생성
            ids = [f"{novel_id}_chunk_{i}" for i in range(len(passages))]
            
            # 메타데이터 기본값 설정
            if metadatas is None:
                metadatas = [{"novel_id": novel_id} for _ in passages]
            else:
                # novel_id가 없으면 추가
                for meta in metadatas:
                    if "novel_id" not in meta:
                        meta["novel_id"] = novel_id
            
            # 배치로 추가 (ChromaDB는 자동으로 배치 처리)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=passages,
                metadatas=metadatas
            )
            
            logger.info(f"소설 {novel_id}: {len(passages)}개 문장 추가 완료")
            return True
            
        except Exception as e:
            logger.error(f"문장 추가 실패 (소설 {novel_id}): {e}")
            return False
    
    def search_passages(
        self,
        query_embedding: List[float],
        novel_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        유사한 문장 검색
        
        Args:
            query_embedding: 검색 쿼리 임베딩 (768차원)
            novel_id: 특정 소설만 검색 (None이면 전체)
            n_results: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        try:
            collection = self.get_collection("novel_passages")
            if collection is None:
                logger.error("novel_passages 컬렉션을 찾을 수 없습니다")
                return []
            
            # 필터 설정
            where = {}
            if novel_id:
                where["novel_id"] = novel_id
            
            # 검색
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where if where else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"문장 검색 실패: {e}")
            return []
    
    def get_collection_count(self, collection_name: str) -> int:
        """컬렉션의 문서 수 반환"""
        try:
            collection = self.get_collection(collection_name)
            if collection is None:
                return 0
            return collection.count()
        except Exception as e:
            logger.error(f"컬렉션 카운트 실패 ({collection_name}): {e}")
            return 0
    
    def delete_novel(self, novel_id: str) -> bool:
        """
        특정 소설의 모든 문장 삭제
        
        Args:
            novel_id: 소설 ID
            
        Returns:
            성공 여부
        """
        try:
            collection = self.get_collection("novel_passages")
            if collection is None:
                return False
            
            # novel_id로 필터링하여 삭제
            collection.delete(where={"novel_id": novel_id})
            logger.info(f"소설 {novel_id} 삭제 완료")
            return True
            
        except Exception as e:
            logger.error(f"소설 삭제 실패 ({novel_id}): {e}")
            return False
    
    def health_check(self) -> bool:
        """
        VectorDB 연결 상태 확인
        
        Returns:
            연결 성공 여부
        """
        try:
            # 간단한 연결 테스트: 컬렉션 목록 조회
            self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"VectorDB health check 실패: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        모든 컬렉션 목록 반환
        
        Returns:
            컬렉션 이름 리스트
        """
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"컬렉션 목록 조회 실패: {e}")
            return []
    
    def add_characters(
        self,
        novel_id: str,
        characters: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        캐릭터를 VectorDB에 추가
        
        Args:
            novel_id: 소설 ID
            characters: 캐릭터 리스트 (각 캐릭터는 dict 형태)
            embeddings: 임베딩 벡터 리스트 (선택, 나중에 생성 가능)
        
        Returns:
            성공 여부
        """
        try:
            collection = self.get_collection("characters")
            if collection is None:
                logger.error("characters 컬렉션을 찾을 수 없습니다")
                return False
            
            ids = []
            documents = []
            metadatas = []
            
            for char in characters:
                char_id = char.get("id")
                common_name = char.get("common_name", "")
                
                # VectorDB ID 생성
                vectordb_id = f"char-{novel_id}-{char_id}"
                
                # 캐릭터 설명 텍스트 생성
                description_parts = []
                if char.get("description"):
                    description_parts.append(char.get("description"))
                description_parts.append(f"Character ID: {char_id}")
                description_parts.append(f"Names: {', '.join(char.get('names', []))}")
                description_parts.append(f"Main character: {char.get('main_character', False)}")
                
                document_text = "\n".join(description_parts)
                
                # 메타데이터 구성
                metadata = {
                    "novel_id": novel_id,
                    "character_id": str(char_id),
                    "name": common_name,
                    "names": ", ".join(char.get("names", [])),  # 쉼표로 구분된 문자열
                    "main_character": char.get("main_character", False),
                    "role": "main" if char.get("main_character", False) else "supporting"
                }
                
                # portrait_prompt가 있으면 추가
                if char.get("portrait_prompt"):
                    metadata["portrait_prompt"] = char.get("portrait_prompt")
                
                ids.append(vectordb_id)
                documents.append(document_text)
                metadatas.append(metadata)
            
            # 임베딩이 있으면 함께 저장, 없으면 텍스트만 저장 (나중에 업데이트 가능)
            if embeddings and len(embeddings) == len(ids):
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            else:
                # 임베딩 없이 저장 (나중에 업데이트 가능)
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            
            logger.info(f"{len(ids)}개 캐릭터를 VectorDB에 저장했습니다 (novel_id: {novel_id})")
            return True
            
        except Exception as e:
            logger.error(f"캐릭터 저장 실패: {e}", exc_info=True)
            return False


# 전역 VectorDB 클라이언트 인스턴스
_vectordb_client: Optional[VectorDBClient] = None


def get_vectordb_client() -> VectorDBClient:
    """
    VectorDB 클라이언트 싱글톤 반환
    
    Returns:
        VectorDBClient 인스턴스
    """
    global _vectordb_client
    
    if _vectordb_client is None:
        from app.config import settings
        # settings에서 chromadb_path 또는 기본값 사용
        persist_directory = getattr(settings, 'chromadb_path', "./chroma_data")
        _vectordb_client = VectorDBClient(persist_directory=persist_directory)
    
    return _vectordb_client

