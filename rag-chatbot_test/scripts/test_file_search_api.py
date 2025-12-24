"""
Gemini File Search API 테스트 스크립트

client.file_search API를 사용하여 스토어 및 파일 목록 조회
"""

import os
from dotenv import load_dotenv

load_dotenv()


def main():
    print("="*70)
    print("Gemini File Search API 테스트")
    print("="*70)
    
    try:
        from google import genai
    except ImportError:
        print("[오류] google-genai 라이브러리가 설치되지 않았습니다.")
        return
    
    # 첫 번째 API 키 사용
    keys_str = os.getenv("GEMINI_API_KEYS")
    if keys_str:
        api_key = keys_str.split(',')[0].strip()
    else:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[오류] API 키를 찾을 수 없습니다.")
        return
    
    client = genai.Client(api_key=api_key)
    
    # Client 객체의 모든 속성 확인
    print("\n[1] Client 객체 속성 확인")
    print("-"*50)
    attrs = [a for a in dir(client) if not a.startswith('_')]
    print(f"사용 가능한 속성: {attrs}")
    
    # file_search 속성 확인
    print("\n[2] file_search 속성 확인")
    print("-"*50)
    if hasattr(client, 'file_search'):
        fs = client.file_search
        fs_methods = [m for m in dir(fs) if not m.startswith('_')]
        print(f"file_search 메서드: {fs_methods}")
        
        # list_file_search_stores 시도
        print("\n[3] 스토어 목록 조회 (file_search.list_file_search_stores)")
        print("-"*50)
        try:
            stores = list(fs.list_file_search_stores())
            print(f"총 {len(stores)}개 스토어 발견")
            for store in stores[:5]:
                print(f"  - {getattr(store, 'name', 'unknown')}")
        except AttributeError as e:
            print(f"  메서드 없음: {e}")
        except Exception as e:
            print(f"  오류: {e}")
    else:
        print("file_search 속성이 없습니다.")
    
    # file_search_stores 속성 확인 (기존 방식)
    print("\n[4] file_search_stores 속성 확인 (기존 방식)")
    print("-"*50)
    if hasattr(client, 'file_search_stores'):
        fss = client.file_search_stores
        fss_methods = [m for m in dir(fss) if not m.startswith('_')]
        print(f"file_search_stores 메서드: {fss_methods}")
        
        # 스토어 목록 조회
        print("\n[5] 스토어 목록 조회 (file_search_stores.list)")
        print("-"*50)
        try:
            stores = list(fss.list())
            print(f"총 {len(stores)}개 스토어 발견")
            
            # 첫 번째 novel-characters-store 찾기
            target_store = None
            for store in stores:
                if 'novel-characters-store' in getattr(store, 'display_name', ''):
                    target_store = store
                    break
            
            if target_store:
                store_name = getattr(target_store, 'name', '')
                print(f"\n대상 스토어: {store_name}")
                
                # 스토어 내 파일 목록 조회 시도
                print("\n[6] 스토어 내 파일 목록 조회")
                print("-"*50)
                
                # 방법 1: documents.list
                print("\n방법 1: file_search_stores.documents.list()")
                try:
                    docs = list(fss.documents.list(parent=store_name))
                    print(f"  총 {len(docs)}개 문서 발견")
                    for doc in docs[:3]:
                        print(f"    - {getattr(doc, 'display_name', 'unknown')}")
                        print(f"      ID: {getattr(doc, 'name', 'unknown')}")
                except Exception as e:
                    print(f"  오류: {e}")
                
                # 방법 2: list_file_search_store_files (만약 존재한다면)
                print("\n방법 2: file_search.list_file_search_store_files()")
                if hasattr(client, 'file_search'):
                    try:
                        if hasattr(client.file_search, 'list_file_search_store_files'):
                            files = list(client.file_search.list_file_search_store_files(
                                file_search_store_name=store_name
                            ))
                            print(f"  총 {len(files)}개 파일 발견")
                            for f in files[:3]:
                                print(f"    - {getattr(f, 'name', 'unknown')}")
                        else:
                            print("  list_file_search_store_files 메서드가 없습니다.")
                    except Exception as e:
                        print(f"  오류: {e}")
                else:
                    print("  file_search 속성이 없습니다.")
                    
        except Exception as e:
            print(f"오류: {e}")
    else:
        print("file_search_stores 속성이 없습니다.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()

