"""
데이터셋을 CSV 메타데이터로 변환하는 스크립트

Gutenberg 데이터셋을 로드하여 책 메타데이터를 CSV 파일로 저장합니다.
이 CSV 파일은 collect_data.py에서 검색 속도를 향상시키기 위해 사용됩니다.
"""

import argparse
import json
import pandas as pd
from pathlib import Path
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
        dataset_path_obj = Path(dataset_path)
        
        # 방법 1: load_from_disk 사용 (권장 - save_to_disk로 저장된 경우)
        if (dataset_path_obj / "dataset_info.json").exists() or (dataset_path_obj / "state.json").exists():
            print("  [방법] load_from_disk 사용")
            ds = load_from_disk(str(dataset_path_obj))
            print(f"[완료] 총 {len(ds):,}개 책 로드 완료")
            return ds
        
        # 방법 2: Arrow 파일 직접 로드
        arrow_files = list(dataset_path_obj.glob("data-*.arrow"))
        if arrow_files:
            print(f"  [방법] Arrow 파일 직접 로드 ({len(arrow_files)}개 파일)")
            from datasets import load_dataset
            # 모든 Arrow 파일을 로드
            data_files = {
                "train": [str(f) for f in sorted(arrow_files)]
            }
            ds = load_dataset("arrow", data_files=data_files, split="train")
            print(f"[완료] 총 {len(ds):,}개 책 로드 완료")
            return ds
        
        raise FileNotFoundError(f"데이터셋을 찾을 수 없습니다: {dataset_path}")
        
    except Exception as e:
        print(f"[오류] 데이터셋 로드 실패: {e}")
        raise


def dataset_to_dataframe(ds: Dataset) -> pd.DataFrame:
    """
    Dataset을 DataFrame으로 변환
    
    Args:
        ds: Dataset 객체
    
    Returns:
        pandas DataFrame
    """
    print("[변환] Dataset을 DataFrame으로 변환 중...")
    print("   (이 작업은 시간이 걸릴 수 있습니다)")
    
    # 필요한 컬럼만 추출
    data = []
    total = len(ds)
    
    for i, item in enumerate(ds):
        if (i + 1) % 5000 == 0:
            print(f"  진행: {i+1:,}/{total:,} ({(i+1)/total*100:.1f}%)")
        
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
            
            # 최소 길이 필터링 (너무 짧은 텍스트 제외)
            if title and text and len(text) >= 100:
                # 메타데이터만 저장 (텍스트는 원본 데이터셋에서 가져옴)
                data.append({
                    "index": i,
                    "gutenberg_id": gutenberg_id,
                    "title": title,
                    "author": author,
                    "text_length": len(text)
                    # text 컬럼 제거: 원본 데이터셋에서 가져오므로 CSV에 저장하지 않음
                })
        except Exception as e:
            # 개별 항목 오류는 무시하고 계속 진행
            continue
    
    df = pd.DataFrame(data)
    print(f"[완료] DataFrame 생성 완료: {len(df):,}개 책")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Gutenberg 데이터셋을 CSV 메타데이터로 변환"
    )
    parser.add_argument(
        "--dataset-path",
        default="data/origin_dataset/sedthh___gutenberg_english",
        help="로컬 데이터셋 경로 (기본: data/origin_dataset/sedthh___gutenberg_english)"
    )
    parser.add_argument(
        "--csv-path",
        default="data/cache/books_metadata.csv",
        help="CSV 출력 경로 (기본: data/cache/books_metadata.csv)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 CSV 파일이 있어도 다시 생성"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="확인 메시지 없이 자동 실행"
    )
    
    args = parser.parse_args()
    
    # CSV 파일 경로
    csv_path = Path(args.csv_path)
    
    # 기존 CSV 확인
    if csv_path.exists() and not args.force:
        print(f"[확인] CSV 파일이 이미 존재합니다: {csv_path}")
        print("   기존 CSV를 사용하려면 이 스크립트를 실행하지 않아도 됩니다.")
        
        if not args.yes:
            response = input("\n다시 생성하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("[취소] 취소되었습니다. 기존 CSV를 사용합니다.")
                return
    
    # 확인 메시지
    if not args.yes:
        print("\n" + "="*60)
        print("⚠️  경고: 이 작업은 시간이 오래 걸릴 수 있습니다.")
        print("   데이터셋 크기에 따라 수십 분에서 수 시간이 걸릴 수 있습니다.")
        print("="*60)
        response = input("\n계속하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("[취소] 취소되었습니다.")
            return
    
    try:
        # 1. 데이터셋 로드
        print("\n[1단계] 데이터셋 로드 중...")
        ds = load_local_dataset(args.dataset_path)
        
        # 2. DataFrame 변환
        print("\n[2단계] DataFrame 변환 중...")
        df = dataset_to_dataframe(ds)
        
        # 3. CSV 저장
        print(f"\n[3단계] CSV 저장 중: {csv_path}")
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"\n{'='*60}")
        print(f"✅ 작업 완료!")
        print(f"   - 총 책 개수: {len(df):,}개")
        print(f"   - CSV 파일: {csv_path}")
        print(f"   - 파일 크기: {csv_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"\n이제 collect_data.py를 사용하여 책을 빠르게 검색할 수 있습니다.")
        print(f"예시: python scripts/collect_data.py --search 'Frankenstein' --yes")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\n[중단] 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n[오류] 변환 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()


