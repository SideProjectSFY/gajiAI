"""
로컬 Gutenberg 데이터셋에서 책 검색 및 저장 스크립트

로컬에 저장된 데이터셋에서 책 제목으로 검색하여 개별 txt 파일로 저장합니다.
"""

import argparse
import json
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datasets import load_from_disk, Dataset


def load_local_dataset(dataset_path: str) -> Dataset:
    """
    로컬에 저장된 데이터셋 로드
    
    Args:
        dataset_path: 데이터셋 경로
    
    Returns:
        Dataset 객체
    """
    print(f"[로딩] 로컬 데이터셋 로드 중: {dataset_path}")
    
    try:
        # Arrow 파일에서 직접 로드
        from datasets import load_dataset
        ds = load_dataset(
            "arrow",
            data_files={
                "train": str(Path(dataset_path) / "default/0.0.0/*/gutenberg_english-train-*.arrow")
            },
            split="train"
        )
        print(f"[완료] 총 {len(ds):,}개 책 로드 완료")
        return ds
    except Exception as e:
        print(f"[오류] 데이터셋 로드 실패: {e}")
        raise


def calculate_text_quality_score(text: str, text_length: int, gutenberg_id: str) -> Tuple[float, Dict]:
    """
    텍스트 품질 점수 계산
    
    여러 기준을 종합하여 가장 완전하고 깨끗한 버전을 선택합니다.
    
    평가 기준:
    1. 텍스트 길이 (긴 것이 더 완전함)
    2. Gutenberg ID (낮을수록 오래된 원본, 더 신뢰도 높음)
    3. 구조적 완성도 (Chapter, Letter 등 구조 요소)
    4. 텍스트 품질 (특수문자, 깨진 문자 비율)
    
    Args:
        text: 텍스트 내용
        text_length: 텍스트 길이
        gutenberg_id: Gutenberg ID
    
    Returns:
        (품질 점수, 상세 정보)
    """
    scores = {}
    
    # 1. 길이 점수 (0-40점): 긴 것이 더 완전함
    # 정규화: 100,000자 기준
    length_score = min(40, (text_length / 100000) * 40)
    scores['length'] = length_score
    
    # 2. ID 점수 (0-30점): 낮은 ID가 더 신뢰도 높음
    # ID가 낮을수록 높은 점수 (10000 이하는 만점)
    try:
        id_num = int(gutenberg_id)
        if id_num <= 10000:
            id_score = 30
        elif id_num <= 50000:
            id_score = 20
        else:
            id_score = 10
    except:
        id_score = 5
    scores['id'] = id_score
    
    # 3. 구조 점수 (0-20점): 목차, 챕터 구조가 있으면 더 완전함
    structure_score = 0
    
    # 샘플링: 처음 5000자만 검사 (성능 최적화)
    sample_text = text[:5000].lower()
    
    # 목차 존재 여부
    if 'contents' in sample_text or 'table of contents' in sample_text:
        structure_score += 5
    
    # Chapter 구조
    chapter_pattern = r'chapter\s+\d+|chapter\s+[ivxlcdm]+'
    chapter_count = len(re.findall(chapter_pattern, sample_text, re.IGNORECASE))
    if chapter_count >= 3:
        structure_score += 10
    elif chapter_count >= 1:
        structure_score += 5
    
    # Letter 구조 (서간체 소설)
    letter_pattern = r'letter\s+\d+|letter\s+[ivxlcdm]+'
    letter_count = len(re.findall(letter_pattern, sample_text, re.IGNORECASE))
    if letter_count >= 2:
        structure_score += 5
    
    scores['structure'] = min(20, structure_score)
    
    # 4. 품질 점수 (0-10점): 깨끗한 텍스트
    quality_score = 10
    
    # 샘플링: 중간 1000자 검사
    mid_start = len(text) // 2
    quality_sample = text[mid_start:mid_start+1000]
    
    # 비정상적인 문자 비율 (제어문자, 과도한 특수문자)
    control_chars = sum(1 for c in quality_sample if ord(c) < 32 and c not in '\n\r\t')
    if control_chars > 10:
        quality_score -= 5
    
    # 과도한 줄바꿈 (연속 3개 이상)
    excessive_newlines = len(re.findall(r'\n{4,}', quality_sample))
    if excessive_newlines > 5:
        quality_score -= 2
    
    scores['quality'] = max(0, quality_score)
    
    # 총점 계산 (0-100점)
    total_score = sum(scores.values())
    
    return total_score, scores


