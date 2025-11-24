"""
캐릭터 대화 서비스

Gemini File Search를 활용하여 책 속 인물과 대화합니다.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from google import genai
from google.genai.types import Tool, FileSearch
from app.services.api_key_manager import get_api_key_manager

class CharacterChatService:
    """책 속 인물과 대화하는 서비스"""
    
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
        # 현재 API 키 인덱스에 맞는 Store 정보 파일 찾기
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
        
        # 캐릭터 정보 로드
        self.characters = self._load_characters()
        
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
    
    
    def _load_characters(self, path: str = None) -> List[Dict]:
        """캐릭터 정보 로드"""
        if path is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            path = project_root / "data" / "characters.json"
        else:
            path = Path(path)
            if not path.is_absolute():
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent
                path = project_root / path
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('characters', [])
        except FileNotFoundError:
            return []
    
    def get_available_characters(self) -> List[Dict]:
        """사용 가능한 캐릭터 목록 반환"""
        return [
            {
                'character_name': c['character_name'],
                'book_title': c['book_title'],
                'author': c['author']
            }
            for c in self.characters
        ]
    
    def get_character_info(self, character_name: str, book_title: Optional[str] = None) -> Optional[Dict]:
        """특정 캐릭터 정보 가져오기
        
        Args:
            character_name: 캐릭터 이름
            book_title: 책 제목 (선택, 제공되면 같은 책의 캐릭터만 검색)
        
        Returns:
            캐릭터 정보 딕셔너리 또는 None
        """
        for char in self.characters:
            if char['character_name'].lower() == character_name.lower():
                # book_title이 제공되면 일치하는지 확인
                if book_title is None or char['book_title'].lower() == book_title.lower():
                    return char
        return None
    
    def create_persona_prompt(self, character: Dict, output_language: str = "ko") -> str:
        """페르소나 프롬프트 생성 (system_instruction용)
        
        Args:
            character: 캐릭터 정보 딕셔너리
            output_language: 출력 언어 ("ko", "en", "ja", "zh" 등)
        """
        # 언어별 출력 지시
        language_instructions = {
            "ko": "You must respond in Korean (한국어).",
            "en": "You must respond in English.",
            "ja": "You must respond in Japanese (日本語).",
            "zh": "You must respond in Chinese (中文).",
            "es": "You must respond in Spanish (Español).",
            "fr": "You must respond in French (Français).",
            "de": "You must respond in German (Deutsch).",
        }
        
        language_instruction = language_instructions.get(output_language.lower(), f"You must respond in {output_language}.")
        
        prompt = f"""You are {character['character_name']} from '{character['book_title']}'.

【Persona】
{character['persona']}

【Speaking Style】
{character['speaking_style']}

【Output Language】
{language_instruction}

【Conversation Rules】
1. Always respond from {character['character_name']}'s perspective.

2. REQUIRED: You must use the File Search tool
   - Before answering any question, you must first use the File Search tool to search for the original content from the book.
   - It is absolutely forbidden to answer using only general knowledge without using File Search.
   - Use File Search to check if the user's question relates to specific scenes, characters, events, or dialogues in the book.
   - If you do not use File Search, the accuracy and reliability of your answer will be compromised.

3. Citing specific scenes, dialogues, and events from the book enhances the reliability and immersion of your response.
   - When you need to cite, base your citations on File Search results and quote the original text from the book.

4. Reflect the character's personality, experiences, and values.

5. Maintain natural and immersive conversation.

