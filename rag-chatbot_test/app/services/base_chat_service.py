"""
기본 대화 서비스 (공통 로직)

API 호출, 재시도, 에러 처리 등 공통 기능을 제공합니다.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from google import genai
from google.genai.types import Tool, FileSearch
from app.services.api_key_manager import get_api_key_manager


class BaseChatService:
    """기본 대화 서비스 - 공통 API 호출 로직"""
    
    def __init__(self, api_key: Optional[str] = None, store_info_path: str = None):
        """
        Args:
            api_key: Gemini API 키 (선택, 없으면 API 키 매니저 사용)
            store_info_path: File Search Store 정보 파일 경로 (None이면 자동 설정)
        """
        # API 키 매니저 사용
        self.api_key_manager = get_api_key_manager()
        
        # API 키가 제공되면 사용, 아니면 매니저에서 가져오기
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self.api_key_manager.get_current_key()
        
        self.client = genai.Client(api_key=self.api_key)
        
        # Store 정보 파일 경로 설정 (프로젝트 루트 기준)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        
        if store_info_path is None:
            # 현재 API 키 인덱스 확인
            current_key_index = self.api_key_manager.current_key_index
            # API 키별 Store 정보 파일 경로 시도
            store_info_path = project_root / "data" / f"file_search_store_info_key{current_key_index + 1}.json"
            
            # 파일이 없으면 기본 파일 시도
            if not store_info_path.exists():
                store_info_path = project_root / "data" / "file_search_store_info.json"
        else:
            store_info_path = Path(store_info_path)
            if not store_info_path.is_absolute():
                store_info_path = project_root / store_info_path
        
        self.store_info_path = str(store_info_path)
        
        # Store 정보 로드 (파일만 읽기, API 호출 없음)
        self.store_info = self._load_store_info(self.store_info_path)
        if self.store_info and self.store_info.get('store_name'):
            self.store_name = self.store_info.get('store_name')
        else:
            self.store_name = None
    
    def _load_store_info(self, path: str) -> dict:
        """File Search Store 정보 로드"""
        try:
            path_obj = Path(path)
            if not path_obj.is_absolute():
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent
                path_obj = project_root / path_obj
            with open(path_obj, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def _ensure_store_loaded(self):
        """Store 정보가 로드되었는지 확인하고 필요시 다시 로드"""
        current_key = self.api_key_manager.get_current_key()
        
        # API 키가 변경되었으면 Store 정보 파일 다시 로드
        if current_key != self.api_key:
            self.api_key = current_key
            self.client = genai.Client(api_key=self.api_key)
            # 현재 API 키 인덱스에 맞는 Store 정보 파일 로드
            current_key_index = self.api_key_manager.current_key_index
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            store_info_path = project_root / "data" / f"file_search_store_info_key{current_key_index + 1}.json"
            if not store_info_path.exists():
                store_info_path = project_root / "data" / "file_search_store_info.json"
            self.store_info = self._load_store_info(str(store_info_path))
            if self.store_info and self.store_info.get('store_name'):
                self.store_name = self.store_info.get('store_name')
            else:
                self.store_name = None
    
    def _call_gemini_api(
        self,
        contents: List[Dict],
        system_instruction: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.8,
        top_p: float = 0.95,
        max_output_tokens: int = 4096,
        stream: bool = False
    ):
        """
        Gemini API 호출 (재시도 로직 포함)
        
        Args:
            contents: 대화 내용
            system_instruction: 시스템 지시사항
            model: 모델 이름
            temperature: 온도
            top_p: top_p
            max_output_tokens: 최대 출력 토큰
            stream: 스트리밍 여부
        
        Returns:
            API 응답 또는 스트림
        
        Raises:
            Exception: API 호출 실패 시
        """
        max_retries = len(self.api_key_manager.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Store 정보 확인 및 로드
                self._ensure_store_loaded()
                
                # Store가 없으면 에러
                if not self.store_name:
                    raise ValueError(
                        "File Search Store가 설정되지 않았습니다. "
                        "'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요."
                    )
                
                # API 호출
                config = {
                    "system_instruction": system_instruction,
                    "tools": [
                        Tool(
                            file_search=FileSearch(
                                file_search_store_names=[self.store_name]
                            )
                        )
                    ],
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_output_tokens": max_output_tokens
                }
                
                if stream:
                    response = self.client.models.generate_content_stream(
                        model=model,
                        contents=contents,
                        config=config
                    )
                else:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config
                    )
                
                return response
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Store 접근 권한 에러 감지
                if 'PERMISSION_DENIED' in error_str or 'file search store' in error_str.lower():
                    raise ValueError(
                        f"Store 접근 권한이 없습니다. "
                        f"'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요: {str(e)}"
                    )
                
                # 할당량 에러가 아니면 즉시 반환
                if not self.api_key_manager._is_quota_error(e):
                    raise
                
                # 마지막 시도면 에러 반환
                if attempt >= max_retries - 1:
                    raise ValueError(f"모든 API 키의 할당량이 초과되었습니다: {str(e)}")
                
                # 다음 키로 전환
                if not self.api_key_manager.switch_to_next_key():
                    raise ValueError(f"사용 가능한 API 키가 없습니다: {str(e)}")
                
                # 잠시 대기 후 재시도
                time.sleep(1)
        
        # 모든 재시도 실패
        raise ValueError(f"API 호출 실패: {str(last_error)}")
    
    def _extract_response(self, response) -> Dict:
        """
        API 응답에서 텍스트와 메타데이터 추출
        
        Args:
            response: Gemini API 응답
        
        Returns:
            {'response': str, 'grounding_metadata': dict}
        """
        # 응답 추출
        response_text = response.text if (hasattr(response, 'text') and response.text) else ""
        if not response_text:
            response_text = str(response) if hasattr(response, '__str__') else "응답을 가져올 수 없습니다."
        
        # Grounding 메타데이터 추출 (인용 정보)
        grounding_metadata = None
        if hasattr(response, 'candidates') and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                try:
                    if hasattr(candidate.grounding_metadata, 'model_dump'):
                        grounding_metadata = candidate.grounding_metadata.model_dump()
                    elif hasattr(candidate.grounding_metadata, 'dict'):
                        grounding_metadata = candidate.grounding_metadata.dict()
                    else:
                        grounding_metadata = dict(candidate.grounding_metadata) if candidate.grounding_metadata else None
                except Exception:
                    grounding_metadata = None
        
        return {
            'response': response_text,
            'grounding_metadata': grounding_metadata
        }

