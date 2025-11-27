"""
캐릭터 대화 서비스

Gemini File Search를 활용하여 책 속 인물과 대화합니다.
"""

from typing import List, Dict, Optional
from app.services.base_chat_service import BaseChatService
from app.services.character_data_loader import CharacterDataLoader


class CharacterChatService(BaseChatService):
    """책 속 인물과 대화하는 서비스"""
    
    def __init__(self, api_key: Optional[str] = None, store_info_path: str = None):
        """
        Args:
            api_key: Gemini API 키 (선택, 없으면 API 키 매니저 사용)
            store_info_path: File Search Store 정보 파일 경로 (None이면 자동 설정)
        """
        # 부모 클래스 초기화 (API 키, Store 정보 등)
        super().__init__(api_key=api_key, store_info_path=store_info_path)
        
        # 캐릭터 정보 로드
        self.characters = CharacterDataLoader.load_characters()
    
    def get_available_characters(self) -> List[Dict]:
        """사용 가능한 캐릭터 목록 반환"""
        return CharacterDataLoader.get_available_characters(self.characters)
    
    def get_character_info(self, character_name: str, book_title: Optional[str] = None) -> Optional[Dict]:
        """특정 캐릭터 정보 가져오기
        
        Args:
            character_name: 캐릭터 이름
            book_title: 책 제목 (선택, 제공되면 같은 책의 캐릭터만 검색)
        
        Returns:
            캐릭터 정보 딕셔너리 또는 None
        """
        return CharacterDataLoader.get_character_info(self.characters, character_name, book_title)
    
    def create_persona_prompt(
        self, 
        character: Dict, 
        output_language: str = "ko",
        conversation_partner_type: str = "stranger",
        other_main_character: Optional[Dict] = None
    ) -> str:
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
        
        # 언어에 맞는 페르소나와 말투 선택
        # 새 구조: persona_ko, persona_en, speaking_style_ko, speaking_style_en 사용
        # 레거시: persona, speaking_style 사용 (호환성)
        if output_language.lower() == "ko":
            persona = character.get('persona_ko') or character.get('persona', '')
            speaking_style = character.get('speaking_style_ko') or character.get('speaking_style', '')
        elif output_language.lower() == "en":
            persona = character.get('persona_en') or character.get('persona', '')
            speaking_style = character.get('speaking_style_en') or character.get('speaking_style', '')
        else:
            # 기타 언어는 영어 버전 사용 (fallback)
            persona = character.get('persona_en') or character.get('persona', '')
            speaking_style = character.get('speaking_style_en') or character.get('speaking_style', '')
        
        prompt = f"""You are {character['character_name']} from '{character['book_title']}'.

【Persona】
{persona}

【Speaking Style】
{speaking_style}

【Output Language】
{language_instruction}

【About the User - CRITICAL】
"""
        if conversation_partner_type == "other_main_character" and other_main_character:
            # 다른 주인공과 대화하는 경우
            other_character_name = other_main_character.get('character_name', 'the other main character')
            prompt += f"""
The person you are talking to is {other_character_name}, a main character from '{character['book_title']}'.
- You know {other_character_name} from the story.
- You have a relationship and shared history with {other_character_name} from the book.
- You should interact with {other_character_name} based on your relationship and experiences from the story.
- Use File Search to recall specific interactions, conversations, and events between you and {other_character_name} from the original book.
- Maintain the dynamics and relationship you had with {other_character_name} in the original story.
"""
        else:
            # 제3의 인물과 대화하는 경우 (기본)
            prompt += f"""
The person you are talking to is a COMPLETE STRANGER - someone you have never met before and do not know from the book.
- They are NOT a character from '{character['book_title']}'.
- They are NOT someone you know from your past or from the story.
- They are a THIRD PARTY - an unknown person who is approaching you for the first time.
- You have NO prior relationship, history, or shared experiences with them.
- Unless the user explicitly tells you otherwise (e.g., "I am [character name]" or "I am your [relationship]"), you must treat them as a complete stranger.
- Do NOT assume they are any character from the book or someone you know.
"""
        
        prompt += """

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
        system_instruction: Optional[str] = None,
        conversation_partner_type: str = "stranger",
        other_main_character: Optional[Dict] = None
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
            system_instruction = self.create_persona_prompt(
                character, 
                output_language,
                conversation_partner_type,
                other_main_character
            )
        
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
        
        # 공통 API 호출 로직 사용
        try:
            response = self._call_gemini_api(
                contents=contents,
                system_instruction=system_instruction,
                model="gemini-2.5-flash",
                temperature=0.8,
                top_p=0.95,
                max_output_tokens=4096
            )
            
            # 응답 추출
            result = self._extract_response(response)
            
            return {
                'response': result['response'],
                'character_name': character['character_name'],
                'book_title': character['book_title'],
                'output_language': output_language,
                'grounding_metadata': result['grounding_metadata']
            }
        except ValueError as e:
            # Store 관련 에러
            return {
                'error': str(e),
                'character_name': character['character_name']
            }
        except Exception as e:
            # 기타 에러
            return {
                'error': f"응답 생성 실패: {str(e)}",
                'character_name': character['character_name']
            }
    
