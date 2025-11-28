"""
시나리오 관리 서비스

What if 시나리오 생성, 저장, 조회, Fork 기능을 제공합니다.
"""

import os
import json
import uuid
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from google import genai
from google.genai.types import Tool, FileSearch
from app.services.api_key_manager import get_api_key_manager


class ScenarioManagementService:
    """시나리오 생성 및 관리 서비스"""
    
    def __init__(self):
        """시나리오 관리 서비스 초기화"""
        self.api_key_manager = get_api_key_manager()
        self.api_key = self.api_key_manager.get_current_key()
        self.client = genai.Client(api_key=self.api_key)
        
        # 프로젝트 루트 경로
        current_file = Path(__file__)
        self.project_root = current_file.parent.parent.parent
        
        # 데이터 디렉토리 경로
        self.scenarios_dir = self.project_root / "data" / "scenarios"
        self.public_scenarios_dir = self.scenarios_dir / "public"
        self.private_scenarios_dir = self.scenarios_dir / "private"
        self.forked_scenarios_dir = self.scenarios_dir / "forked"
        
        # 디렉토리 생성
        self.public_scenarios_dir.mkdir(parents=True, exist_ok=True)
        self.private_scenarios_dir.mkdir(parents=True, exist_ok=True)
        self.forked_scenarios_dir.mkdir(parents=True, exist_ok=True)
        
        # File Search Store 정보 로드
        self._load_store_info()
    
    def _load_store_info(self):
        """File Search Store 정보 로드"""
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        
        # 현재 API 키 인덱스에 맞는 Store 정보 파일 찾기
        current_key_index = self.api_key_manager.current_key_index
        store_info_path = project_root / "data" / f"file_search_store_info_key{current_key_index + 1}.json"
        
        if not store_info_path.exists():
            store_info_path = project_root / "data" / "file_search_store_info.json"
        
        try:
            with open(store_info_path, 'r', encoding='utf-8') as f:
                store_info = json.load(f)
                self.store_name = store_info.get('store_name')
        except FileNotFoundError:
            self.store_name = None
    
    def create_scenario(
        self,
        scenario_name: str,
        book_title: str,
        character_name: str,
        descriptions: Dict[str, str],  # 자연어 설명
        creator_id: str,
        is_public: bool = False
    ) -> Dict:
        """
        시나리오 생성
        
        Args:
            scenario_name: 시나리오 이름
            book_title: 책 제목
            character_name: 캐릭터 이름
            descriptions: 자연어 설명 딕셔너리
                - character_property_changes: 캐릭터 속성 변경 설명
                - event_alterations: 사건 변경 설명
                - setting_modifications: 배경 변경 설명
            creator_id: 생성자 ID
            is_public: 공개 여부
        
        Returns:
            생성된 시나리오 정보
        """
        scenario_id = str(uuid.uuid4())
        
        # 자연어 설명을 구조화된 데이터로 변환
        parsed_data = {}
        
        if descriptions.get("character_property_changes", {}).get("enabled"):
            parsed_data["character_property_changes"] = self._parse_character_property_changes(
                descriptions["character_property_changes"]["description"],
                book_title,
                character_name
            )
        else:
            parsed_data["character_property_changes"] = {"enabled": False}
        
        if descriptions.get("event_alterations", {}).get("enabled"):
            parsed_data["event_alterations"] = self._parse_event_alterations(
                descriptions["event_alterations"]["description"],
                book_title
            )
        else:
            parsed_data["event_alterations"] = {"enabled": False}
        
        if descriptions.get("setting_modifications", {}).get("enabled"):
            parsed_data["setting_modifications"] = self._parse_setting_modifications(
                descriptions["setting_modifications"]["description"],
                book_title
            )
        else:
            parsed_data["setting_modifications"] = {"enabled": False}
        
        # 시나리오 타입 확인
        scenario_types = {
            "character_property_changes": parsed_data["character_property_changes"]["enabled"],
            "event_alterations": parsed_data["event_alterations"]["enabled"],
            "setting_modifications": parsed_data["setting_modifications"]["enabled"]
        }
        
        # 사용자 원본 입력값 저장 (메타데이터)
        user_inputs = {
            "character_property_changes": descriptions.get("character_property_changes", {}).get("description", "") if descriptions.get("character_property_changes", {}).get("enabled") else None,
            "event_alterations": descriptions.get("event_alterations", {}).get("description", "") if descriptions.get("event_alterations", {}).get("enabled") else None,
            "setting_modifications": descriptions.get("setting_modifications", {}).get("description", "") if descriptions.get("setting_modifications", {}).get("enabled") else None
        }
        
        # 시나리오 메타데이터 생성
        scenario = {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "book_title": book_title,
            "character_name": character_name,
            "creator_id": creator_id,
            "is_public": is_public,
            "fork_count": 0,
            "like_count": 0,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "scenario_types": scenario_types,
            "user_inputs": user_inputs,  # 사용자 원본 입력값 저장
            "character_property_changes": parsed_data["character_property_changes"],
            "event_alterations": parsed_data["event_alterations"],
            "setting_modifications": parsed_data["setting_modifications"],
            "first_conversation": None  # 나중에 업데이트됨
        }
        
        # 시나리오 저장
        self._save_scenario(scenario, creator_id)
        
        return {
            "scenario_id": scenario_id,
            "status": "created",
            "parsed_data": parsed_data,
            "message": "시나리오가 생성되었습니다. 첫 대화를 시작하세요."
        }
    
    def _parse_character_property_changes(
        self,
        description: str,
        book_title: str,
        character_name: str
    ) -> Dict:
        """
        자연어 설명을 구조화된 캐릭터 속성 변경 데이터로 변환
        
        Args:
            description: 자연어 설명 (예: "헤르미온이가 그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해졌다면?")
            book_title: 책 제목
            character_name: 캐릭터 이름
        
        Returns:
            구조화된 캐릭터 속성 변경 데이터
        """
        if not self.store_name:
            raise ValueError("File Search Store가 설정되지 않았습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.")
        
        # LLM을 사용하여 변경점 분석
        prompt = f"""Analyze this scenario change for the character {character_name} from the book "{book_title}".

User's description: {description}

Use File Search to find information about {character_name} in the book, then output ONLY a valid JSON object with this exact structure:

{{
  "changes": [
    {{
      "property_type": "personality_trait",
      "original_value": "what it was originally in the book",
      "altered_value": "what it becomes",
      "description": "brief description of the change",
      "source_reference": "where in the book this was found",
      "source_text": "relevant excerpt from the book (DO NOT include citation markers like [cite: ...])"
    }}
  ]
}}

Available property types: personality_trait, house_assignment, friend_group, background_story, ability, relationship

IMPORTANT:
- Output ONLY the JSON object. No explanations, no markdown, no additional text.
- Do NOT include citation markers like [cite: ...] in source_text.
- Keep source_text concise and relevant."""
        
        # 파싱 재시도 로직 (최대 2번 재시도, 총 3번 시도)
        max_parse_retries = 2
        last_parse_error = None
        
        for parse_attempt in range(max_parse_retries + 1):
            try:
                # Gemini API 호출 (File Search 포함)
                response = self._call_llm_with_file_search(prompt)
                
                # JSON 파싱 시도 (마크다운 코드 블록 제거 포함)
                try:
                    # 마크다운 코드 블록 제거
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:].strip()
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3].strip()
                    
                    # "Here is the JSON requested:" 같은 전처리 텍스트 제거
                    if "```json" in cleaned_response:
                        # ```json 이후부터 추출
                        json_start = cleaned_response.find("```json") + 7
                        json_end = cleaned_response.rfind("```")
                        if json_end > json_start:
                            cleaned_response = cleaned_response[json_start:json_end].strip()
                    elif "```" in cleaned_response:
                        # ``` 이후부터 추출
                        json_start = cleaned_response.find("```") + 3
                        json_end = cleaned_response.rfind("```")
                        if json_end > json_start:
                            cleaned_response = cleaned_response[json_start:json_end].strip()
                    
                    # JSON 객체 시작 위치 찾기
                    json_start_idx = cleaned_response.find("{")
                    if json_start_idx != -1:
                        cleaned_response = cleaned_response[json_start_idx:]
                    
                    parsed = json.loads(cleaned_response)
                    changes = parsed.get("changes", [])
                    
                    # source_text에서 인용 표시 제거
                    for change in changes:
                        if "source_text" in change:
                            # [cite: ...] 패턴 제거
                            change["source_text"] = re.sub(r'\[cite:[^\]]*\]', '', change["source_text"]).strip()
                    
                    # 파싱 성공 시 파싱된 데이터만 반환
                    if not changes:
                        raise ValueError(f"캐릭터 속성 변경 파싱 결과가 비어있습니다. 응답: {response[:500]}")
                    
                    return {
                        "enabled": True,
                        "target_character": character_name,
                        "changes": changes
                    }
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # 파싱 실패 시 재시도 또는 에러 발생
                    last_parse_error = e
                    if parse_attempt < max_parse_retries:
                        # 재시도 전 잠시 대기
                        time.sleep(1)
                        continue
                    else:
                        # 모든 재시도 실패
                        raise ValueError(f"캐릭터 속성 변경 파싱 실패 (재시도 {max_parse_retries}회 후): {str(e)}\n응답: {response[:500]}")
            
            except ValueError as ve:
                # ValueError는 그대로 전파 (파싱 실패 에러)
                raise
            except Exception as e:
                # LLM 호출 실패 등 기타 예외
                if parse_attempt < max_parse_retries:
                    # 재시도 전 잠시 대기
                    time.sleep(1)
                    continue
                else:
                    # 모든 재시도 실패
                    raise ValueError(f"캐릭터 속성 변경 분석 중 오류 발생 (재시도 {max_parse_retries}회 후): {str(e)}")
        
        # 이 코드는 도달하지 않아야 하지만 안전을 위해
        raise ValueError(f"캐릭터 속성 변경 파싱 실패: {str(last_parse_error)}")
    
    def _parse_event_alterations(
        self,
        description: str,
        book_title: str
    ) -> Dict:
        """
        자연어 설명을 구조화된 사건 변경 데이터로 변환
        
        Args:
            description: 자연어 설명 (예: "첫 번째 퀴디치 경기가 발생하지 않았다면?")
            book_title: 책 제목
        
        Returns:
            구조화된 사건 변경 데이터
        """
        if not self.store_name:
            raise ValueError("File Search Store가 설정되지 않았습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.")
        
        # LLM을 사용하여 변경점 분석
        prompt = f"""Analyze this event alteration scenario for the book "{book_title}".

User's description: {description}

Use File Search to find the event in the book, then output ONLY a valid JSON object with this exact structure:

{{
  "alterations": [
    {{
      "event_id": "event_1",
      "event_description": "description of the event",
      "alteration_type": "never_occurred",
      "original_outcome": "what happened in the original story",
      "altered_outcome": "what happens instead",
      "reason": "why this change occurs",
      "impact_level": "high",
      "timeline_branch_point": {{
        "chapter": "chapter number or description",
        "event_description": "the branching event",
        "divergence_point": "divergence_1"
      }},
      "source_reference": "where in the book this was found",
      "source_text": "relevant excerpt from the book (DO NOT include citation markers like [cite: ...])"
    }}
  ]
}}

Alteration types: never_occurred, prevented, outcome_changed, succeeded

IMPORTANT:
- Output ONLY the JSON object. No explanations, no markdown, no additional text.
- Do NOT include citation markers like [cite: ...] in source_text.
- Keep source_text concise and relevant."""
        
        # 파싱 재시도 로직 (최대 2번 재시도, 총 3번 시도)
        max_parse_retries = 2
        last_parse_error = None
        
        for parse_attempt in range(max_parse_retries + 1):
            try:
                # Gemini API 호출 (File Search 포함)
                response = self._call_llm_with_file_search(prompt)
                
                # JSON 파싱 시도 (마크다운 코드 블록 제거 포함)
                try:
                    # 마크다운 코드 블록 제거
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:].strip()
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3].strip()
                    
                    # "Here is the JSON requested:" 같은 전처리 텍스트 제거
                    if "```json" in cleaned_response:
                        # ```json 이후부터 추출
                        json_start = cleaned_response.find("```json") + 7
                        json_end = cleaned_response.rfind("```")
                        if json_end > json_start:
                            cleaned_response = cleaned_response[json_start:json_end].strip()
                    elif "```" in cleaned_response:
                        # ``` 이후부터 추출
                        json_start = cleaned_response.find("```") + 3
                        json_end = cleaned_response.rfind("```")
                        if json_end > json_start:
                            cleaned_response = cleaned_response[json_start:json_end].strip()
                    
                    # JSON 객체 시작 위치 찾기
                    json_start_idx = cleaned_response.find("{")
                    if json_start_idx != -1:
                        cleaned_response = cleaned_response[json_start_idx:]
                    
                    parsed = json.loads(cleaned_response)
                    alterations = parsed.get("alterations", [])
                    
                    # source_text에서 인용 표시 제거
                    for alteration in alterations:
                        if "source_text" in alteration:
                            # [cite: ...] 패턴 제거
                            alteration["source_text"] = re.sub(r'\[cite:[^\]]*\]', '', alteration["source_text"]).strip()
                    
                    # 파싱 성공 시 파싱된 데이터만 반환
                    if not alterations:
                        raise ValueError(f"사건 변경 파싱 결과가 비어있습니다. 응답: {response[:500]}")
                    
                    return {
                        "enabled": True,
                        "alterations": alterations
                    }
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # 파싱 실패 시 재시도 또는 에러 발생
                    last_parse_error = e
                    if parse_attempt < max_parse_retries:
                        # 재시도 전 잠시 대기
                        time.sleep(1)
                        continue
                    else:
                        # 모든 재시도 실패
                        raise ValueError(f"사건 변경 파싱 실패 (재시도 {max_parse_retries}회 후): {str(e)}\n응답: {response[:500]}")
            
            except ValueError as ve:
                # ValueError는 그대로 전파 (파싱 실패 에러)
                raise
            except Exception as e:
                # LLM 호출 실패 등 기타 예외
                if parse_attempt < max_parse_retries:
                    # 재시도 전 잠시 대기
                    time.sleep(1)
                    continue
                else:
                    # 모든 재시도 실패
                    raise ValueError(f"사건 변경 분석 중 오류 발생 (재시도 {max_parse_retries}회 후): {str(e)}")
        
        # 이 코드는 도달하지 않아야 하지만 안전을 위해
        raise ValueError(f"사건 변경 파싱 실패: {str(last_parse_error)}")
    
    def _parse_setting_modifications(
        self,
        description: str,
        book_title: str
    ) -> Dict:
        """
        자연어 설명을 구조화된 배경 변경 데이터로 변환
        
        Args:
            description: 자연어 설명 (예: "1990년대에서 2024년 서울로 배경이 변경되었다면?")
            book_title: 책 제목
        
        Returns:
            구조화된 배경 변경 데이터
        """
        if not self.store_name:
            raise ValueError("File Search Store가 설정되지 않았습니다. 'py scripts/setup_file_search.py'를 실행하여 Store를 설정하세요.")
        
        # LLM을 사용하여 변경점 분석
        prompt = f"""Analyze this setting modification scenario for the book "{book_title}".

User's description: {description}

Use File Search to find information about the original setting in the book, then output ONLY a valid JSON object with this exact structure:

{{
  "modifications": [
    {{
      "modification_type": "time_period",
      "original_value": "original setting value from the book",
      "altered_value": "new setting value",
      "description": "description of the change",
      "source_reference": "where in the book this was found",
      "source_text": "relevant excerpt from the book (DO NOT include citation markers like [cite: ...])"
    }}
  ]
}}

Available modification types: time_period, location, cultural_context, magic_system, technology_level, social_structure

IMPORTANT:
- Output ONLY the JSON object. No explanations, no markdown, no additional text.
- Do NOT include citation markers like [cite: ...] in source_text.
- Keep source_text concise and relevant."""
        
        # 파싱 재시도 로직 (최대 2번 재시도, 총 3번 시도)
        max_parse_retries = 2
        last_parse_error = None
        
        for parse_attempt in range(max_parse_retries + 1):
            try:
                # Gemini API 호출 (File Search 포함)
                response = self._call_llm_with_file_search(prompt)
                
                # JSON 파싱 시도 (마크다운 코드 블록 제거 포함)
                try:
                    # 마크다운 코드 블록 제거
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:].strip()
                    elif cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:].strip()
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3].strip()
                    
                    # "Here is the JSON requested:" 같은 전처리 텍스트 제거
                    if "```json" in cleaned_response:
                        # ```json 이후부터 추출
                        json_start = cleaned_response.find("```json") + 7
                        json_end = cleaned_response.rfind("```")
                        if json_end > json_start:
                            cleaned_response = cleaned_response[json_start:json_end].strip()
                    elif "```" in cleaned_response:
                        # ``` 이후부터 추출
                        json_start = cleaned_response.find("```") + 3
                        json_end = cleaned_response.rfind("```")
                        if json_end > json_start:
                            cleaned_response = cleaned_response[json_start:json_end].strip()
                    
                    # "Here is the JSON requested:" 같은 전처리 텍스트 제거 (정규식 사용)
                    cleaned_response = re.sub(r'^[^{]*', '', cleaned_response, count=1)
                    
                    # JSON 객체 시작 위치 찾기
                    json_start_idx = cleaned_response.find("{")
                    if json_start_idx != -1:
                        cleaned_response = cleaned_response[json_start_idx:]
                    
                    parsed = json.loads(cleaned_response)
                    modifications = parsed.get("modifications", [])
                    
                    # source_text에서 인용 표시 제거
                    for mod in modifications:
                        if "source_text" in mod:
                            # [cite: ...] 패턴 제거
                            mod["source_text"] = re.sub(r'\[cite:[^\]]*\]', '', mod["source_text"]).strip()
                    
                    # 파싱 성공 시 파싱된 데이터만 반환
                    if not modifications:
                        raise ValueError(f"배경 변경 파싱 결과가 비어있습니다. 응답: {response[:500]}")
                    
                    return {
                        "enabled": True,
                        "modifications": modifications
                    }
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # 파싱 실패 시 재시도 또는 에러 발생
                    last_parse_error = e
                    if parse_attempt < max_parse_retries:
                        # 재시도 전 잠시 대기
                        time.sleep(1)
                        continue
                    else:
                        # 모든 재시도 실패
                        raise ValueError(f"배경 변경 파싱 실패 (재시도 {max_parse_retries}회 후): {str(e)}\n응답: {response[:500]}")
            
            except ValueError as ve:
                # ValueError는 그대로 전파 (파싱 실패 에러)
                raise
            except Exception as e:
                # LLM 호출 실패 등 기타 예외
                if parse_attempt < max_parse_retries:
                    # 재시도 전 잠시 대기
                    time.sleep(1)
                    continue
                else:
                    # 모든 재시도 실패
                    raise ValueError(f"배경 변경 분석 중 오류 발생 (재시도 {max_parse_retries}회 후): {str(e)}")
        
        # 이 코드는 도달하지 않아야 하지만 안전을 위해
        raise ValueError(f"배경 변경 파싱 실패: {str(last_parse_error)}")
    
    def _call_llm_with_file_search(self, prompt: str) -> str:
        """
        File Search를 사용하여 LLM 호출
        
        Args:
            prompt: 프롬프트
        
        Returns:
            LLM 응답 텍스트
        """
        max_retries = len(self.api_key_manager.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 현재 API 키로 클라이언트 생성
                current_key = self.api_key_manager.get_current_key()
                
                # API 키가 변경되었으면 클라이언트 재생성 및 Store 정보 다시 로드
                if current_key != self.api_key:
                    self.api_key = current_key
                    self.client = genai.Client(api_key=self.api_key)
                    self._load_store_info()
                
                if not self.store_name:
                    raise ValueError("File Search Store가 설정되지 않았습니다.")
                
                # System instruction 추가 (모델에게 역할 명확히 지정)
                system_instruction = """You are a data processing agent that converts "What If" scenarios into structured JSON data.
Your ONLY job is to output valid JSON. DO NOT output any conversational text, explanations, or markdown code blocks.
Use File Search to find relevant information from the source material, then output ONLY the JSON object."""
                
                # API 호출 (JSON 모드 강제)
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    config={
                        "system_instruction": system_instruction,
                        "tools": [
                            Tool(
                                file_search=FileSearch(
                                    file_search_store_names=[self.store_name]
                                )
                            )
                        ],
                        "response_mime_type": "application/json",  # JSON 응답 강제
                        "temperature": 0.1,  # 정확한 포맷을 위해 낮춤
                        "top_p": 0.8,
                        "max_output_tokens": 8192
                    }
                )
                
                # finish_reason 확인 (RECITATION, SAFETY 등 감지)
                if hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = str(candidate.finish_reason)
                        if 'RECITATION' in finish_reason:
                            # RECITATION: 모델이 응답을 거부함 (재시도 필요)
                            if attempt < max_retries - 1:
                                # 다음 키로 전환하여 재시도
                                if not self.api_key_manager.switch_to_next_key():
                                    raise ValueError("모든 API 키에서 RECITATION이 발생했습니다. 프롬프트를 수정하거나 다른 방법을 시도하세요.")
                                time.sleep(1)
                                continue
                            else:
                                raise ValueError("RECITATION: 모델이 응답을 생성하지 않았습니다. 프롬프트를 더 간결하게 수정하거나 다른 방법을 시도하세요.")
                        elif 'SAFETY' in finish_reason:
                            raise ValueError("SAFETY: 안전 필터에 걸렸습니다. 프롬프트를 수정하세요.")
                        elif 'MAX_TOKENS' in finish_reason:
                            # MAX_TOKENS는 부분 응답이 있을 수 있으므로 계속 진행
                            pass
                
                # 응답 추출 (다양한 방법 시도)
                response_text = ""
                
                # 방법 1: response.text 직접 접근
                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                
                # 방법 2: candidates를 통해 접근
                if not response_text and hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                
                # 최종 검증
                if not response_text or not response_text.strip():
                    raise ValueError("LLM 응답이 비어있습니다. 응답 구조를 확인하세요.")
                
                return response_text.strip()
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Store 접근 권한 에러
                if 'PERMISSION_DENIED' in error_str or 'file search store' in error_str.lower():
                    raise ValueError(f"Store 접근 권한이 없습니다: {str(e)}")
                
                # 할당량 에러가 아니면 즉시 전파
                if not self.api_key_manager._is_quota_error(e):
                    raise
                
                # 마지막 시도면 에러 전파
                if attempt >= max_retries - 1:
                    raise
                
                # 다음 키로 전환
                if not self.api_key_manager.switch_to_next_key():
                    raise ValueError(f"사용 가능한 API 키가 없습니다: {str(e)}")
                
                # 잠시 대기 후 재시도
                time.sleep(1)
        
        # 모든 재시도 실패
        raise Exception(f"LLM 호출 실패: {str(last_error)}")
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        LLM 응답에서 JSON 추출 및 파싱
        
        Args:
            response_text: LLM 응답 텍스트
        
        Returns:
            파싱된 JSON 딕셔너리
        """
        # JSON 코드 블록 제거
        response_text = response_text.strip()
        
        # ```json 또는 ```로 감싸진 경우 제거
        if response_text.startswith("```json"):
            response_text = response_text[7:].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:].strip()
        
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()
        
        # JSON 파싱
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 에러 메시지와 함께 재시도
            raise ValueError(f"JSON 파싱 실패: {str(e)}\n응답: {response_text[:500]}")
    
    def _save_scenario(self, scenario: Dict, user_id: str):
        """시나리오를 파일에 저장"""
        scenario_id = scenario["scenario_id"]
        
        if scenario["is_public"]:
            # 공개 시나리오
            file_path = self.public_scenarios_dir / f"{scenario_id}.json"
        else:
            # 비공개 시나리오
            user_dir = self.private_scenarios_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            file_path = user_dir / f"{scenario_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, ensure_ascii=False, indent=2)
    
    def get_scenario(self, scenario_id: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """
        시나리오 조회
        
        Args:
            scenario_id: 시나리오 ID
            user_id: 사용자 ID (비공개 시나리오 조회용)
        
        Returns:
            시나리오 정보 또는 None
        """
        # 공개 시나리오에서 찾기
        file_path = self.public_scenarios_dir / f"{scenario_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 비공개 시나리오에서 찾기
        if user_id:
            file_path = self.private_scenarios_dir / user_id / f"{scenario_id}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        # 모든 사용자의 비공개 시나리오에서 찾기 (관리자용)
        for user_dir in self.private_scenarios_dir.iterdir():
            if user_dir.is_dir():
                file_path = user_dir / f"{scenario_id}.json"
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
        
        return None
    
    def update_scenario(self, scenario: Dict):
        """시나리오 업데이트"""
        scenario_id = scenario["scenario_id"]
        creator_id = scenario["creator_id"]
        
        scenario["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        if scenario["is_public"]:
            file_path = self.public_scenarios_dir / f"{scenario_id}.json"
        else:
            file_path = self.private_scenarios_dir / creator_id / f"{scenario_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, ensure_ascii=False, indent=2)
    
    def fork_scenario(
        self, 
        scenario_id: str, 
        user_id: str,
        conversation_partner_type: str = "stranger",
        other_main_character: Optional[Dict] = None
    ) -> Dict:
        """
        시나리오 Fork
        
        Args:
            scenario_id: 원본 시나리오 ID
            user_id: Fork하는 사용자 ID
            conversation_partner_type: 대화 상대 유형
            other_main_character: 다른 주인공 정보
        
        Returns:
            Fork된 시나리오 정보
        """
        # 원본 시나리오 조회
        original_scenario = self.get_scenario(scenario_id)
        if not original_scenario:
            raise ValueError(f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        # 이미 Fork했는지 확인
        user_forked_dir = self.forked_scenarios_dir / user_id
        if user_forked_dir.exists():
            for file_path in user_forked_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    forked = json.load(f)
                    if forked.get("original_scenario_id") == scenario_id:
                        raise ValueError("이미 이 시나리오를 Fork했습니다.")
        
        # Fork된 시나리오 생성
        forked_scenario_id = str(uuid.uuid4())
        
        # other_main_character 최소 정보만 저장
        other_main_character_minimal = None
        if other_main_character:
            other_main_character_minimal = {
                "character_name": other_main_character.get("character_name"),
                "book_title": other_main_character.get("book_title")
            }
        
        # 원본 시나리오의 first_conversation 가져오기
        original_first_conv = original_scenario.get("first_conversation")
        
        # conversation_partner_type이 원본과 같은지 확인
        # 같으면 reference_first_conversation 저장, 다르면 None (대화 맥락이 의미 없음)
        reference_first_conversation = None
        if original_first_conv:
            original_partner_type = original_first_conv.get("conversation_partner_type", "stranger")
            
            # conversation_partner_type이 같으면 기존 대화 맥락 사용 가능
            if conversation_partner_type == original_partner_type:
                # other_main_character도 비교 (other_main_character인 경우)
                if conversation_partner_type == "other_main_character":
                    original_other = original_first_conv.get("other_main_character")
                    if original_other and other_main_character_minimal:
                        # character_name과 book_title 비교
                        if (original_other.get("character_name") == other_main_character_minimal.get("character_name") and
                            original_other.get("book_title") == other_main_character_minimal.get("book_title")):
                            reference_first_conversation = original_first_conv
                    elif original_other == other_main_character_minimal:  # 둘 다 None이거나 동일
                        reference_first_conversation = original_first_conv
                else:
                    # stranger인 경우 타입만 같으면 됨
                    reference_first_conversation = original_first_conv
        
        forked_scenario = {
            "forked_scenario_id": forked_scenario_id,
            "original_scenario_id": scenario_id,
            "forked_by_user_id": user_id,
            "forked_at": datetime.utcnow().isoformat() + "Z",
            "is_regenerable": False,
            "scenario_name": f"{original_scenario['scenario_name']} (Fork)",
            "book_title": original_scenario["book_title"],
            "character_name": original_scenario["character_name"],
            "scenario_types": original_scenario["scenario_types"],
            "user_inputs": original_scenario.get("user_inputs"),  # 원본 사용자 입력값 포함
            "character_property_changes": original_scenario["character_property_changes"],
            "event_alterations": original_scenario["event_alterations"],
            "setting_modifications": original_scenario["setting_modifications"],
            "reference_first_conversation": reference_first_conversation,  # conversation_partner_type이 같을 때만 저장
            "conversations": []
        }
        
        # reference_first_conversation이 없을 때만 최상위 레벨에 저장 (중복 방지)
        # reference_first_conversation이 있으면 그 안에 이미 conversation_partner_type과 other_main_character가 있음
        if not reference_first_conversation:
            forked_scenario["conversation_partner_type"] = conversation_partner_type
            forked_scenario["other_main_character"] = other_main_character_minimal
        
        # Fork된 시나리오 저장
        user_forked_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_forked_dir / f"{forked_scenario_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(forked_scenario, f, ensure_ascii=False, indent=2)
        
        # 원본 시나리오의 fork_count 증가
        original_scenario["fork_count"] = original_scenario.get("fork_count", 0) + 1
        self.update_scenario(original_scenario)
        
        return forked_scenario
    
    def get_public_scenarios(
        self,
        book_title: Optional[str] = None,
        character_name: Optional[str] = None,
        sort: str = "popular"
    ) -> List[Dict]:
        """
        공개 시나리오 목록 조회
        
        Args:
            book_title: 책 제목 필터
            character_name: 캐릭터 이름 필터
            sort: 정렬 방식 ("popular", "recent")
        
        Returns:
            공개 시나리오 목록
        """
        scenarios = []
        
        for file_path in self.public_scenarios_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
                
                # 필터링
                if book_title and scenario.get("book_title") != book_title:
                    continue
                if character_name and scenario.get("character_name") != character_name:
                    continue
                
                # 미리보기 정보 추가
                preview = {
                    "initial_message": "",
                    "initial_response": ""
                }
                if scenario.get("first_conversation"):
                    messages = scenario["first_conversation"].get("messages", [])
                    if len(messages) > 0:
                        preview["initial_message"] = messages[0].get("content", "")
                    if len(messages) > 1:
                        preview["initial_response"] = messages[1].get("content", "")
                
                scenarios.append({
                    "scenario_id": scenario["scenario_id"],
                    "scenario_name": scenario["scenario_name"],
                    "book_title": scenario["book_title"],
                    "character_name": scenario["character_name"],
                    "creator_username": scenario.get("creator_id", "unknown"),
                    "fork_count": scenario.get("fork_count", 0),
                    "like_count": scenario.get("like_count", 0),
                    "first_conversation_preview": preview,
                    "created_at": scenario.get("created_at", "")
                })
        
        # 정렬
        if sort == "popular":
            scenarios.sort(key=lambda x: (x["fork_count"] + x["like_count"]), reverse=True)
        elif sort == "recent":
            scenarios.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return scenarios
    

