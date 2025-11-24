"""
Gutenberg 데이터셋 다운로드 및 저장 스크립트

Hugging Face에서 Gutenberg 영어 데이터셋을 다운로드하여 로컬에 저장합니다.
"""

import argparse
import os
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm


def download_gutenberg_dataset(
    dataset_name: str = "sedthh/gutenberg_english",
    save_path: str = "data/origin_dataset/sedthh___gutenberg_english",
    split: str = "train"
):
    """
    Gutenberg 데이터셋 다운로드 및 로컬 저장
    
    Args:
        dataset_name: Hugging Face 데이터셋 이름
        save_path: 로컬 저장 경로
        split: 데이터셋 split (기본: "train")
    """
    print(f"[다운로드] 데이터셋: {dataset_name}")
    print(f"[저장 경로] {save_path}")
    print(f"[Split] {split}")
    print("\n" + "="*60)
    print("⚠️  주의: 데이터셋 크기가 매우 큽니다 (수 GB)")
    print("   다운로드에는 시간이 오래 걸릴 수 있습니다.")
    print("="*60 + "\n")
    
    # 저장 경로 생성
    save_path_obj = Path(save_path)
    save_path_obj.mkdir(parents=True, exist_ok=True)
    
    try:
        print("[1단계] 데이터셋 다운로드 중...")
        print("   (처음 실행 시 시간이 오래 걸릴 수 있습니다)")
        
        # 데이터셋 다운로드
        # streaming=False로 전체 데이터셋 다운로드
        dataset = load_dataset(
            dataset_name,
            split=split,
            trust_remote_code=True
        )
        
        print(f"[완료] 데이터셋 다운로드 완료: {len(dataset):,}개 책")
        
        print("\n[2단계] 로컬에 저장 중...")
        print("   (이 작업도 시간이 걸릴 수 있습니다)")
        
        # 로컬에 저장 (disk 형식으로 저장)
        dataset.save_to_disk(str(save_path_obj))
        
        print(f"\n[완료] 데이터셋 저장 완료!")
        print(f"   저장 위치: {save_path}")
        print(f"   총 책 개수: {len(dataset):,}개")
        print(f"\n이제 collect_data.py를 사용하여 책을 검색할 수 있습니다.")
        print(f"예시: python scripts/collect_data.py --search 'Frankenstein' --yes")
        
    except Exception as e:
        print(f"\n[오류] 데이터셋 다운로드 실패: {e}")
        print("\n문제 해결 방법:")
        print("1. 인터넷 연결을 확인하세요")
        print("2. Hugging Face 계정이 필요할 수 있습니다 (로그인)")
        print("3. 디스크 공간이 충분한지 확인하세요 (최소 10GB 이상 권장)")
        print("4. 데이터셋 이름이 올바른지 확인하세요")
        raise


def check_dataset_exists(dataset_path: str) -> bool:
    """데이터셋이 이미 존재하는지 확인"""
    path = Path(dataset_path)
    if path.exists():
        # Arrow 파일이 있는지 확인
        arrow_files = list(path.rglob("*.arrow"))
        if arrow_files:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Gutenberg 데이터셋 다운로드 및 저장"
    )
    parser.add_argument(
        "--dataset-name",
        default="sedthh/gutenberg_english",
        help="Hugging Face 데이터셋 이름 (기본: sedthh/gutenberg_english)"
    )
    parser.add_argument(
        "--save-path",
        default="data/origin_dataset/sedthh___gutenberg_english",
        help="로컬 저장 경로 (기본: data/origin_dataset/sedthh___gutenberg_english)"
    )
    parser.add_argument(
        "--split",
        default="train",
        help="데이터셋 split (기본: train)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 데이터셋이 있어도 다시 다운로드"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="확인 메시지 없이 자동 실행"
    )
    
    args = parser.parse_args()
    
    # 기존 데이터셋 확인
    if check_dataset_exists(args.save_path) and not args.force:
        print(f"[확인] 데이터셋이 이미 존재합니다: {args.save_path}")
        print("   기존 데이터셋을 사용하려면 이 스크립트를 실행하지 않아도 됩니다.")
        
        if not args.yes:
            response = input("\n다시 다운로드하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("[취소] 취소되었습니다. 기존 데이터셋을 사용합니다.")
                return
    
    # 확인 메시지
    if not args.yes:
        print("\n" + "="*60)
        print("⚠️  경고: 이 작업은 시간이 오래 걸릴 수 있습니다.")
        print("   데이터셋 크기: 수 GB")
        print("   예상 시간: 네트워크 속도에 따라 다름 (수십 분 ~ 수 시간)")
        print("="*60)
        response = input("\n계속하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("[취소] 취소되었습니다.")
            return
    
    # 다운로드 실행
    try:
        download_gutenberg_dataset(
            dataset_name=args.dataset_name,
            save_path=args.save_path,
            split=args.split
        )
    except KeyboardInterrupt:
        print("\n\n[중단] 사용자에 의해 중단되었습니다.")
        print("   부분적으로 다운로드된 파일은 다음 실행 시 재개될 수 있습니다.")
    except Exception as e:
        print(f"\n[오류] 다운로드 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()


