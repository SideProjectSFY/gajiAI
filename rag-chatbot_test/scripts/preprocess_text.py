"""
텍스트 전처리 및 청킹 스크립트

원본 텍스트를 정제하고 200-500 단어 단위로 청킹합니다.
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict
import math


def clean_text(text: str) -> str:
    """
    텍스트 정제: Gutenberg 헤더/푸터 제거, 인코딩 정리
    
    Args:
        text: 원본 텍스트
    
    Returns:
        정제된 텍스트
    """
    # Gutenberg 프로젝트 헤더/푸터 패턴 제거
    # 헤더 제거 (보통 "*** START OF ..." 패턴)
    text = re.sub(r"\*\*\* START OF.*?\*\*\*", "", text, flags=re.DOTALL | re.IGNORECASE)
    
    # 푸터 제거 (보통 "*** END OF ..." 패턴)
    text = re.sub(r"\*\*\* END OF.*?\*\*\*", "", text, flags=re.DOTALL | re.IGNORECASE)
    
    # 여러 공백을 하나로
    text = re.sub(r"\s+", " ", text)
    
    # 줄바꿈 정리
    text = re.sub(r"\n\s*\n", "\n\n", text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text


def split_into_chunks(
    text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    min_chunk_size: int = 200
) -> List[Dict]:
    """
    텍스트를 청크로 분할
    
    Args:
        text: 정제된 텍스트
        chunk_size: 목표 청크 크기 (단어 수)
        chunk_overlap: 청크 간 겹치는 단어 수
        min_chunk_size: 최소 청크 크기
    
    Returns:
        청크 리스트 (각 청크는 text, word_count, chunk_index 포함)
    """
    # 문장 단위로 분할 (간단한 방법)
    sentences = re.split(r'[.!?]+\s+', text)
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    chunk_index = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # 문장의 단어 수 계산
        words = sentence.split()
        sentence_word_count = len(words)
        
        # 현재 청크에 추가하면 목표 크기를 초과하는지 확인
        if current_word_count + sentence_word_count > chunk_size and current_chunk:
            # 현재 청크 저장
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= min_chunk_size:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "word_count": current_word_count,
                    "char_count": len(chunk_text),
                })
                chunk_index += 1
            
            # 오버랩 처리: 마지막 몇 문장을 다음 청크 시작점으로
            if chunk_overlap > 0:
                overlap_words = []
                overlap_count = 0
                for sent in reversed(current_chunk):
                    sent_words = sent.split()
                    if overlap_count + len(sent_words) <= chunk_overlap:
                        overlap_words.insert(0, sent)
                        overlap_count += len(sent_words)
                    else:
                        break
                current_chunk = overlap_words
                current_word_count = overlap_count
            else:
                current_chunk = []
                current_word_count = 0
        
        # 문장 추가
        current_chunk.append(sentence)
        current_word_count += sentence_word_count
    
    # 마지막 청크 저장
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        if len(chunk_text.split()) >= min_chunk_size:
            chunks.append({
                "chunk_index": chunk_index,
                "text": chunk_text,
                "word_count": current_word_count,
                "char_count": len(chunk_text),
            })
    
    return chunks


def preprocess_book(input_file: str, output_dir: str, chunk_size: int = 400) -> Dict:
    """
    단일 책 파일 전처리
    
    Args:
        input_file: 입력 텍스트 파일 경로
        output_dir: 출력 디렉토리
        chunk_size: 청크 크기 (단어 수)
    
    Returns:
        전처리 결과 메타데이터
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 원본 텍스트 읽기
    print(f"📖 파일 읽기: {input_file}")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    
    # 메타데이터 읽기 (있는 경우)
    metadata_file = input_path.parent / f"{input_path.stem}.metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    
    # 텍스트 정제
    print("🧹 텍스트 정제 중...")
    cleaned_text = clean_text(raw_text)
    
    # 청킹
    print(f"✂️ 텍스트 청킹 중 (목표 크기: {chunk_size} 단어)...")
    chunks = split_into_chunks(cleaned_text, chunk_size=chunk_size)
    
    print(f"✅ {len(chunks)}개 청크 생성 완료")
    
    # 청크 저장
    book_id = metadata.get("gutenberg_id", input_path.stem)
    output_file = output_path / f"{book_id}_chunks.json"
    
    chunks_data = {
        "book_id": book_id,
        "title": metadata.get("title", input_path.stem),
        "author": metadata.get("author", "Unknown"),
        "total_chunks": len(chunks),
        "total_words": sum(c["word_count"] for c in chunks),
        "chunks": chunks,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 청크 저장 완료: {output_file}")
    print(f"   총 단어 수: {chunks_data['total_words']:,}")
    print(f"   평균 청크 크기: {chunks_data['total_words'] // len(chunks):,} 단어")
    
    return chunks_data


def main():
    parser = argparse.ArgumentParser(description="텍스트 전처리 및 청킹 스크립트")
    parser.add_argument(
        "--input",
        required=True,
        help="입력 텍스트 파일 경로 또는 디렉토리"
    )
    parser.add_argument(
        "--output",
        default="data/processed",
        help="출력 디렉토리 (기본: data/processed)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=400,
        help="청크 크기 (단어 수, 기본: 400)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # 단일 파일 처리
        preprocess_book(str(input_path), args.output, args.chunk_size)
    elif input_path.is_dir():
        # 디렉토리 내 모든 .txt 파일 처리
        txt_files = list(input_path.glob("*.txt"))
        print(f"📚 {len(txt_files)}개 파일 발견")
        
        for txt_file in txt_files:
            print(f"\n{'='*60}")
            preprocess_book(str(txt_file), args.output, args.chunk_size)
    else:
        print(f"❌ 입력 경로를 찾을 수 없습니다: {args.input}")


if __name__ == "__main__":
    main()