def dataset_to_dataframe(ds: Dataset) -> pd.DataFrame:
    """
    Dataset을 DataFrame으로 변환
    
    Args:
        ds: Dataset 객체
    
    Returns:
        pandas DataFrame
    """
    print("[변환] Dataset을 DataFrame으로 변환 중...")
    
    # 필요한 컬럼만 추출
    data = []
    for i, item in enumerate(ds):
        if (i + 1) % 5000 == 0:
            print(f"  진행: {i+1:,}/{len(ds):,} ({(i+1)/len(ds)*100:.1f}%)")
        
        try:
            metadata_str = item.get("METADATA", "")
            if not metadata_str:
                continue
            
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            
            title = metadata.get("title", "").replace("\r\n", " ").replace("\n", " ").strip()
            authors = metadata.get("authors", metadata.get("author", "Unknown"))
            
            if isinstance(authors, list):
                author = ", ".join(authors) if authors else "Unknown"
            elif isinstance(authors, str):
                author = authors
            else:
                author = "Unknown"
            
            gutenberg_id = str(metadata.get("text_id", ""))
            text = item.get("TEXT", "")
            
            if title and text and len(text) >= 100:
                data.append({
                    "index": i,
                    "gutenberg_id": gutenberg_id,
                    "title": title,
                    "author": author,
                    "text": text,
                    "text_length": len(text)
                })
        except Exception as e:
            continue
    
    df = pd.DataFrame(data)
    print(f"[완료] DataFrame 생성 완료: {len(df):,}개 책")
    return df


