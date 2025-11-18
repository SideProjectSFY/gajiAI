"""
Gemini Embedding API를 사용하여 텍스트 청크의 임베딩 생성

각 청크에 대해 768차원 벡터를 생성하고 저장합니다.
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict
import time

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai 라이브러리가 설치되지 않았습니다.")
    print("설치: pip install google-generativeai")
    exit(1)


def generate_embedding(text: str, model: str = "models/text-embedding-004") -> List[float]:
    """
    Gemini Embedding API로 텍스트 임베딩 생성
    
    Args:
        text: 임베딩을 생성할 텍스트
        model: 사용할 모델 (기본: text-embedding-004, 768차원)
    
    Returns:
        768차원 임베딩 벡터
    """
    try:
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"  # 문서 검색용
        )
        return result['embedding']
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        raise


def process_chunks_file(chunks_file: str, output_dir: str, api_key: str, batch_size: int = 10) -> Dict:
    """
    청크 파일을 읽어 임베딩 생성 및 저장
    
    Args:
        chunks_file: 청크 JSON 파일 경로
        output_dir: 출력 디렉토리
        api_key: Gemini API 키
        batch_size: 배치 크기 (API 호출 간 딜레이)
    
    Returns:
        처리 결과 메타데이터
    """
    # API 키 설정
    genai.configure(api_key=api_key)
    
    # 청크 파일 읽기
    print(f"📖 청크 파일 읽기: {chunks_file}")
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)
    
    book_id = chunks_data["book_id"]
    chunks = chunks_data["chunks"]
    total_chunks = len(chunks)
    
    print(f"📊 총 {total_chunks}개 청크 처리 예정")
    
    # 임베딩 생성
    embeddings = []
    processed = 0
    
    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        
        try:
            print(f"🔄 [{i+1}/{total_chunks}] 임베딩 생성 중...", end="\r")
            embedding = generate_embedding(text)
            
            # 청크에 임베딩 추가
            chunk["embedding"] = embedding
            embeddings.append(embedding)
            processed += 1
            
            # API 레이트 리밋 방지를 위한 딜레이
            if (i + 1) % batch_size == 0:
                time.sleep(1)  # 1초 대기
                
        except Exception as e:
            print(f"\n❌ 청크 {i+1} 처리 실패: {e}")
            # 임베딩 실패 시 None 저장
            chunk["embedding"] = None
            continue
    
    print(f"\n✅ {processed}/{total_chunks}개 청크 임베딩 생성 완료")
    
    # 결과 저장
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / f"{book_id}_embeddings.json"
    
    # 임베딩이 포함된 청크 데이터 저장
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 임베딩 저장 완료: {output_file}")
    
    # 통계 정보
    embedding_dim = len(embeddings[0]) if embeddings else 0
    print(f"📊 임베딩 차원: {embedding_dim}")
    print(f"📊 성공률: {processed/total_chunks*100:.1f}%")
    
    return {
        "book_id": book_id,
        "total_chunks": total_chunks,
        "processed_chunks": processed,
        "embedding_dim": embedding_dim,
        "output_file": str(output_file),
    }


def main():
    parser = argparse.ArgumentParser(description="Gemini Embedding API로 임베딩 생성")
    parser.add_argument(
        "--input",
        required=True,
        help="입력 청크 JSON 파일 경로 또는 디렉토리"
    )
    parser.add_argument(
        "--output",
        default="data/embeddings",
        help="출력 디렉토리 (기본: data/embeddings)"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API 키 (또는 GEMINI_API_KEY 환경변수 사용)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="배치 크기 (API 호출 간 딜레이, 기본: 10)"
    )
    
    args = parser.parse_args()
    
    # API 키 확인
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Gemini API 키가 필요합니다.")
        print("   --api-key 옵션 또는 GEMINI_API_KEY 환경변수를 설정하세요.")
        return
    
    input_path = Path(args.input)
    
    if input_path.is_file() and input_path.suffix == ".json":
        # 단일 파일 처리
        process_chunks_file(str(input_path), args.output, api_key, args.batch_size)
    elif input_path.is_dir():
        # 디렉토리 내 모든 _chunks.json 파일 처리
        chunk_files = list(input_path.glob("*_chunks.json"))
        print(f"📚 {len(chunk_files)}개 청크 파일 발견")
        
        for chunk_file in chunk_files:
            print(f"\n{'='*60}")
            process_chunks_file(str(chunk_file), args.output, api_key, args.batch_size)
    else:
        print(f"❌ 입력 경로를 찾을 수 없습니다: {args.input}")


if __name__ == "__main__":
    main()