6. For content not in the book, use your imagination in a way that matches the character's personality, but do not contradict the book's settings.
   - However, before using your imagination, first check with File Search if there is any related content."""
        
        return prompt
    
    def chat(
        self,
        character_name: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        book_title: Optional[str] = None,
        output_language: str = "ko",
        system_instruction: Optional[str] = None
    ) -> Dict:
        """
        캐릭터와 대화
        
        Args:
            character_name: 대화할 캐릭터 이름
            user_message: 사용자 메시지
            conversation_history: 이전 대화 기록 (선택)
            book_title: 책 제목 (선택, 같은 책의 여러 캐릭터 구분용)
            output_language: 출력 언어 (기본값: "ko", 지원: "ko", "en", "ja", "zh" 등)
        
        Returns:
            응답 딕셔너리 (response, character_info, grounding_metadata)
        """
        # 캐릭터 정보 가져오기
        character = self.get_character_info(character_name, book_title)
        if not character:
            error_msg = f"캐릭터를 찾을 수 없습니다: {character_name}"
            if book_title:
                error_msg += f" (책: {book_title})"
            return {
                'error': error_msg,
                'available_characters': self.get_available_characters()
            }
        
        # 페르소나 프롬프트 생성 (제공되지 않으면 기본 생성)
        if system_instruction is None:
            system_instruction = self.create_persona_prompt(character, output_language)
        
        # 대화 기록 포함
        contents = []
        if conversation_history:
            for msg in conversation_history[-5:]:  # 최근 5개만
                # 빈 딕셔너리나 잘못된 형식 필터링
                if isinstance(msg, dict) and msg.get('role') and msg.get('parts'):
                    contents.append(msg)
        
        # 사용자 메시지 추가
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })
        
        # 재시도 로직으로 API 호출
        max_retries = len(self.api_key_manager.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 현재 API 키로 클라이언트 생성
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
                
                client = self.client
                
                # Store가 없으면 에러
                if not self.store_name:
                    return {
                        'error': "File Search Store가 설정되지 않았습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.",
                        'character_name': character['character_name']
                    }
                
                # API 호출
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        "system_instruction": system_instruction,
                        "tools": [
                            Tool(
                                file_search=FileSearch(
                                    file_search_store_names=[self.store_name]
                                )
                            )
                        ],
                        "temperature": 0.8,
                        "top_p": 0.95,
                        "max_output_tokens": 4096  # 대화 응답은 4096 토큰으로 제한 (약 3000-4000자) - 품질 향상을 위해 증가
                    }
                )
                
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
                    'character_name': character['character_name'],
                    'book_title': character['book_title'],
                    'output_language': output_language,
                    'grounding_metadata': grounding_metadata
                }
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Store 접근 권한 에러 감지
                if 'PERMISSION_DENIED' in error_str or 'file search store' in error_str.lower():
                    return {
                        'error': f"Store 접근 권한이 없습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요: {str(e)}",
                        'character_name': character['character_name']
                    }
                
                # 할당량 에러가 아니면 즉시 반환
                if not self.api_key_manager._is_quota_error(e):
                    return {
                        'error': f"응답 생성 실패: {str(e)}",
                        'character_name': character['character_name']
                    }
                
                # 마지막 시도면 에러 반환
                if attempt >= max_retries - 1:
                    return {
                        'error': f"모든 API 키의 할당량이 초과되었습니다: {str(e)}",
                        'character_name': character['character_name']
                    }
                
                # 다음 키로 전환
                if not self.api_key_manager.switch_to_next_key():
                    return {
                        'error': f"사용 가능한 API 키가 없습니다: {str(e)}",
                        'character_name': character['character_name']
                    }
                
                # 잠시 대기 후 재시도
                time.sleep(1)
        
        # 모든 재시도 실패
        return {
            'error': f"응답 생성 실패: {str(last_error)}",
            'character_name': character['character_name']
        }
    
    def stream_chat(
        self,
        character_name: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        book_title: Optional[str] = None,
        output_language: str = "ko"
    ):
        """
        캐릭터와 스트리밍 대화
        
        Args:
            character_name: 대화할 캐릭터 이름
            user_message: 사용자 메시지
            conversation_history: 이전 대화 기록 (선택)
            book_title: 책 제목 (선택, 같은 책의 여러 캐릭터 구분용)
            output_language: 출력 언어 (기본값: "ko", 지원: "ko", "en", "ja", "zh" 등)
        
        Yields:
            응답 청크
        """
        # 캐릭터 정보 가져오기
        character = self.get_character_info(character_name, book_title)
        if not character:
            error_msg = f"캐릭터를 찾을 수 없습니다: {character_name}"
            if book_title:
                error_msg += f" (책: {book_title})"
            yield {
                'error': error_msg,
                'available_characters': self.get_available_characters()
            }
            return
        
        # 페르소나 프롬프트 생성
        system_instruction = self.create_persona_prompt(character, output_language)
        
        # 대화 기록 포함
        contents = []
        if conversation_history:
            for msg in conversation_history[-5:]:
                # 빈 딕셔너리나 잘못된 형식 필터링
                if isinstance(msg, dict) and msg.get('role') and msg.get('parts'):
                    contents.append(msg)
        
        # 사용자 메시지 추가
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}]
        })
        
        # 재시도 로직으로 API 호출
        max_retries = len(self.api_key_manager.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 현재 API 키로 클라이언트 생성
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
                
                client = self.client
                
                # Store가 없으면 에러
                if not self.store_name:
                    yield {
                        'error': "File Search Store가 설정되지 않았습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.",
                        'character_name': character['character_name']
                    }
                    return
                
                # 스트리밍 API 호출
                response_stream = client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        "system_instruction": system_instruction,
                        "tools": [
                            Tool(
                                file_search=FileSearch(
                                    file_search_store_names=[self.store_name]
                                )
                            )
                        ],
                        "temperature": 0.8,
                        "top_p": 0.95,
                        "max_output_tokens": 4096  # 대화 응답은 4096 토큰으로 제한 (약 3000-4000자) - 품질 향상을 위해 증가
                    }
                )
                
                # 청크 단위로 응답 전송
                for chunk in response_stream:
                    if hasattr(chunk, 'text'):
                        yield {
                            'chunk': chunk.text,
                            'character_name': character['character_name']
                        }
                
                # 성공적으로 완료되면 반환
                return
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Store 접근 권한 에러 감지
                if 'PERMISSION_DENIED' in error_str or 'file search store' in error_str.lower():
                    yield {
                        'error': f"Store 접근 권한이 없습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요: {str(e)}",
                        'character_name': character['character_name']
                    }
                    return
                
                # 할당량 에러가 아니면 즉시 반환
                if not self.api_key_manager._is_quota_error(e):
                    yield {
                        'error': f"스트리밍 실패: {str(e)}",
                        'character_name': character['character_name']
                    }
                    return
                
                # 마지막 시도면 에러 반환
                if attempt >= max_retries - 1:
                    yield {
                        'error': f"모든 API 키의 할당량이 초과되었습니다: {str(e)}",
                        'character_name': character['character_name']
                    }
                    return
                
                # 다음 키로 전환
                if not self.api_key_manager.switch_to_next_key():
                    yield {
                        'error': f"사용 가능한 API 키가 없습니다: {str(e)}",
                        'character_name': character['character_name']
                    }
                    return
                
                # 잠시 대기 후 재시도
                time.sleep(1)
        
        # 모든 재시도 실패
        yield {
            'error': f"스트리밍 실패: {str(last_error)}",
            'character_name': character['character_name']
        }