def search_books(df: pd.DataFrame, search_terms: List[str], dataset_path: str = None) -> pd.DataFrame:
    """
    책 제목으로 검색 (각 검색어당 품질이 가장 좋은 버전 선택)
    
    Args:
        df: 책 데이터 DataFrame
        search_terms: 검색어 리스트
        dataset_path: 데이터셋 경로 (품질 분석용)
    
    Returns:
        검색 결과 DataFrame
    """
    print(f"\n[검색] 검색어: {search_terms}")
    
    results = []
    
    for term in search_terms:
        # 대소문자 구분 없이 검색
        mask = df['title'].str.contains(term, case=False, na=False)
        matched = df[mask]
        
        if len(matched) > 0:
            print(f"  '{term}': {len(matched)}개 발견")
            
            if len(matched) == 1:
                # 하나만 있으면 바로 선택
                best_match = matched
                print(f"    - [{best_match.iloc[0]['gutenberg_id']}] {best_match.iloc[0]['title']} by {best_match.iloc[0]['author']} ({best_match.iloc[0]['text_length']:,}자)")
            else:
                # 여러 개면 품질 분석
                print(f"    [분석] 여러 버전 발견, 품질 분석 중...")
                
                # 품질 점수 계산 (데이터셋 로드 필요)
                if dataset_path:
                    try:
                        ds = load_local_dataset(dataset_path)
                        
                        quality_scores = []
                        for _, row in matched.iterrows():
                            book_index = int(row['index'])
                            text = ds[book_index]['TEXT']
                            score, details = calculate_text_quality_score(
                                text, 
                                row['text_length'], 
                                row['gutenberg_id']
                            )
                            quality_scores.append({
                                'index': row['index'],
                                'gutenberg_id': row['gutenberg_id'],
                                'score': score,
                                'details': details
                            })
                        
                        # 점수 순으로 정렬
                        quality_scores.sort(key=lambda x: x['score'], reverse=True)
                        
                        # 최고 점수 선택
                        best_id = quality_scores[0]['gutenberg_id']
                        best_match = matched[matched['gutenberg_id'] == best_id]
                        
                        # 결과 출력
                        print(f"    [품질 분석 결과]")
                        for qs in quality_scores[:3]:  # 상위 3개만 표시
                            row = matched[matched['gutenberg_id'] == qs['gutenberg_id']].iloc[0]
                            marker = "★ 선택" if qs['gutenberg_id'] == best_id else "  "
                            print(f"      {marker} ID {qs['gutenberg_id']:>6} | 점수: {qs['score']:.1f} | "
                                  f"길이: {qs['details']['length']:.1f} | ID: {qs['details']['id']:.1f} | "
                                  f"구조: {qs['details']['structure']:.1f} | 품질: {qs['details']['quality']:.1f}")
                        
                    except Exception as e:
                        # 품질 분석 실패시 길이로 폴백
                        print(f"    [경고] 품질 분석 실패, 텍스트 길이로 선택: {e}")
                        matched_sorted = matched.sort_values('text_length', ascending=False)
                        best_match = matched_sorted.iloc[0:1]
                else:
                    # dataset_path 없으면 길이로만 판단
                    matched_sorted = matched.sort_values('text_length', ascending=False)
                    best_match = matched_sorted.iloc[0:1]
                    print(f"    - [{best_match.iloc[0]['gutenberg_id']}] {best_match.iloc[0]['title']} (텍스트 길이 기준)")
            
            results.append(best_match)
        else:
            print(f"  '{term}': 검색 결과 없음")
    
    if results:
        result_df = pd.concat(results, ignore_index=True)
        # 중복 제거 (혹시 모를 중복)
        result_df = result_df.drop_duplicates(subset=['gutenberg_id'])
        print(f"\n[결과] 총 {len(result_df)}개 책 선택됨")
        return result_df
    else:
        print("[결과] 검색 결과 없음")
        return pd.DataFrame()


