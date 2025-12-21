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
    """모든 API 키 가져오기 (최대 10개)"""
    keys = []
    
    # 방법 1: GEMINI_API_KEYS (쉼표로 구분) - 우선순위 1
    keys_str = os.getenv("GEMINI_API_KEYS")
    if keys_str:
        keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        print(f"[API 키] GEMINI_API_KEYS에서 {len(keys)}개 키 발견")
    
    # 방법 2: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ... (최대 10개까지)
    if not keys:
        for i in range(1, 11):  # 1부터 10까지
            key = os.getenv(f"GEMINI_API_KEY_{i}")
            if key:
                keys.append(key)
        if keys:
            print(f"[API 키] GEMINI_API_KEY_1~10에서 {len(keys)}개 키 발견")
    
    # 방법 3: 레거시 단일 키 (GEMINI_API_KEY)
    if not keys:
        legacy_key = os.getenv("GEMINI_API_KEY")
        if legacy_key:
            keys.append(legacy_key)
            print(f"[API 키] GEMINI_API_KEY에서 1개 키 발견")
    
    # 중복 제거
    keys = list(dict.fromkeys(keys))  # 순서 유지하면서 중복 제거
    
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
    """책을 File Search Store에 업로드 (에러 발생 시 즉시 실패, 다음 키로 전환)"""
    print(f"\n[업로드] {book_info['title']} (ID: {book_info['gutenberg_id']})")
    
    try:
        # 파일 업로드 및 임포트
        print(f"  [업로드] 업로드 시작...")
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
        wait_count = 0
        max_wait_retries = 180  # 최대 15분 대기 (5초 * 180)
        
        while not operation.done and wait_count < max_wait_retries:
            time.sleep(5)
            operation = client.operations.get(operation)
            wait_count += 1
            if wait_count % 12 == 0:  # 1분마다 진행상황 출력
                print(f"  [진행] {wait_count * 5}초 경과...")
        
        if operation.done:
            print(f"  [완료] 업로드 완료!")
            return True
        else:
            print(f"  [경고] 타임아웃 (15분 초과)")
            return False
            
    except Exception as e:
        error_str = str(e)
        print(f"  [오류] 업로드 실패: {error_str[:100]}")
        # 에러 발생 시 즉시 실패하고 다음 키로 전환
        print(f"  [건너뛰기] 다음 키로 전환합니다.")
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
    
    # 모든 API 키 사용 (각 키마다 모든 책 업로드)
    print(f"\n[정보] 총 {len(api_keys)}개 API 키를 모두 사용합니다.")
    print(f"       각 API 키마다 {len(selected_books)}개 책을 모두 업로드합니다.")
    print(f"       Rate Limit 발생 시 다음 키로 전환합니다.")
    
    if len(api_keys) < 10:
        print(f"\n[경고] API 키가 {len(api_keys)}개만 발견되었습니다.")
        print(f"       10개 키를 모두 사용하려면 .env 파일에 GEMINI_API_KEYS를 설정하세요.")
        print(f"       형식: GEMINI_API_KEYS=key1,key2,key3,...,key10")
    
    # 각 API 키에 대해 Store 생성 및 업로드
    total_success = 0
    total_failed = 0
    
    # 모든 키 사용
    api_keys_to_use = [(i, api_keys[i]) for i in range(len(api_keys))]
    
    for key_index, api_key in api_keys_to_use:
        print("\n" + "="*70)
        print(f"API 키 #{key_index + 1} 처리 중...")
        print("="*70)
        
        try:
            # API 클라이언트 초기화
            # 문서에 따르면: client = genai.Client() (환경변수에서 API 키 가져옴)
            # 하지만 여러 키를 사용하므로 명시적으로 전달
            # google-genai 1.0.0에서는 api_key 파라미터를 지원해야 함
            client = genai.Client(api_key=api_key)
            
            # 디버그: 클라이언트 속성 확인 (문제 진단용)
            if not hasattr(client, 'file_search_stores'):
                print(f"[오류] Client 객체에 file_search_stores 속성이 없습니다.")
                print(f"[디버그] Client 객체 속성: {[attr for attr in dir(client) if not attr.startswith('_')]}")
                try:
                    import google.genai
                    print(f"[디버그] google-genai 버전: {google.genai.__version__ if hasattr(google.genai, '__version__') else '알 수 없음'}")
                except:
                    pass
                print(f"[해결 방법]")
                print(f"  1. pip install --upgrade google-genai")
                print(f"  2. 또는 pip install google-genai==1.0.0")
                raise AttributeError("file_search_stores 속성을 찾을 수 없습니다. google-genai 라이브러리 버전을 확인하세요.")
            
            # File Search Store 생성 (키별로 별도 Store)
            store_name = f"novel-characters-store-key{key_index + 1}"
            
            # Store 생성 시 503 에러 재시도
            max_store_retries = 3
            store = None
            for store_attempt in range(1, max_store_retries + 1):
                try:
                    store = create_file_search_store(client, store_name=store_name, reset=args.reset)
                    break
                except Exception as store_error:
                    error_str = str(store_error)
                    if "503" in error_str or "unavailable" in error_str.lower():
                        if store_attempt < max_store_retries:
                            wait_seconds = 60 * store_attempt
                            print(f"[대기] Store 생성 실패 (503). {wait_seconds}초 후 재시도... ({store_attempt}/{max_store_retries})")
                            time.sleep(wait_seconds)
                            continue
                        else:
                            raise
                    else:
                        raise
            
            if store is None:
                raise Exception("Store 생성 실패")
            
            # 이미 업로드된 책 확인 (reset이 아닐 때만)
            already_uploaded = set()
            if not args.reset:
                store_info = load_store_info(key_index)
                if store_info:
                    already_uploaded = {book['gutenberg_id'] for book in store_info.get('uploaded_books', [])}
                    print(f"[확인] 이미 업로드된 책: {len(already_uploaded)}개")
            
            # 각 키마다 모든 책 업로드 (분산하지 않음)
            # 업로드할 책 필터링 (이미 업로드된 것 제외)
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
            
            for book_idx, book in enumerate(books_to_upload, 1):
                print(f"\n{'='*70}")
                print(f"[{book_idx}/{len(books_to_upload)}] {book['title']} 처리 중...")
                print(f"{'='*70}")
                
                # 파일 경로 처리 (프로젝트 루트 기준)
                # Windows 경로 처리: 백슬래시를 슬래시로 변환
                filepath = book['filepath'].replace('\\', '/')
                book_path = Path(filepath)
                
                # 상대 경로면 프로젝트 루트 기준으로 변환
                if not book_path.is_absolute():
                    book_path = project_root / book_path
                
                # 파일이 없으면 origin_txt에서 찾기
                if not book_path.exists():
                    # 파일명만 추출하여 origin_txt에서 찾기
                    filename = book_path.name
                    book_path = project_root / 'data' / 'origin_txt' / filename
                
                if not book_path.exists():
                    print(f"[건너뛰기] 파일 없음: {book['filepath']}")
                    print(f"  시도한 경로 1: {project_root / filepath}")
                    print(f"  시도한 경로 2: {book_path}")
                    continue
                
                # 파일 크기 확인
                file_size_mb = book_path.stat().st_size / (1024 * 1024)
                print(f"[파일] 크기: {file_size_mb:.2f} MB")
                
                # 업로드 시도 (에러 발생 시 다음 키로 전환)
                success = upload_book_to_store(
                    client, 
                    store.name, 
                    str(book_path), 
                    book
                )
                
                if success:
                    uploaded_books.append({
                        'gutenberg_id': book['gutenberg_id'],
                        'title': book['title'],
                        'author': book['author'],
                        'filepath': book['filepath']
                    })
                    success_count += 1
                    print(f"[성공] {book['title']} 업로드 완료!")
                else:
                    print(f"[실패] {book['title']} 업로드 실패. 다음 파일로 진행...")
                
                # API 제한 고려 (각 파일 업로드 사이에 대기 시간)
                if book_idx < len(books_to_upload):
                    wait_seconds = 60  # 1분 대기
                    print(f"\n[대기] 다음 파일 업로드 전 {wait_seconds}초({wait_seconds//60}분) 대기...")
                    time.sleep(wait_seconds)
            
            # 결과 저장
            save_store_info(store, uploaded_books, api_key_index=key_index, reset=args.reset)
            
            print(f"\n[완료] API 키 #{key_index + 1} 업로드 완료!")
            print(f"  - 전체 책: {len(selected_books)}개")
            print(f"  - 성공: {success_count}/{len(books_to_upload)}개")
            print(f"  - 스토어: {store.name}")
            
            total_success += success_count
            
            # 키 간 전환 시 대기 시간 (Rate Limit 방지)
            if key_index < len(api_keys) - 1:
                wait_seconds = 120  # 2분 대기
                print(f"\n[대기] 다음 키로 전환 전 {wait_seconds}초({wait_seconds//60}분) 대기...")
                time.sleep(wait_seconds)
            
        except Exception as e:
            print(f"\n[오류] API 키 #{key_index + 1} 처리 실패: {e}")
            total_failed += len(selected_books)
            # 오류 발생 시에도 다음 키로 전환 전 대기
            if key_index < len(api_keys) - 1:
                wait_seconds = 120
                print(f"[대기] 다음 키로 전환 전 {wait_seconds}초 대기...")
                time.sleep(wait_seconds)
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

