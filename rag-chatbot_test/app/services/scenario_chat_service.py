"""
시나리오 기반 대화 서비스

What if 시나리오를 적용하여 캐릭터와 대화하는 서비스
"""

import json
import uuid
import threading
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.services.character_chat_service import CharacterChatService
from app.services.scenario_management_service import ScenarioManagementService


class ScenarioChatService:
    """시나리오 기반 대화 서비스"""
    
    def __init__(self):
        """시나리오 기반 대화 서비스 초기화"""
        self.scenario_service = ScenarioManagementService()
        self.character_service = CharacterChatService()
        
        # 프로젝트 루트 경로
        current_file = Path(__file__)
        self.project_root = current_file.parent.parent.parent
        
        # 임시 대화 저장 디렉토리 (파일 기반)
        self.temp_conversations_dir = self.project_root / "data" / "scenarios" / "temp_conversations"
        self.temp_conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread-safe를 위한 Lock 추가
        self._conversations_lock = threading.Lock()
        
        # TTL 설정: 1시간 후 자동 삭제
        self.conversation_ttl = timedelta(hours=1)
    
    def create_scenario_prompt(
        self,
        character: Dict,
        scenario: Dict,
        output_language: str = "ko",
        is_forked: bool = False,
        original_first_conversation: Optional[Dict] = None
    ) -> str:
        """
        시나리오가 적용된 프롬프트 생성
        
        Args:
            character: 캐릭터 정보
            scenario: 시나리오 정보
            output_language: 출력 언어
            is_forked: Fork된 시나리오인지 여부
        
        Returns:
            시나리오 적용 프롬프트
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

【Original Persona】
{character.get('persona', '')}

【Original Speaking Style】
{character.get('speaking_style', '')}

【Scenario Context - IMPORTANT】
This conversation takes place in an ALTERNATE TIMELINE where certain changes have occurred.
"""
        
        if is_forked:
            prompt += """
【Note】
This scenario was created by another user and you are experiencing it through a fork.
Maintain the scenario's alternate timeline while having your own unique conversation.
"""
            
            # 원본 생성자의 첫 대화 참조 (말투, 스타일, 인명 표기 등 일관성 유지)
            if original_first_conversation and original_first_conversation.get("messages"):
                prompt += """
【Reference: Original Creator's First Conversation】
The original creator of this scenario had the following conversation. Use this as a reference for:
- Speaking style and tone consistency
- Character name translations (e.g., "Irene Adler" → "아이린 애들러", NOT "이레네")
- How the character expresses themselves in this alternate timeline
- The overall atmosphere and mood

Original conversation:
"""
                # 원본 first_conversation의 모든 메시지 포함 (최대 5턴 = 10개 메시지)
                for msg in original_first_conversation["messages"][:10]:
                    role = "User" if msg.get("role") == "user" else "Character"
                    prompt += f"{role}: {msg.get('content', '')}\n"
                
                prompt += """
IMPORTANT: Maintain the same speaking style, tone, and name usage as shown in the original conversation above.
For example, if the original used "아이린", you must also use "아이린" (not "이레네" or other variations).
"""
        
        # Character Property Changes 적용
        if scenario.get('character_property_changes', {}).get('enabled'):
            prompt += """
【Character Property Changes】
The following properties of your character have been altered:
"""
            for change in scenario['character_property_changes'].get('changes', []):
                prompt += f"""
- {change.get('property_type', 'unknown')}: Changed from "{change.get('original_value', '')}" to "{change.get('altered_value', '')}"
  Description: {change.get('description', '')}
"""
            prompt += """
You must act according to these altered properties while maintaining the core essence of your character.
"""
        
        # Event Alterations 적용
        if scenario.get('event_alterations', {}).get('enabled'):
            prompt += """
【Event Alterations】
The following events in the original story have been altered:
"""
            for alteration in scenario['event_alterations'].get('alterations', []):
                prompt += f"""
- Event: {alteration.get('event_description', '')}
  Type: {alteration.get('alteration_type', '')}
  Original: {alteration.get('original_outcome', '')}
  Altered: {alteration.get('altered_outcome', '')}
  Reason: {alteration.get('reason', '')}
"""
            prompt += """
You must respond as if these events occurred differently or did not occur at all.
"""
        
        # Setting Modifications 적용
        if scenario.get('setting_modifications', {}).get('enabled'):
            prompt += """
【Setting Modifications】
The story's setting has been modified:
"""
            for mod in scenario['setting_modifications'].get('modifications', []):
                prompt += f"""
- {mod.get('modification_type', 'unknown')}: Changed from "{mod.get('original_value', '')}" to "{mod.get('altered_value', '')}"
  Description: {mod.get('description', '')}
"""
            prompt += """
You must adapt your responses to this new setting while maintaining your character's core personality.
"""
        
        prompt += f"""
【Output Language】
{language_instruction}

【Conversation Rules】
1. Always respond from {character['character_name']}'s perspective in this ALTERNATE TIMELINE.

2. REQUIRED: Use File Search to understand the original story context, then apply the scenario changes.

3. Maintain character consistency within the altered scenario.

4. Reference original book content but adapt it to the new timeline/setting.

5. Be aware of how the changes affect your relationships, experiences, and worldview.
"""
        
        return prompt
    
    def first_conversation(
        self,
        scenario_id: str,
        initial_message: str,
        output_language: str = "ko",
        is_creator: bool = True,
        conversation_id: Optional[str] = None,
        original_first_conversation: Optional[Dict] = None
    ) -> Dict:
        """
        첫 대화 시작 (5턴 제한)
        
        Args:
            scenario_id: 시나리오 ID
            initial_message: 첫 메시지
            output_language: 출력 언어
            is_creator: 원본 생성자인지 여부
            conversation_id: 기존 대화 ID (계속하기용)
        
        Returns:
            대화 응답
        """
        # 시나리오 로드
        scenario = self.scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"시나리오를 찾을 수 없습니다: {scenario_id}")
        
        # 캐릭터 정보 로드
        character = self.character_service.get_character_info(
            scenario["character_name"],
            scenario["book_title"]
        )
        if not character:
            raise ValueError(f"캐릭터를 찾을 수 없습니다: {scenario['character_name']}")
        
        # 시나리오 적용 프롬프트 생성
        # is_creator가 False면 Fork된 시나리오이므로 원본 first_conversation 참조
        # original_first_conversation이 전달되지 않은 경우에만 forked_scenario에서 가져오기 시도
        if not is_creator and not original_first_conversation:
            # Fork된 시나리오인 경우, 원본 시나리오의 first_conversation을 직접 가져오기
            # (fork_scenario 엔드포인트에서 이미 전달하므로 이 부분은 fallback)
            original_first_conversation = scenario.get("first_conversation")
        
        system_instruction = self.create_scenario_prompt(
            character,
            scenario,
            output_language,
            is_forked=not is_creator,
            original_first_conversation=original_first_conversation
        )
        
        # 오래된 임시 대화 정리 (TTL 체크)
        self._cleanup_expired_conversations()
        
        # 임시 대화 ID 생성 또는 기존 ID 사용 (Thread-safe)
        with self._conversations_lock:
            if conversation_id:
                # 파일에서 임시 대화 로드
                temp_conv_file = self.temp_conversations_dir / f"{conversation_id}.json"
                if not temp_conv_file.exists():
                    raise ValueError(f"임시 대화를 찾을 수 없습니다: {conversation_id}")
                
                with open(temp_conv_file, 'r', encoding='utf-8') as f:
                    temp_conv = json.load(f)
                
                # TTL 체크
                created_at = datetime.fromisoformat(temp_conv.get("created_at", datetime.utcnow().isoformat()).replace('Z', '+00:00'))
                if datetime.utcnow() - created_at.replace(tzinfo=None) > self.conversation_ttl:
                    temp_conv_file.unlink()  # 파일 삭제
                    raise ValueError(f"임시 대화가 만료되었습니다: {conversation_id}")
                
                messages = temp_conv.get("messages", [])
                turn_count = temp_conv.get("turn_count", 0)
            else:
                conversation_id = str(uuid.uuid4())
                messages = []
                turn_count = 0
        
        # 대화 진행
        conversation_history = []
        for msg in messages[-10:]:  # 최근 10개 메시지만 사용
            # Gemini API는 "model" role을 요구하므로 변환
            role = msg["role"]
            if role == "assistant":
                role = "model"
            elif role not in ["user", "model"]:
                continue  # 잘못된 role은 건너뛰기
            
            conversation_history.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        # 사용자 메시지 추가
        conversation_history.append({
            "role": "user",
            "parts": [{"text": initial_message}]
        })
        
        # Gemini API 호출
        result = self.character_service.chat(
            character_name=scenario["character_name"],
            user_message=initial_message,
            conversation_history=conversation_history[:-1] if len(conversation_history) > 1 else [],  # 마지막 메시지 제외 (이미 추가됨)
            book_title=scenario["book_title"],
            output_language=output_language,
            system_instruction=system_instruction
        )
        
        # 에러 체크
        if "error" in result:
            raise ValueError(f"대화 생성 실패: {result['error']}")
        
        if "response" not in result:
            raise ValueError(f"대화 생성 실패: 응답 형식이 올바르지 않습니다. {result}")
        
        # 응답 메시지 추가 (grounding_metadata 제외)
        messages.append({
            "role": "user",
            "content": initial_message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "turn": turn_count + 1
        })
        messages.append({
            "role": "assistant",
            "content": result["response"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "turn": turn_count + 1
        })
        
        turn_count += 1
        
        # 임시 저장 (파일 기반, Thread-safe)
        temp_conv_data = {
            "scenario_id": scenario_id,
            "messages": messages,
            "turn_count": turn_count,
            "is_creator": is_creator,
            "created_at": datetime.utcnow().isoformat() + "Z"  # TTL 관리를 위한 생성 시간
        }
        
        with self._conversations_lock:
            temp_conv_file = self.temp_conversations_dir / f"{conversation_id}.json"
            with open(temp_conv_file, 'w', encoding='utf-8') as f:
                json.dump(temp_conv_data, f, ensure_ascii=False, indent=2)
        
        return {
            "conversation_id": conversation_id,
            "scenario_id": scenario_id,
            "response": result["response"],
            "grounding_metadata": result.get("grounding_metadata"),
            "turn_count": turn_count,
            "max_turns": 5,
            "is_temporary": True,
            "is_creator": is_creator  # Fork 여부 확인용
        }
    
    def confirm_first_conversation(
        self,
        scenario_id: str,
        conversation_id: str,
        action: str  # "save" or "cancel"
    ) -> Dict:
        """
        첫 대화 최종 컨펌 (5턴 완료 후)
        
        Args:
            scenario_id: 시나리오 ID
            conversation_id: 임시 대화 ID
            action: "save" 또는 "cancel"
        
        Returns:
            컨펌 결과
        """
        # 파일에서 임시 대화 로드 (Thread-safe)
        temp_conv_file = self.temp_conversations_dir / f"{conversation_id}.json"
        with self._conversations_lock:
            if not temp_conv_file.exists():
                raise ValueError(f"임시 대화를 찾을 수 없습니다: {conversation_id}")
            
            with open(temp_conv_file, 'r', encoding='utf-8') as f:
                temp_conv = json.load(f)
        
        if action == "save":
            # 시나리오 로드
            scenario = self.scenario_service.get_scenario(scenario_id)
            if not scenario:
                raise ValueError(f"시나리오를 찾을 수 없습니다: {scenario_id}")
            
            # first_conversation 업데이트
            scenario["first_conversation"] = {
                "conversation_id": conversation_id,
                "is_complete": True,
                "turn_count": temp_conv["turn_count"],
                "messages": temp_conv["messages"],
                "created_at": temp_conv["messages"][0]["timestamp"] if temp_conv["messages"] else datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
            
            # 시나리오 업데이트
            self.scenario_service.update_scenario(scenario)
            
            # 임시 대화 파일 삭제 (Thread-safe)
            with self._conversations_lock:
                if temp_conv_file.exists():
                    temp_conv_file.unlink()
            
            return {
                "scenario_id": scenario_id,
                "status": "saved",
                "first_conversation": scenario["first_conversation"],
                "message": "첫 대화가 시나리오에 저장되었습니다."
            }
        else:  # cancel
            # 임시 대화 파일 삭제 (Thread-safe)
            with self._conversations_lock:
                if temp_conv_file.exists():
                    temp_conv_file.unlink()
            
            return {
                "scenario_id": scenario_id,
                "status": "cancelled",
                "message": "대화가 취소되었습니다. 다시 시작할 수 있습니다."
            }
    
    def chat_with_scenario(
        self,
        scenario_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        output_language: str = "ko",
        is_forked: bool = False,
        forked_scenario_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        시나리오 기반 대화
        
        Args:
            scenario_id: 시나리오 ID (Fork된 경우 원본 시나리오 ID)
            user_message: 사용자 메시지
            conversation_history: 대화 기록
            output_language: 출력 언어
            is_forked: Fork된 시나리오인지 여부
            forked_scenario_id: Fork된 시나리오 ID (Fork된 경우)
            conversation_id: 기존 대화 ID
            user_id: 사용자 ID (대화 저장용)
        
        Returns:
            대화 응답
        """
        # 시나리오 로드
        original_scenario = None
        if is_forked and forked_scenario_id:
            # Fork된 시나리오 로드
            file_path = self.project_root / "data" / "scenarios" / "forked" / user_id / f"{forked_scenario_id}.json"
            if not file_path.exists():
                raise ValueError(f"Fork된 시나리오를 찾을 수 없습니다: {forked_scenario_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                forked_scenario = json.load(f)
            
            # 원본 시나리오 로드 (first_conversation 참조용)
            original_scenario_id = forked_scenario.get("original_scenario_id")
            original_scenario = self.scenario_service.get_scenario(original_scenario_id)
            if not original_scenario:
                raise ValueError(f"원본 시나리오를 찾을 수 없습니다: {original_scenario_id}")
            
            scenario = {
                "scenario_id": original_scenario_id,
                "character_name": forked_scenario["character_name"],
                "book_title": forked_scenario["book_title"],
                "character_property_changes": forked_scenario["character_property_changes"],
                "event_alterations": forked_scenario["event_alterations"],
                "setting_modifications": forked_scenario["setting_modifications"]
            }
        else:
            scenario = self.scenario_service.get_scenario(scenario_id)
            if not scenario:
                raise ValueError(f"시나리오를 찾을 수 없습니다: {scenario_id}")
            original_scenario = scenario
        
        # 캐릭터 정보 로드
        character = self.character_service.get_character_info(
            scenario["character_name"],
            scenario["book_title"]
        )
        if not character:
            raise ValueError(f"캐릭터를 찾을 수 없습니다: {scenario['character_name']}")
        
        # 시나리오 적용 프롬프트 생성 (원본 first_conversation 참조 포함)
        system_instruction = self.create_scenario_prompt(
            character,
            scenario,
            output_language,
            is_forked=is_forked,
            original_first_conversation=original_scenario.get("first_conversation") if original_scenario else None
        )
        
        # 대화 진행
        result = self.character_service.chat(
            character_name=scenario["character_name"],
            user_message=user_message,
            conversation_history=conversation_history,
            book_title=scenario["book_title"],
            output_language=output_language,
            system_instruction=system_instruction
        )
        
        # 에러 체크
        if "error" in result:
            raise ValueError(f"대화 생성 실패: {result['error']}")
        
        if "response" not in result:
            raise ValueError(f"대화 생성 실패: 응답 형식이 올바르지 않습니다. {result}")
        
        # Fork된 시나리오의 경우 대화 저장
        if is_forked and forked_scenario_id and user_id:
            # 대화 ID 생성 또는 기존 ID 사용
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Fork된 시나리오 파일 다시 로드
            with open(file_path, 'r', encoding='utf-8') as f:
                forked_scenario = json.load(f)
            
            # 대화 찾기 또는 생성
            conversation = None
            for conv in forked_scenario.get("conversations", []):
                if conv.get("conversation_id") == conversation_id:
                    conversation = conv
                    break
            
            if not conversation:
                conversation = {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "started_at": datetime.utcnow().isoformat() + "Z",
                    "messages": []
                }
                forked_scenario.setdefault("conversations", []).append(conversation)
            
            # 메시지 추가 (grounding_metadata 제외)
            conversation["messages"].append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            conversation["messages"].append({
                "role": "assistant",
                "content": result["response"],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            # 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(forked_scenario, f, ensure_ascii=False, indent=2)
        
        return {
            "response": result["response"],
            "conversation_id": conversation_id,
            "scenario_id": scenario_id if not is_forked else forked_scenario_id,
            "character_name": scenario["character_name"],
            "book_title": scenario["book_title"],
            "output_language": output_language,
            "grounding_metadata": result.get("grounding_metadata"),
            "is_forked": is_forked,
            "is_saved": is_forked  # Fork된 시나리오는 저장됨
        }
    
    def _cleanup_expired_conversations(self):
        """
        만료된 임시 대화 파일 정리 (TTL 체크)
        Thread-safe하게 실행됨
        """
        now = datetime.utcnow()
        expired_files = []
        
        with self._conversations_lock:
            # 모든 임시 대화 파일 확인
            for conv_file in self.temp_conversations_dir.glob("*.json"):
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                    
                    created_at_str = conv_data.get("created_at", "")
                    if created_at_str:
                        # ISO 형식 파싱 (Z 제거 후 UTC로 처리)
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        created_at_utc = created_at.replace(tzinfo=None)
                        
                        if now - created_at_utc > self.conversation_ttl:
                            expired_files.append(conv_file)
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    # 잘못된 파일은 삭제
                    expired_files.append(conv_file)
            
            # 만료된 파일 삭제
            for expired_file in expired_files:
                try:
                    expired_file.unlink()
                except Exception:
                    pass  # 삭제 실패해도 계속 진행
    
    def confirm_forked_conversation(
        self,
        forked_scenario_id: str,
        conversation_id: str,
        action: str,  # "save" or "cancel"
        user_id: str
    ) -> Dict:
        """
        Fork된 시나리오 대화 최종 컨펌 (5턴 완료 후)
        
        Args:
            forked_scenario_id: Fork된 시나리오 ID
            conversation_id: 임시 대화 ID
            action: "save" 또는 "cancel"
            user_id: 사용자 ID
        
        Returns:
            컨펌 결과
        """
        # 파일에서 임시 대화 로드 (Thread-safe)
        temp_conv_file = self.temp_conversations_dir / f"{conversation_id}.json"
        with self._conversations_lock:
            if not temp_conv_file.exists():
                raise ValueError(f"임시 대화를 찾을 수 없습니다: {conversation_id}")
            
            with open(temp_conv_file, 'r', encoding='utf-8') as f:
                temp_conv = json.load(f)
        
        if action == "save":
            # Fork된 시나리오 파일 로드
            forked_scenario_file = self.project_root / "data" / "scenarios" / "forked" / user_id / f"{forked_scenario_id}.json"
            if not forked_scenario_file.exists():
                raise ValueError(f"Fork된 시나리오를 찾을 수 없습니다: {forked_scenario_id}")
            
            with open(forked_scenario_file, 'r', encoding='utf-8') as f:
                forked_scenario = json.load(f)
            
            # 대화를 conversations 배열에 추가
            conversation = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "turn_count": temp_conv["turn_count"],
                "messages": temp_conv["messages"],
                "started_at": temp_conv["messages"][0]["timestamp"] if temp_conv["messages"] else datetime.utcnow().isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "is_complete": True
            }
            
            # conversations 배열에 추가 (중복 체크)
            conversations = forked_scenario.get("conversations", [])
            existing_index = None
            for i, conv in enumerate(conversations):
                if conv.get("conversation_id") == conversation_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                conversations[existing_index] = conversation
            else:
                conversations.append(conversation)
            
            forked_scenario["conversations"] = conversations
            
            # Fork된 시나리오 파일 저장
            with open(forked_scenario_file, 'w', encoding='utf-8') as f:
                json.dump(forked_scenario, f, ensure_ascii=False, indent=2)
            
            # 임시 대화 파일 삭제 (Thread-safe)
            with self._conversations_lock:
                if temp_conv_file.exists():
                    temp_conv_file.unlink()
            
            return {
                "forked_scenario_id": forked_scenario_id,
                "status": "saved",
                "conversation": conversation,
                "message": "Fork된 시나리오 대화가 저장되었습니다."
            }
        else:  # cancel
            # 임시 대화 파일 삭제 (Thread-safe)
            with self._conversations_lock:
                if temp_conv_file.exists():
                    temp_conv_file.unlink()
            
            return {
                "forked_scenario_id": forked_scenario_id,
                "status": "cancelled",
                "message": "대화가 취소되었습니다. 다시 시작할 수 있습니다."
            }

