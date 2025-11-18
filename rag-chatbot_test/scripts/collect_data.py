"""
Gutenberg 데이터 수집 스크립트

두 가지 방법을 지원:
1. Hugging Face datasets (추천 - 빠른 시작)
2. gutenbergpy (특정 책 선택 시)
"""

import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Optional

# 방법 1: Hugging Face datasets (추천)
def collect_with_datasets(book_titles: List[str], output_dir: str) -> List[Dict]:
    """
    Hugging Face datasets를 사용하여 Gutenberg 데이터 수집
    
    Args:
        book_titles: 수집할 책 제목 리스트 (예: ["Pride and Prejudice", "The Great Gatsby"])
        output_dir: 저장할 디렉토리 경로
    
    Returns:
        수집된 책 데이터 리스트
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ datasets 라이브러리가 설치되지 않았습니다.")
        print("설치: pip install datasets")
        return []
    
    print("📚 Hugging Face datasets에서 데이터 로드 중...")
    
    # 데이터셋 로드 (전체 다운로드는 시간이 걸릴 수 있음)
    ds = load_dataset("sedthh/gutenberg_english", split="train")
    
    print(f"✅ 총 {len(ds)}개 책 로드 완료")
    
    collected_books = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 책 제목으로 필터링
    import json
    
    # 불용어 제거 (검색에서 제외할 단어)
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    
    for title_keyword in book_titles:
        print(f"\n🔍 '{title_keyword}' 검색 중...")
        
        # 검색 키워드에서 불용어 제거하고 핵심 키워드만 추출
        keywords = [kw.lower() for kw in title_keyword.split() if kw.lower() not in stopwords]
        
        if not keywords:
            # 불용어만 있으면 원본 키워드 사용
            keywords = [kw.lower() for kw in title_keyword.split()]
        
        print(f"   검색 키워드: {keywords}")
        
        # METADATA에서 제목을 파싱해서 검색
        matching_books = []
        max_search = min(50000, len(ds))  # 최대 50000개까지 검색
        
        for i in range(max_search):
            try:
                book = ds[i]
                # METADATA 파싱
                metadata_str = book.get("METADATA", "")
                if not metadata_str:
                    continue
                
                metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                title = metadata.get("title", "")
                
                # 제목에서 이스케이프 문자 제거 후 검색
                title_clean = title.replace("\r\n", " ").replace("\n", " ").lower()
                
                # 모든 핵심 키워드가 제목에 포함되어 있는지 확인 (더 정확한 매칭)
                if all(keyword in title_clean for keyword in keywords):
                    matching_books.append((i, book, metadata))
                    print(f"   ✅ 매칭 발견: '{title.replace(chr(13), ' ').replace(chr(10), ' ').strip()}' (인덱스: {i})")
                    break  # 첫 번째 정확한 매칭만 사용
            except Exception as e:
                if i < 10:  # 처음 10개만 에러 출력
                    print(f"   ⚠️ 인덱스 {i} 처리 중 오류: {e}")
                continue
        
        if len(matching_books) == 0:
            print(f"⚠️ '{title_keyword}'를 찾을 수 없습니다 (검색 범위: {max_search:,}개).")
            print(f"   시도한 키워드: {keywords}")
            continue
        
        # 첫 번째 매칭 결과 사용
        idx, book, metadata = matching_books[0]
        
        # 제목 정리
        title = metadata.get("title", "Unknown")
        title_clean = title.replace("\r\n", " ").replace("\n", " ").strip()
        
        # 저자 추출 (authors는 리스트일 수 있음)
        authors = metadata.get("authors", metadata.get("author", "Unknown"))
        if isinstance(authors, list):
            author = ", ".join(authors) if authors else "Unknown"
        elif isinstance(authors, str):
            author = authors
        else:
            author = "Unknown"
        
        # Gutenberg ID (text_id 사용)
        gutenberg_id = str(metadata.get("text_id", ""))
        
        book_data = {
            "title": title_clean,
            "author": author,
            "text": book.get("TEXT", ""),
            "gutenberg_id": gutenberg_id,
        }
        
        # 파일로 저장
        filename = f"{book_data['title'].replace(' ', '_').replace('/', '_')}.txt"
        filepath = output_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(book_data["text"])
        
        # 메타데이터 저장
        metadata_path = output_path / f"{filename}.metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": book_data["title"],
                "author": book_data["author"],
                "gutenberg_id": book_data["gutenberg_id"],
                "filepath": str(filepath),
                "text_length": len(book_data["text"]),
            }, f, indent=2, ensure_ascii=False)
        
        collected_books.append(book_data)
        print(f"✅ '{book_data['title']}' 저장 완료: {filepath}")
        print(f"   저자: {book_data['author']}")
        print(f"   텍스트 길이: {len(book_data['text']):,} 문자")
    
    return collected_books


# 방법 2: gutenbergpy (특정 책 ID로 다운로드)
def collect_with_gutenbergpy(book_ids: List[int], output_dir: str) -> List[Dict]:
    """
    gutenbergpy를 사용하여 특정 책 ID로 데이터 수집
    
    Args:
        book_ids: Gutenberg 책 ID 리스트 (예: [1342, 64317])
        output_dir: 저장할 디렉토리 경로
    
    Returns:
        수집된 책 데이터 리스트
    """
    try:
        import gutenbergpy.textget
        import gutenbergpy.query
    except ImportError:
        print("❌ gutenbergpy 라이브러리가 설치되지 않았습니다.")
        print("설치: pip install gutenbergpy")
        return []
    
    print("📚 gutenbergpy로 데이터 수집 중...")
    
    collected_books = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for book_id in book_ids:
        try:
            print(f"\n🔍 책 ID {book_id} 다운로드 중...")
            
            # 텍스트 다운로드
            raw_text = gutenbergpy.textget.get_text_by_id(book_id)
            
            # 바이트를 문자열로 변환
            if isinstance(raw_text, bytes):
                text = raw_text.decode("utf-8", errors="ignore")
            else:
                text = str(raw_text)
            
            # 메타데이터 조회
            try:
                meta = gutenbergpy.query.get_metadata_by_ID(book_id)
                title = meta.get("Title", [f"Book_{book_id}"])[0] if meta else f"Book_{book_id}"
                author = meta.get("Author", ["Unknown"])[0] if meta else "Unknown"
            except:
                title = f"Book_{book_id}"
                author = "Unknown"
            
            book_data = {
                "title": title,
                "author": author,
                "text": text,
                "gutenberg_id": str(book_id),
            }
            
            # 파일로 저장
            filename = f"{title.replace(' ', '_').replace('/', '_')}.txt"
            filepath = output_path / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            
            # 메타데이터 저장
            metadata_path = output_path / f"{filename}.metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump({
                    "title": title,
                    "author": author,
                    "gutenberg_id": str(book_id),
                    "filepath": str(filepath),
                    "text_length": len(text),
                }, f, indent=2, ensure_ascii=False)
            
            collected_books.append(book_data)
            print(f"✅ '{title}' 저장 완료: {filepath}")
            print(f"   저자: {author}")
            print(f"   텍스트 길이: {len(text):,} 문자")
            
        except Exception as e:
            print(f"❌ 책 ID {book_id} 다운로드 실패: {e}")
            continue
    
    return collected_books


def main():
    parser = argparse.ArgumentParser(description="Gutenberg 데이터 수집 스크립트")
    parser.add_argument(
        "--method",
        choices=["datasets", "gutenbergpy"],
        default="datasets",
        help="사용할 수집 방법 (기본: datasets)"
    )
    parser.add_argument(
        "--titles",
        nargs="+",
        help="datasets 방법 사용 시: 책 제목 리스트 (예: 'Pride and Prejudice' 'The Great Gatsby')"
    )
    parser.add_argument(
        "--ids",
        type=int,
        nargs="+",
        help="gutenbergpy 방법 사용 시: Gutenberg 책 ID 리스트 (예: 1342 64317)"
    )
    parser.add_argument(
        "--output",
        default="data/raw",
        help="출력 디렉토리 (기본: data/raw)"
    )
    
    args = parser.parse_args()
    
    if args.method == "datasets":
        if not args.titles:
            print("❌ datasets 방법 사용 시 --titles 옵션이 필요합니다.")
            print("예시: python collect_data.py --method datasets --titles 'Pride and Prejudice'")
            return
        
        books = collect_with_datasets(args.titles, args.output)
        
    elif args.method == "gutenbergpy":
        if not args.ids:
            print("❌ gutenbergpy 방법 사용 시 --ids 옵션이 필요합니다.")
            print("예시: python collect_data.py --method gutenbergpy --ids 1342 64317")
            return
        
        books = collect_with_gutenbergpy(args.ids, args.output)
    
    print(f"\n✅ 총 {len(books)}개 책 수집 완료!")
    print(f"📁 저장 위치: {args.output}")


if __name__ == "__main__":
    main()

