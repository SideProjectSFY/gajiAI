"""
ChromaDB에 청크와 임베딩 임포트 스크립트

전처리된 청크와 임베딩을 ChromaDB 벡터 저장소에 저장합니다.
"""

import argparse
import json
import uuid
from pathlib import Path
from typing import List, Dict

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("❌ chromadb 라이브러리가 설치되지 않았습니다.")
    print("설치: pip install chromadb")
    exit(1)


def import_book_embeddings(
    embeddings_file: str,
    collection_name: str = "novel_passages",
    chroma_path: str = "./chroma_data"
) -> Dict:
    """
    임베딩 파일을 ChromaDB에 임포트
    
    Args:
        embeddings_file: 임베딩이 포함된 JSON 파일 경로
        collection_name: ChromaDB 컬렉션 이름
        chroma_path: ChromaDB 데이터 저장 경로
    
    Returns:
        임포트 결과 메타데이터
    """
    # ChromaDB 클라이언트 초기화
    print(f"🔌 ChromaDB 연결 중... (경로: {chroma_path})")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # 컬렉션 가져오기 또는 생성
    try:
        collection = client.get_collection(name=collection_name)
        print(f"✅ 기존 컬렉션 사용: {collection_name}")
    except:
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 코사인 유사도 사용
        )
        print(f"✅ 새 컬렉션 생성: {collection_name}")
    
    # 임베딩 파일 읽기
    print(f"📖 임베딩 파일 읽기: {embeddings_file}")
    with open(embeddings_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    book_id = data["book_id"]
    chunks = data["chunks"]
    
    # 임베딩이 있는 청크만 필터링
    valid_chunks = [c for c in chunks if c.get("embedding") is not None]
    total_chunks = len(valid_chunks)
    
    print(f"📊 {total_chunks}개 청크 임포트 예정")
    
    # 배치로 임포트 (ChromaDB는 배치 추가 지원)
    batch_size = 100
    imported = 0
    
    for i in range(0, total_chunks, batch_size):
        batch = valid_chunks[i:i+batch_size]
        
        # ChromaDB 형식으로 변환
        ids = [f"{book_id}_chunk_{c['chunk_index']}" for c in batch]
        embeddings = [c["embedding"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = [
            {
                "book_id": book_id,
                "title": data["title"],
                "author": data["author"],
                "chunk_index": c["chunk_index"],
                "word_count": c["word_count"],
                "char_count": c["char_count"],
            }
            for c in batch
        ]
        
        # ChromaDB에 추가
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        imported += len(batch)
        print(f"🔄 [{imported}/{total_chunks}] 청크 임포트 중...", end="\r")
    
    print(f"\n✅ {imported}개 청크 임포트 완료")
    
    # 검증: 컬렉션에 실제로 저장되었는지 확인
    count = collection.count()
    print(f"📊 컬렉션 총 청크 수: {count}")
    
    return {
        "book_id": book_id,
        "imported_chunks": imported,
        "collection_name": collection_name,
        "collection_count": count,
    }


def verify_import(collection_name: str = "novel_passages", chroma_path: str = "./chroma_data"):
    """
    ChromaDB 임포트 검증: 샘플 쿼리 테스트
    
    Args:
        collection_name: 컬렉션 이름
        chroma_path: ChromaDB 경로
    """
    print("\n🔍 임포트 검증 중...")
    
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name=collection_name)
    
    # 컬렉션 정보
    count = collection.count()
    print(f"✅ 컬렉션 '{collection_name}': {count}개 문서")
    
    # 샘플 쿼리 테스트
    if count > 0:
        print("\n🧪 샘플 검색 테스트...")
        
        # 첫 번째 문서 가져오기
        sample = collection.get(limit=1)
        if sample["ids"]:
            print(f"   샘플 문서 ID: {sample['ids'][0]}")
            print(f"   샘플 텍스트 (처음 100자): {sample['documents'][0][:100]}...")
        
        # 간단한 텍스트 검색 (임베딩 없이)
        # 실제로는 Gemini Embedding API로 쿼리 임베딩을 생성해야 함
        print("   ⚠️ 실제 검색 테스트는 Gemini Embedding API가 필요합니다.")


def main():
    parser = argparse.ArgumentParser(description="ChromaDB에 청크와 임베딩 임포트")
    parser.add_argument(
        "--input",
        required=True,
        help="입력 임베딩 JSON 파일 경로 또는 디렉토리"
    )
    parser.add_argument(
        "--collection",
        default="novel_passages",
        help="ChromaDB 컬렉션 이름 (기본: novel_passages)"
    )
    parser.add_argument(
        "--chroma-path",
        default="./chroma_data",
        help="ChromaDB 데이터 저장 경로 (기본: ./chroma_data)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="임포트 후 검증 실행"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file() and input_path.suffix == ".json":
        # 단일 파일 처리
        import_book_embeddings(
            str(input_path),
            args.collection,
            args.chroma_path
        )
    elif input_path.is_dir():
        # 디렉토리 내 모든 _embeddings.json 파일 처리
        embedding_files = list(input_path.glob("*_embeddings.json"))
        print(f"📚 {len(embedding_files)}개 임베딩 파일 발견")
        
        for embedding_file in embedding_files:
            print(f"\n{'='*60}")
            import_book_embeddings(
                str(embedding_file),
                args.collection,
                args.chroma_path
            )
    else:
        print(f"❌ 입력 경로를 찾을 수 없습니다: {args.input}")
        return
    
    # 검증
    if args.verify:
        verify_import(args.collection, args.chroma_path)


if __name__ == "__main__":
    main()

