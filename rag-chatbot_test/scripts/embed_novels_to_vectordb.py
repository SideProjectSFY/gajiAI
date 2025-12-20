"""
소설 원본 텍스트를 Gemini Embedding으로 임베딩 처리하여 ChromaDB에 저장

사용법:
    python scripts/embed_novels_to_vectordb.py
    python scripts/embed_novels_to_vectordb.py --novel-id 84  # 특정 소설만
    python scripts/embed_novels_to_vectordb.py --reset  # 기존 데이터 삭제 후 재생성
    python scripts/embed_novels_to_vectordb.py --batch-size 5 --delay 5.0  # 무료 티어용

주의사항:
    - 무료 티어에서는 Embedding API 할당량이 매우 제한적입니다
    - 배치 크기를 작게 (5-10) 하고 대기 시간을 길게 (5-10초) 설정하는 것을 권장합니다
    - 429 에러 발생 시 자동으로 재시도하며, 여러 API 키가 있으면 자동 전환합니다
"""

import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google import genai
from google.genai import types
from app.services.vectordb_client import VectorDBClient
from app.services.api_key_manager import get_api_key_manager


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    텍스트를 청크로 분할
    
    Args:
        text: 원본 텍스트
        chunk_size: 청크 크기 (단어 수)
        overlap: 오버랩 단어 수
        
    Returns:
        청크 리스트
    """
    words = text.split()
    chunks = []
    
    if not words:
        return chunks
    
    i = 0
    while i < len(words):
        chunk = words[i:i + chunk_size]
        if chunk:
            chunks.append(' '.join(chunk))
        i += chunk_size - overlap
        
        # 마지막 청크가 너무 작으면 이전 청크와 병합
        if i < len(words) and len(words) - i < chunk_size // 2:
            break
    
    return chunks


def generate_embeddings_batch(
    client: genai.Client,
    texts: List[str],
    batch_size: int = 10,
    api_key_manager=None,
    max_retries: int = 3,
    initial_delay: float = 2.0
) -> List[List[float]]:
    """
    배치로 임베딩 생성 (429 에러 처리 포함)
    
    Args:
        client: Gemini API 클라이언트
        texts: 텍스트 리스트
        batch_size: 배치 크기
        api_key_manager: API 키 매니저 (선택)
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 대기 시간 (초)
        
    Returns:
        임베딩 벡터 리스트 (768차원)
    """
    all_embeddings = []
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        success = False
        last_error = None

        for retry in range(max_retries):
            try:
                # Gemini Embedding API 호출
                result = client.models.embed_content(
                    model="models/gemini-embedding-001",
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=768
                    )
                )
                
                # 결과 파싱
                if hasattr(result, 'embeddings'):
                    batch_embeddings = [emb.values for emb in result.embeddings]
                elif hasattr(result, 'embedding'):
                    batch_embeddings = [[result.embedding.values]]
                else:
                    # 다양한 응답 형식 처리
                    batch_embeddings = []
                    for emb in result:
                        if isinstance(emb, list):
                            batch_embeddings.append(emb)
                        elif hasattr(emb, 'values'):
                            batch_embeddings.append(emb.values)
                        else:
                            batch_embeddings.append(list(emb))
                
                all_embeddings.extend(batch_embeddings)
                success = True
                break
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # 429 에러 또는 할당량 초과 에러 처리
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                    # API 키 전환 시도
                    if api_key_manager:
                        if api_key_manager.switch_to_next_key():
                            print(f"  [키 전환] 다음 API 키로 전환 (배치 {batch_num})")
                            new_key = api_key_manager.get_current_key()
                            client = genai.Client(api_key=new_key)
                            wait_time = (2 ** retry) * initial_delay
                            print(f"  [대기] {wait_time}초 대기 후 재시도...")
                            time.sleep(wait_time)
                            continue
                    
                    # 키 전환이 안 되면 더 긴 대기 시간
                    wait_time = (2 ** retry) * (initial_delay * 2)
                    print(f"  [할당량 초과] {wait_time}초 대기 후 재시도 (배치 {batch_num}, 시도 {retry + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                
                # 다른 에러는 재시도
                print(f"  [오류] 배치 {batch_num} 임베딩 실패 (시도 {retry + 1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    wait_time = (2 ** retry) * initial_delay
                    time.sleep(wait_time)
        
        if not success:
            print(f"  [최종 실패] 배치 {batch_num} 임베딩 실패: {last_error}")
            # 실패한 배치는 빈 임베딩으로 채움 (부분 성공 허용)
            all_embeddings.extend([[] for _ in batch])
        
        # 배치 간 대기 시간
        if i + batch_size < len(texts):
            time.sleep(initial_delay)
    
    return all_embeddings


def embed_novel(
    client: genai.Client,
    vectordb: VectorDBClient,
    novel_file_path: Path,
    novel_metadata: Dict,
    reset: bool = False,
    api_key_manager=None,
    batch_size: int = 10,
    batch_delay: float = 2.0,
    chunk_size: int = 300
) -> bool:
    """
    소설 하나를 임베딩 처리하여 VectorDB에 저장
    
    Args:
        client: Gemini API 클라이언트
        vectordb: VectorDB 클라이언트
        novel_file_path: 소설 파일 경로
        novel_metadata: 소설 메타데이터
        reset: 기존 데이터 삭제 여부
        api_key_manager: API 키 매니저 (선택)
        batch_size: 배치 크기
        batch_delay: 배치 간 대기 시간 (초)
        chunk_size: 청크 크기 (단어 수)
        
    Returns:
        성공 여부
    """
    novel_id = str(novel_metadata['gutenberg_id'])
    title = novel_metadata['title']
    
    print(f"\n[처리 중] {title} (ID: {novel_id})")
    
    # 기존 데이터 삭제
    if reset:
        print(f"  [삭제] 기존 데이터 삭제 중...")
        vectordb.delete_novel(novel_id)
    
    # 파일 읽기
    try:
        with open(novel_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"  [오류] 파일 읽기 실패: {e}")
        return False
    
    if not text.strip():
        print(f"  [경고] 빈 파일입니다")
        return False
    
    # 텍스트 청킹
    print(f"  [청킹] 텍스트 분할 중... (청크 크기: {chunk_size}단어)")
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=50)
    print(f"  [청킹] {len(chunks)}개 청크 생성 완료")
    
    if not chunks:
        print(f"  [경고] 청크가 생성되지 않았습니다")
        return False
    
    # 임베딩 생성
    print(f"  [임베딩] Gemini Embedding API 호출 중... (배치 크기: {batch_size}, 대기: {batch_delay}초)")
    try:
        embeddings = generate_embeddings_batch(
            client, 
            chunks, 
            batch_size=batch_size,
            api_key_manager=api_key_manager,
            max_retries=3,
            initial_delay=batch_delay
        )
        
        # 유효한 임베딩만 필터링
        valid_chunks = []
        valid_embeddings = []
        valid_metadatas = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding and len(embedding) == 768:
                valid_chunks.append(chunk)
                valid_embeddings.append(embedding)
                
                # 메타데이터 구성 (saved_books_info.json의 모든 정보 활용)
                chunk_metadata = {
                    "novel_id": novel_id,
                    "title": novel_metadata.get('title', title),
                    "author": novel_metadata.get('author', ''),
                    "chunk_index": i,
                    "word_count": len(chunk.split())
                }
                
                # saved_books_info.json에서 추가 정보 포함
                if 'index' in novel_metadata:
                    chunk_metadata['novel_index'] = novel_metadata['index']
                if 'filepath' in novel_metadata:
                    chunk_metadata['filepath'] = novel_metadata['filepath']
                if 'text_length' in novel_metadata:
                    chunk_metadata['novel_text_length'] = novel_metadata['text_length']
                
                valid_metadatas.append(chunk_metadata)
        
        print(f"  [임베딩] {len(valid_embeddings)}/{len(chunks)}개 임베딩 생성 완료")
        
        if not valid_embeddings:
            print(f"  [경고] 유효한 임베딩이 없습니다. 소설 {title} 처리를 건너뜀.")
            return False
        
        # VectorDB에 저장
        print(f"  [저장] VectorDB에 저장 중...")
        success = vectordb.add_passages(
            novel_id=novel_id,
            passages=valid_chunks,
            embeddings=valid_embeddings,
            metadatas=valid_metadatas
        )
        
        if success:
            print(f"✅ 소설 {title} 임베딩 및 VectorDB 저장 완료.")
            return True
        else:
            print(f"  [오류] VectorDB 저장 실패")
            return False
            
    except Exception as e:
        print(f"  [오류] 소설 {title} 임베딩 및 저장 실패: {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Embed novel texts to ChromaDB using Gemini Embedding API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 모든 소설 처리 (기본 설정)
  python scripts/embed_novels_to_vectordb.py
  
  # 특정 소설만 처리
  python scripts/embed_novels_to_vectordb.py --novel-id 84
  
  # 무료 티어용 (안정적)
  python scripts/embed_novels_to_vectordb.py --batch-size 5 --delay 10.0
  
  # 기존 데이터 삭제 후 재생성
  python scripts/embed_novels_to_vectordb.py --reset
        """
    )
    parser.add_argument(
        "--novel-id", 
        type=int, 
        help="Specific Gutenberg ID of the novel to embed."
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Delete existing data for the novel(s) before re-embedding."
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=10, 
        help="Number of text chunks to send per embedding API request (default: 10)."
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=2.0, 
        help="Delay in seconds between embedding API batch requests (default: 2.0)."
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=300, 
        help="Chunk size in words (default: 300)."
    )
    
    args = parser.parse_args()

    # API 키 매니저 초기화
    api_key_manager = get_api_key_manager()
    initial_key = api_key_manager.get_current_key()
    client = genai.Client(api_key=initial_key)
    
    # VectorDB 클라이언트 초기화
    vectordb = VectorDBClient()
    
    # 소설 정보 로드
    origin_txt_dir = project_root / "data" / "origin_txt"
    with open(origin_txt_dir / "saved_books_info.json", 'r', encoding='utf-8') as f:
        books_info = json.load(f)
    
    # 처리할 소설 선택
    books_to_process = []
    if args.novel_id:
        selected_book = next(
            (book for book in books_info['books'] if book['gutenberg_id'] == args.novel_id), 
            None
        )
        if selected_book:
            books_to_process.append(selected_book)
        else:
            print(f"오류: Gutenberg ID {args.novel_id}에 해당하는 소설을 찾을 수 없습니다.")
            return
    else:
        books_to_process = books_info['books']
    
    print(f"\n=== 소설 임베딩 처리 시작 ===")
    print(f"처리할 소설 수: {len(books_to_process)}")
    print(f"배치 크기: {args.batch_size}")
    print(f"배치 간 대기: {args.delay}초")
    print(f"청크 크기: {args.chunk_size}단어")
    print(f"API 키 수: {len(api_key_manager.api_keys)}")
    print("=" * 50)
    
    # 소설 처리
    success_count = 0
    for book in tqdm(books_to_process, desc="Processing novels"):
        book_path = origin_txt_dir / f"{book['gutenberg_id']}_{book['title']}.txt"
        
        if not book_path.exists():
            print(f"경고: 파일이 존재하지 않습니다: {book_path}")
            continue
        
        if embed_novel(
            client,
            vectordb,
            book_path,
            book,
            reset=args.reset,
            api_key_manager=api_key_manager,
            batch_size=args.batch_size,
            batch_delay=args.delay,
            chunk_size=args.chunk_size
        ):
            success_count += 1
        
        # 소설 처리 후 API 키 로테이션 (다음 소설을 위해, 실패 표시 없이 순환만)
        if api_key_manager.switch_to_next_key(mark_current_as_failed=False):
            client = genai.Client(api_key=api_key_manager.get_current_key())
            print(f"  [키 로테이션] 다음 소설을 위해 API 키 전환 완료.")
        
        # 소설 처리 간 대기 시간 (전체 프로세스 안정성)
        if book != books_to_process[-1]:  # 마지막 소설이 아니면
            time.sleep(args.delay * 2)
    
    print(f"\n=== 임베딩 처리 완료 ===")
    print(f"총 {len(books_to_process)}개 소설 중 {success_count}개 성공적으로 처리.")
    
    # VectorDB 통계
    collection_count = vectordb.get_collection_count("novel_passages")
    print(f"VectorDB에 저장된 총 청크 수: {collection_count}")


if __name__ == "__main__":
    main()

