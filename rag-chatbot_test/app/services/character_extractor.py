"""
Character Extractor Service

chargraph의 CharacterExtractor 기능을 gajiAI 프로젝트에 통합
소설 텍스트에서 캐릭터와 관계를 추출하는 서비스
"""

import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import google.genai as genai
import structlog

from app.services.api_key_manager import get_api_key_manager

logger = structlog.get_logger(__name__)


class CharacterExtractorService:
    """캐릭터 추출 서비스 - chargraph 기능 통합"""
    
    def __init__(self):
        """초기화"""
        self.api_key_manager = get_api_key_manager()
        self.model = "gemini-2.5-flash"
        self.max_retries = 100
        self.retry_delay = 60  # seconds
        
        # 현재 API 키로 클라이언트 초기화
        self._update_client()
    
    def _update_client(self):
        """현재 API 키로 클라이언트 업데이트"""
        try:
            api_key = self.api_key_manager.get_current_key()
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.error("character_extractor_client_init_failed", error=str(e))
            raise
    
    def _switch_to_next_key(self) -> bool:
        """다음 API 키로 전환"""
        try:
            if self.api_key_manager.switch_to_next_key():
                self._update_client()
                logger.info("character_extractor_key_switched")
                return True
            return False
        except Exception as e:
            logger.error("character_extractor_key_switch_failed", error=str(e))
            return False
    
    def _is_quota_exceeded_error(self, error: Exception) -> bool:
        """할당량 초과 에러인지 확인"""
        error_str = str(error).lower()
        quota_indicators = [
            '429',
            'resource_exhausted',
            'quota',
            'rate limit',
            'rate_limit',
            'too many requests'
        ]
        return any(indicator in error_str for indicator in quota_indicators)
    
    def _create_messages(
        self,
        text: str,
        previous_json: Optional[Dict[str, Any]] = None,
        desc_sentences: Optional[int] = None,
        generate_portraits: bool = False,
        copies: int = 1,
        max_main_characters: Optional[int] = None
    ) -> list:
        """API 요청용 메시지 생성"""
        system_prompt = """You are a literary analyst specializing in character extraction and relationship mapping. Your task is to:

1. Character Identification:"""
        
        if max_main_characters is not None:
            system_prompt += f"""
   - FIRST, identify the PROTAGONIST (main character) of the story - the central character around whom the plot revolves
   - THEN, extract the protagonist plus other characters who have relationship weights of 3.0 or higher with the protagonist
   - Character selection criteria:
     * The protagonist (1 character) - the main character of the story
     * Characters with relationship weight >= 3.0 with the protagonist, ranked by weight (highest first)
     * Maximum of {max_main_characters - 1} additional characters (excluding protagonist)
     * If fewer than {max_main_characters - 1} characters have weight >= 3.0, include only those that meet the criteria (do NOT force to reach {max_main_characters} total)
     * Do NOT filter by main_character status - select based ONLY on relationship weight with the protagonist
     * Include characters regardless of whether they are main or supporting characters
     * Focus on characters who have meaningful interactions/relationships with the protagonist (weight >= 3.0)
   - Assign unique ID numbers to each character (ensure no duplicates)
   - Determine their common name (most frequently used in text)
   - List ALL references to them (nicknames, titles, etc.)
   - IMPORTANT: Extract the protagonist plus all characters with relationship weight >= 3.0 to the protagonist (up to {max_main_characters} total characters). If fewer characters meet the weight >= 3.0 criteria, extract only those that qualify."""
        else:
            system_prompt += """
   - Extract EVERY character mentioned in the text:
     * Include all characters regardless of their role or significance
     * Do not skip minor or briefly mentioned characters
     * If a character is named or described, they must be included
   - Assign unique ID numbers to each character (ensure no duplicates)
   - Determine their common name (most frequently used in text)
   - List ALL references to them (nicknames, titles, etc.)
   - Identify main characters based on:
     * Frequency of appearance
     * Plot significance
     * Number of interactions with others"""
        
        system_prompt += """

2. Relationship Analysis:
   - Document ALL character interactions, even brief ones
   - Ensure no duplicate relationships (check both directions: A→B and B→A)
   - For each relationship, provide:
     * Weight (1-10) based on:
       - Frequency of interaction
       - Significance of interactions
       - Impact on plot
     * Positivity scale (-1 to +1):
       - Negative values (-1 to -0.1) for hostile/antagonistic relationships
       - Zero (0) for neutral/professional relationships
       - Positive values (0.1 to 1) for friendly/supportive relationships
       Examples:
       - -1.0: Mortal enemies, intense hatred
       - -0.5: Rivals, strong dislike
       - 0.0: Neutral acquaintances
       - 0.5: Friends, positive relationship
       - 1.0: Best friends, family, deep love
   - Include relationship descriptors (family, friends, enemies, brief encounter, lovers, met in the elevator, etc.)

3. Special Instructions:"""
        
        if max_main_characters is None:
            system_prompt += """
   - Include ALL characters, no matter how minor their role
   - Be thorough in relationship mapping
   - Consider indirect interactions
   - Note character development and changing relationships
   - Ensure every character has at least one connection
   - Check for and eliminate any duplicate characters or relationships
   - Never omit a character just because they:
     * Appear only briefly
     * Have few or weak relationships
     * Seem insignificant to the plot
     * Are only mentioned in passing"""
        else:
            system_prompt += f"""
   - Focus ONLY on the protagonist and characters with relationship weight >= 3.0 to the protagonist (up to {max_main_characters} total characters)
   - Map relationships ONLY between these selected characters
   - Be thorough in relationship mapping between all selected characters
   - Ensure every character has at least one connection with another character
   - Only include relationships with weight >= 3.0 when selecting characters
   - If fewer than {max_main_characters} characters have weight >= 3.0 with the protagonist, include only those that qualify
   - Check for and eliminate any duplicate characters or relationships"""

        if desc_sentences is not None:
            system_prompt += f"""

4. Character Descriptions:
   - For each character, provide:
     * A concise description limited to {desc_sentences} sentences
     * Focus on their role, personality traits, and narrative significance
     * Include key story contributions and character development"""

        if generate_portraits:
            system_prompt += """
   
5. Portrait Generation:
   - For each character, create a detailed prompt for AI image generation that captures:
     * Physical appearance and distinguishing features
     * Clothing and style
     * Facial expressions and emotional state
     * Setting or background elements that reflect their role
     * Artistic style suggestions for consistent character representation"""

        if previous_json:
            if max_main_characters is not None:
                system_prompt += f"\n\nPreliminary character and relationship data: {json.dumps(previous_json)}\nCarefully update this data: ensure you have the protagonist plus characters with relationship weight >= 3.0 to the protagonist (up to {max_main_characters} total characters). If fewer characters have weight >= 3.0, include only those that qualify. Prioritize characters with highest relationship weights to the protagonist regardless of main_character status, add missing relationships, verify weights and positivity (ensure relationship weights are >= 3.0), ensure all characters have connections, and check for any duplicate characters or relationships."
            else:
                system_prompt += f"\n\nPreliminary character and relationship data: {json.dumps(previous_json)}\nCarefully update this data: add any missing characters (no matter how minor or briefly mentioned), add missing relationships, verify weights and positivity, ensure all characters have connections, and check for any duplicate characters or relationships. Every character in the text must be included, even those with minimal roles or single appearances."

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [{"type": "text", "text": "\n\n".join([text] * copies)}]}
        ]
    
    def _get_schema(
        self,
        desc_sentences: Optional[int] = None,
        generate_portraits: bool = False
    ) -> Dict[str, Any]:
        """JSON 스키마 반환"""
        character_properties = {
            "id": {
                "type": "NUMBER",
                "description": "Unique identifier for the character that remains consistent across iterations"
            },
            "common_name": {
                "type": "STRING",
                "description": "The most frequently used name for this character in the text"
            },
            "main_character": {
                "type": "BOOLEAN",
                "description": "True if this is a major character based on frequency of appearance, plot significance, and number of interactions"
            },
            "names": {
                "type": "ARRAY",
                "description": "All variations of the character's name, including nicknames, titles, and other references used in the text",
                "items": {"type": "STRING"}
            }
        }

        if desc_sentences is not None:
            character_properties["description"] = {
                "type": "STRING",
                "description": "Character's role in the story, personality traits, and narrative significance"
            }

        if generate_portraits:
            character_properties["portrait_prompt"] = {
                "type": "STRING",
                "description": "Detailed prompt for AI image generation of the character"
            }

        return {
            "type": "OBJECT",
            "properties": {
                "characters": {
                    "type": "ARRAY",
                    "description": "Characters and connections.",
                    "items": {
                        "type": "OBJECT",
                        "properties": character_properties,
                        "required": ["id", "names", "common_name", "main_character"]
                    }
                },
                "relations": {
                    "type": "ARRAY",
                    "description": "List of each pair of characters who met",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "id1": {
                                "type": "NUMBER",
                                "description": "Unique identifier of the first character in the relationship pair",
                            },
                            "id2": {
                                "type": "NUMBER",
                                "description": "Unique identifier of the second character in the relationship pair",
                            },
                            "relation": {
                                "type": "ARRAY",
                                "description": "Types of relationships between the characters (e.g., family, friends, enemies, colleagues)",
                                "items": {"type": "STRING"}
                            },
                            "weight": {
                                "type": "NUMBER",
                                "description": "Strength of the relationship from 1 (minimal) to 10 (strongest) based on frequency and significance of interactions"
                            },
                            "positivity": {
                                "type": "NUMBER",
                                "description": "Emotional quality of the relationship from -1 (hostile) through 0 (neutral) to 1 (positive)"
                            }
                        },
                        "required": ["id1", "id2", "relation", "weight", "positivity"]
                    }
                },
            },
            "required": ["characters", "relations"]
        }
    
    def _make_request(
        self,
        messages: list,
        desc_sentences: Optional[int] = None,
        generate_portraits: bool = False,
        temperature: float = 1
    ) -> dict:
        """API 요청 (재시도 및 키 전환 포함)"""
        model_name = self.model
        combined_prompt = f"{messages[0]['content']}\n\nInput text:\n{messages[1]['content'][0]['text']}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=combined_prompt,
                    config={
                        "temperature": temperature,
                        "response_mime_type": "application/json",
                        "response_schema": self._get_schema(desc_sentences, generate_portraits)
                    }
                )
                return response
                
            except Exception as e:
                error_str = str(e)
                logger.warning(
                    "character_extraction_api_error",
                    attempt=attempt + 1,
                    error=error_str
                )
                
                # 할당량 초과 에러인 경우 키 전환
                if self._is_quota_exceeded_error(e):
                    logger.info("character_extraction_quota_exceeded_switching_key")
                    if self._switch_to_next_key():
                        continue
                    else:
                        logger.warning("character_extraction_no_more_keys_waiting")
                
                if attempt < self.max_retries - 1:
                    logger.info("character_extraction_retrying", delay=self.retry_delay)
                    time.sleep(self.retry_delay)
        
        raise Exception("Max retries exceeded with all API keys")
    
    def extract_characters(
        self,
        text: str,
        previous_json: Optional[Dict[str, Any]] = None,
        iterations: int = 1,
        desc_sentences: Optional[int] = 2,
        generate_portraits: bool = False,
        copies: int = 1,
        temperature: float = 1.0,
        max_main_characters: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        텍스트에서 캐릭터와 관계 추출
        
        Args:
            text: 소설 텍스트
            previous_json: 이전 추출 결과 (반복 개선용)
            iterations: 반복 횟수
            desc_sentences: 캐릭터 설명 문장 수
            generate_portraits: 포트레이트 프롬프트 생성 여부
            copies: 텍스트 복사본 수
            temperature: 온도
            max_main_characters: 최대 주인공 수 (None이면 모든 캐릭터)
        
        Returns:
            캐릭터와 관계 데이터
        """
        result_json = previous_json
        
        for i in range(iterations):
            logger.info("character_extraction_iteration_started", iteration=i + 1, total=iterations)
            
            max_retries = 10
            retry_delay = 10
            
            for attempt in range(max_retries):
                try:
                    messages = self._create_messages(
                        text,
                        result_json,
                        desc_sentences,
                        generate_portraits,
                        copies,
                        max_main_characters
                    )
                    result = self._make_request(messages, desc_sentences, generate_portraits, temperature)
                    
                    # JSON 파싱
                    if hasattr(result, 'text'):
                        content = json.loads(result.text)
                    elif hasattr(result, 'content'):
                        content = json.loads(result.content)
                    else:
                        content = json.loads(str(result))
                    
                    # 기본 검증
                    if not isinstance(content, dict):
                        raise ValueError("Response content is not a JSON object")
                    if "characters" not in content or "relations" not in content:
                        raise ValueError("Missing required top-level fields")
                    if not isinstance(content["characters"], list) or not isinstance(content["relations"], list):
                        raise ValueError("characters and relations must be arrays")
                    
                    result_json = content
                    logger.info(
                        "character_extraction_iteration_completed",
                        iteration=i + 1,
                        characters_count=len(content.get("characters", [])),
                        relations_count=len(content.get("relations", []))
                    )
                    
                    # 성공하면 다음 반복으로
                    break
                    
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(
                        "character_extraction_parse_error",
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Failed to process iteration {i + 1} after {max_retries} attempts")
            
            # 반복 간 대기 (마지막 반복 제외)
            if i < iterations - 1:
                delay = 60  # 1분 대기
                logger.info("character_extraction_waiting_between_iterations", delay=delay)
                time.sleep(delay)
        
        return result_json