def save_books_to_txt(df: pd.DataFrame, output_dir: str, dataset_path: str) -> List[Dict]:
    """
    책을 개별 txt 파일로 저장 (원본 데이터셋에서 텍스트 추출)
    
    Args:
        df: 저장할 책 메타데이터 DataFrame
        output_dir: 출력 디렉토리
        dataset_path: 원본 데이터셋 경로
    
    Returns:
        저장된 책 정보 리스트
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved_books = []
    
    print(f"\n[저장] {len(df)}개 책을 {output_dir}에 저장 중...")
    print("[로딩] 원본 데이터셋에서 텍스트 추출 중...")
    
    # 원본 데이터셋 로드 (필요한 책만)
    ds = load_local_dataset(dataset_path)
    
    for idx, row in df.iterrows():
        try:
            # 원본 데이터셋에서 텍스트 가져오기
            book_index = int(row['index'])
            text = ds[book_index]['TEXT']
            
            # 파일명 생성 (안전하게)
            safe_title = "".join(
                c if c.isalnum() or c in (' ', '_', '-') else '_' 
                for c in row['title']
            )
            safe_title = safe_title[:100]  # 파일명 길이 제한
            filename = f"{row['gutenberg_id']}_{safe_title}.txt"
            
            # 텍스트 파일 저장
            filepath = output_path / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            
            # 메타데이터 저장
            metadata_path = output_path / f"{filename}.metadata.json"
            book_metadata = {
                "index": book_index,
                "title": row['title'],
                "author": row['author'],
                "gutenberg_id": row['gutenberg_id'],
                "filepath": str(filepath),
                "text_length": len(text),
            }
            
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(book_metadata, f, indent=2, ensure_ascii=False)
            
            saved_books.append(book_metadata)
            print(f"  [{idx+1}/{len(df)}] {row['title']} - 저장 완료")
            
        except Exception as e:
            print(f"  [오류] {row['title']} 저장 실패: {e}")
            continue
    
    # 전체 정보 저장 (기존 데이터에 추가)
    info_path = output_path / "saved_books_info.json"
    
    # 기존 데이터 로드
    existing_books = []
    if info_path.exists():
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_books = existing_data.get("books", [])
        except:
            pass
    
    # 중복 제거 (gutenberg_id 기준)
    existing_ids = {book["gutenberg_id"] for book in existing_books}
    new_books = [book for book in saved_books if book["gutenberg_id"] not in existing_ids]
    
    # 병합
    all_books = existing_books + new_books
    
    # 저장
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_saved": len(all_books),
            "books": all_books
        }, f, indent=2, ensure_ascii=False)
    
    if new_books:
        print(f"[추가] {len(new_books)}개 새 책 추가됨 (기존: {len(existing_books)}개, 총: {len(all_books)}개)")
    
    print(f"\n[완료] {len(saved_books)}개 책 저장 완료")
    print(f"[정보] 저장 위치: {output_dir}")
    print(f"[정보] 메타데이터: {info_path}")
    
    return saved_books


def main():
    parser = argparse.ArgumentParser(
        description="로컬 Gutenberg 데이터셋에서 책 검색 및 저장"
    )
    parser.add_argument(
        "--dataset-path",
        default="data/origin_dataset/sedthh___gutenberg_english",
        help="로컬 데이터셋 경로 (기본: data/origin_dataset/sedthh___gutenberg_english)"
    )
    parser.add_argument(
        "--search",
        nargs="+",
        required=True,
        help="검색할 책 제목 (예: 'Pride and Prejudice' 'Alice' 'Wizard of Oz')"
    )
    parser.add_argument(
        "--output",
        default="data/origin_txt",
        help="출력 디렉토리 (기본: data/origin_txt)"
    )
    parser.add_argument(
        "--csv-path",
        default="data/cache/books_metadata.csv",
        help="CSV 메타데이터 파일 경로 (기본: data/cache/books_metadata.csv)"
    )
    parser.add_argument(
        "--force-reload",
        action="store_true",
        help="CSV 무시하고 데이터셋에서 다시 로드"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="확인 메시지 없이 자동 실행"
    )
    
    args = parser.parse_args()
    
    # CSV 파일 경로
    csv_path = Path(args.csv_path)
    
    # DataFrame 로드 (CSV 우선)
    if csv_path.exists() and not args.force_reload:
        print(f"[CSV] 메타데이터 로드 중: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"[완료] {len(df):,}개 책 로드 완료 (CSV 사용)")
    else:
        print("[경고] CSV 파일이 없습니다. 먼저 convert_to_csv.py를 실행하세요.")
        print("명령어: py convert_to_csv.py")
        print("\n또는 데이터셋에서 직접 로드하시겠습니까? (시간 소요)")
        
        if not args.yes:
            response = input("계속하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("[취소] 취소되었습니다.")
            return
        
        # 데이터셋 로드
        ds = load_local_dataset(args.dataset_path)
        
        # DataFrame 변환
        df = dataset_to_dataframe(ds)
        
        # CSV 저장
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"[저장] CSV 저장 완료: {csv_path}")
    
    # 책 검색 (품질 분석 포함)
    result_df = search_books(df, args.search, args.dataset_path)
    
    if len(result_df) == 0:
        print("\n[종료] 검색 결과가 없습니다.")
        return
    
    # 저장 여부 확인
    if not args.yes:
        print(f"\n{len(result_df)}개 책을 저장하시겠습니까?")
        response = input("계속하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("[취소] 취소되었습니다.")
            return
        
    # txt 파일로 저장 (원본 데이터셋에서 텍스트 추출)
    saved_books = save_books_to_txt(result_df, args.output, args.dataset_path)
    
    print(f"\n{'='*60}")
    print(f"작업 완료!")
    print(f"  - 검색된 책: {len(result_df)}개")
    print(f"  - 저장된 책: {len(saved_books)}개")
    print(f"  - 저장 위치: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
