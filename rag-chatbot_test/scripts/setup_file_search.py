"""
Gemini File Search Store 설정 스크립트

origin_txt의 책들을 Gemini File Search Store에 업로드합니다.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 환경 변수 로드
load_dotenv()

def get_all_api_keys():
    """모든 API 키 가져오기"""
    keys = []
    
    # 방법 1: GEMINI_API_KEYS (쉼표로 구분)
    keys_str = os.getenv("GEMINI_API_KEYS")
    if keys_str:
        keys = [k.strip() for k in keys_str.split(',') if k.strip()]
    
    # 방법 2: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
    if not keys:
        i = 1
        while True:
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if not key:
                break
            keys.append(key)
            i += 1
    
    # 방법 3: 레거시 단일 키 (GEMINI_API_KEY)
    if not keys:
        legacy_key = os.getenv("GEMINI_API_KEY")
        if legacy_key:
            keys.append(legacy_key)
    
    return keys

def load_books_info(info_path: str = None):
    """저장된 책 정보 로드"""
    if info_path is None:
        # 프로젝트 루트 기준으로 경로 설정
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        info_path = project_root / "data" / "origin_txt" / "saved_books_info.json"
        # 대체 경로 시도
        if not info_path.exists():
            info_path = project_root / "data" / "saved_books_info.json"
    
    with open(info_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('books', [])

def delete_file_search_store(client: genai.Client, store_name: str):
    """File Search Store 삭제"""
    try:
        stores = list(client.file_search_stores.list())
        for store in stores:
            if store.display_name == store_name:
                print(f"[삭제] 기존 스토어 삭제 중: {store.name}")
                client.file_search_stores.delete(name=store.name, config={'force': True})
                print(f"[완료] 스토어 삭제 완료")
                return True
        return False
    except Exception as e:
        print(f"[오류] 스토어 삭제 실패: {e}")
        return False

def create_file_search_store(client: genai.Client, store_name: str = "novel-characters-store", reset: bool = False):
    """File Search Store 생성"""
    print(f"\n[생성] File Search Store 생성 중: {store_name}")
    
    try:
        # Reset 옵션이 있으면 기존 스토어 삭제
        if reset:
            delete_file_search_store(client, store_name)
        
        # 기존 스토어 확인
        stores = list(client.file_search_stores.list())
        for store in stores:
            if store.display_name == store_name:
                if reset:
                    # Reset 후 새로 생성
                    store = client.file_search_stores.create(
                        config={'display_name': store_name}
                    )
                    print(f"[완료] 새 스토어 생성 완료: {store.name}")
                else:
                    print(f"[발견] 기존 스토어 사용: {store.name}")
                return store
        
        # 새 스토어 생성
        store = client.file_search_stores.create(
            config={'display_name': store_name}
        )
        print(f"[완료] 스토어 생성 완료: {store.name}")
        return store
        
    except Exception as e:
        print(f"[오류] 스토어 생성 실패: {e}")
        raise

def upload_book_to_store(
    client: genai.Client,
    store_name: str,
    book_path: str,
    book_info: dict
):
    """책을 File Search Store에 업로드"""
    print(f"\n[업로드] {book_info['title']} (ID: {book_info['gutenberg_id']})")
    
    try:
        # 파일 업로드 및 임포트
        operation = client.file_search_stores.upload_to_file_search_store(
            file=book_path,
            file_search_store_name=store_name,
            config={
                'display_name': f"{book_info['gutenberg_id']}_{book_info['title'][:50]}",
                'chunking_config': {
                    'white_space_config': {
                        'max_tokens_per_chunk': 500,  # 책 내용이므로 큰 청크
                        'max_overlap_tokens': 100
                    }
                }
            }
        )
        
        # 업로드 완료 대기
        print(f"  [대기] 임포트 처리 중...")
        retry_count = 0
        max_retries = 60  # 최대 5분 대기
        
        while not operation.done and retry_count < max_retries:
            time.sleep(5)
            operation = client.operations.get(operation)
            retry_count += 1
            if retry_count % 6 == 0:  # 30초마다 진행상황 출력
                print(f"  [진행] {retry_count * 5}초 경과...")
        
        if operation.done:
            print(f"  [완료] 업로드 완료!")
            return True
        else:
            print(f"  [경고] 타임아웃 (5분 초과)")
            return False
            
    except Exception as e:
        print(f"  [오류] 업로드 실패: {e}")
        return False

def load_store_info(api_key_index: int = None):
    """저장된 Store 정보 로드"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    if api_key_index is not None:
        info_path = project_root / "data" / f"file_search_store_info_key{api_key_index + 1}.json"
    else:
        info_path = project_root / "data" / "file_search_store_info.json"
    
    if info_path.exists():
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_store_info(store, uploaded_books: list, api_key_index: int = None, output_path: str = None, reset: bool = False):
    """스토어 정보 저장"""
    if output_path is None:
        # 프로젝트 루트 기준으로 경로 설정
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        if api_key_index is not None:
            # API 키별로 별도 파일 저장
            output_path = project_root / "data" / f"file_search_store_info_key{api_key_index + 1}.json"
        else:
            output_path = project_root / "data" / "file_search_store_info.json"
    else:
        # 상대 경로면 프로젝트 루트 기준으로 변환
        output_path = Path(output_path)
        if not output_path.is_absolute():
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            output_path = project_root / output_path
    
    # 기존 정보가 있으면 업로드된 책 목록 병합 (reset이 아닐 때만)
    if not reset:
        existing_info = load_store_info(api_key_index)
        if existing_info:
            existing_uploaded = {book['gutenberg_id']: book for book in existing_info.get('uploaded_books', [])}
            new_uploaded = {book['gutenberg_id']: book for book in uploaded_books}
            # 기존 + 새로운 책 병합
            merged_uploaded = list({**existing_uploaded, **new_uploaded}.values())
            uploaded_books = merged_uploaded
    
    info = {
        "api_key_index": api_key_index + 1 if api_key_index is not None else None,
        "store_name": store.name,
        "display_name": store.display_name,
        "uploaded_books": uploaded_books,
        "total_books": len(uploaded_books),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    print(f"\n[저장] 스토어 정보 저장: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini File Search Store 설정")
    parser.add_argument(
        "--mode",
        choices=["all", "main", "count"],
        default="main",
        help="업로드 모드: all(모든 책), main(주요 책), count(개수 지정)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="업로드할 책 개수 (mode=count일 때)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="기존 Store를 삭제하고 새로 생성 (중복 업로드 방지)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("Gemini File Search Store 설정")
    print("="*70)
    
    # 모든 API 키 가져오기
    api_keys = get_all_api_keys()
    if not api_keys:
        print("[오류] GEMINI_API_KEY를 찾을 수 없습니다.")
        return
    
    print(f"\n[발견] 총 {len(api_keys)}개의 API 키 발견")
    
    # 책 정보 로드
    books = load_books_info()
    print(f"[로드] 총 {len(books)}개 책 발견")
    
    # 업로드할 책 선택
    if args.mode == "main":
        # 주요 책만 선택 (정수와 문자열 모두 지원)
        main_book_ids = [84, 1342, 64317, 1513, 74, 1661]
        main_book_ids_str = [str(id) for id in main_book_ids]
        selected_books = [b for b in books if b['gutenberg_id'] in main_book_ids or str(b['gutenberg_id']) in main_book_ids_str]
        print(f"[선택] 주요 책 {len(selected_books)}개 업로드")
    elif args.mode == "count":
        selected_books = books[:args.count]
        print(f"[선택] 처음 {args.count}개 책 업로드")
    else:  # all
        selected_books = books
        print(f"[선택] 모든 책 {len(books)}개 업로드")
    
    # 프로젝트 루트 기준으로 경로 설정
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 각 API 키에 대해 Store 생성 및 업로드
    total_success = 0
    total_failed = 0
    
    for key_index, api_key in enumerate(api_keys):
        print("\n" + "="*70)
        print(f"API 키 #{key_index + 1} 처리 중...")
        print("="*70)
        
        try:
            # API 클라이언트 초기화
            client = genai.Client(api_key=api_key)
            
            # File Search Store 생성
            store = create_file_search_store(client, reset=args.reset)
            
            # 이미 업로드된 책 확인 (reset이 아닐 때만)
            already_uploaded = set()
            if not args.reset:
                store_info = load_store_info(key_index)
                if store_info:
                    already_uploaded = {book['gutenberg_id'] for book in store_info.get('uploaded_books', [])}
                    print(f"[확인] 이미 업로드된 책: {len(already_uploaded)}개")
            
            # 업로드할 책 필터링
            books_to_upload = [b for b in selected_books if b['gutenberg_id'] not in already_uploaded]
            
            if not books_to_upload:
                print(f"\n[건너뛰기] 모든 책이 이미 업로드되어 있습니다.")
                # 기존 Store 정보 로드
                store_info = load_store_info(key_index)
                if store_info:
                    uploaded_books = store_info.get('uploaded_books', [])
                    save_store_info(store, uploaded_books, api_key_index=key_index, reset=args.reset)
                continue
            
            print(f"\n[업로드] {len(books_to_upload)}개 책을 업로드합니다... (이미 업로드된 {len(already_uploaded)}개 제외)")
            
            # 책 업로드
            uploaded_books = []
            success_count = 0
            
            # 기존 업로드된 책 목록 로드
            if not args.reset:
                store_info = load_store_info(key_index)
                if store_info:
                    uploaded_books = store_info.get('uploaded_books', [])
            
            for book in books_to_upload:
                # 파일 경로 처리 (프로젝트 루트 기준)
                book_path = Path(book['filepath'])
                
                # 상대 경로면 프로젝트 루트 기준으로 변환
                if not book_path.is_absolute():
                    book_path = project_root / book_path
                
                # 파일이 없으면 origin_txt에서 찾기
                if not book_path.exists():
                    # data\XXX.txt -> data\origin_txt\XXX.txt
                    if len(book_path.parts) >= 2 and book_path.parts[-2] == 'data':
                        book_path = project_root / 'data' / 'origin_txt' / book_path.parts[-1]
                
                if not book_path.exists():
                    print(f"\n[건너뛰기] 파일 없음: {book['filepath']}")
                    print(f"  시도한 경로: {book_path}")
                    continue
                
                success = upload_book_to_store(client, store.name, str(book_path), book)
                
                if success:
                    uploaded_books.append({
                        'gutenberg_id': book['gutenberg_id'],
                        'title': book['title'],
                        'author': book['author'],
                        'filepath': book['filepath']
                    })
                    success_count += 1
                
                # API 제한 고려 (너무 빠르게 요청하지 않기)
                time.sleep(2)
            
            # 결과 저장
            save_store_info(store, uploaded_books, api_key_index=key_index, reset=args.reset)
            
            print(f"\n[완료] API 키 #{key_index + 1} 업로드 완료!")
            print(f"  - 성공: {success_count}/{len(selected_books)}개")
            print(f"  - 스토어: {store.name}")
            
            total_success += success_count
            
        except Exception as e:
            print(f"\n[오류] API 키 #{key_index + 1} 처리 실패: {e}")
            total_failed += len(selected_books)
            continue
    
    # 전체 결과 출력
    print("\n" + "="*70)
    print("전체 업로드 완료!")
    print(f"  - 총 API 키: {len(api_keys)}개")
    print(f"  - 총 성공: {total_success}개")
    if total_failed > 0:
        print(f"  - 총 실패: {total_failed}개")
    print("="*70)

if __name__ == "__main__":
    main()

