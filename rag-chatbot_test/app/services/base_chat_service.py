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
        
        # 응답 텍스트 정리: 중복 제거 및 메타데이터 제거
        response_text = self._clean_response_text(response_text)
        
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
    
    def _clean_response_text(self, text: str) -> str:
        """
        응답 텍스트 정리: 중복 제거 및 메타데이터 제거
        
        Args:
            text: 원본 응답 텍스트
        
        Returns:
            정리된 응답 텍스트
        """
        if not text:
            return text
        
        import re
        
        # 1. 메타데이터 블록 제거
        # 패턴: "The Creature, a main character from..." 같은 설명 블록
        # 또는 "Victor Frankenstein successfully animates..." 같은 시나리오 설명
        # 또는 "The story's setting has been modified: location: Changed from..." 같은 설정 설명
        
        # 메타데이터 패턴 (더 포괄적으로)
        metadata_patterns = [
            r'[A-Z][a-z]+ [A-Z][a-z]+,?\s*a main character from',  # "The Creature, a main character from"
            r'[A-Z][a-z]+ [A-Z][a-z]+ successfully',  # "Victor Frankenstein successfully"
            r'setting has been modified',
            r'Changed from\s*"[^"]+"\s*to\s*"[^"]+"',
            r'location:\s*Changed from',
            r'would likely remain',
            r'trying to understand',
            r'guiding it towards',
            r'integration into society',
            r'The story\'s setting',
            r'alternate timeline',
            r'character from \'[^\']+\''
        ]
        
        # 텍스트를 문장 단위로 분리
        sentences = re.split(r'([.!?]\s+)', text)
        cleaned_sentences = []
        
        for i in range(0, len(sentences), 2):
            if i >= len(sentences):
                break
            
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 메타데이터 패턴 확인
            is_metadata = False
            for pattern in metadata_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    is_metadata = True
                    break
            
            if is_metadata:
                continue
            
            cleaned_sentences.append(sentence)
        
        # 정리된 문장들을 합치기
        cleaned_text = ' '.join(cleaned_sentences).strip()
        
        # 2. 중복된 문단 제거 (같은 내용이 반복되는 경우)
        # 문단 단위로 분리
        paragraphs = re.split(r'\n\s*\n', cleaned_text)
        unique_paragraphs = []
        seen_paragraphs = set()
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 문단 정규화 (공백 정규화, 소문자 변환)
            normalized_para = re.sub(r'\s+', ' ', para.lower().strip())
            
            # 너무 짧은 문단은 제외 (1-2단어만 있는 경우)
            if len(normalized_para.split()) < 3:
                continue
            
            if normalized_para and normalized_para not in seen_paragraphs:
                seen_paragraphs.add(normalized_para)
                unique_paragraphs.append(para)
        
        final_text = '\n\n'.join(unique_paragraphs).strip()
        
        # 3. 최종 정리: 연속된 공백과 줄바꿈 정리
        final_text = re.sub(r'[ \t]+', ' ', final_text)  # 여러 공백을 하나로
        final_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_text)  # 여러 줄바꿈을 두 개로
        
        # 4. 빈 응답이면 원본 반환 (정리 과정에서 모든 내용이 제거된 경우)
        if not final_text or len(final_text.strip()) < 10:
            return text
        
        return final_text.strip()

