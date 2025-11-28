# -*- coding: utf-8 -*-
"""
Gradio UI for What If Scenario Chat

What If 시나리오를 생성하고 시나리오대로 캐릭터와 대화하는 인터페이스
"""

import sys
import json
import logging
from datetime import datetime
import gradio as gr
from pathlib import Path
from typing import List, Dict

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 로그 디렉토리 생성
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

# 로그 파일 설정 (날짜별로 파일 생성)
log_filename = log_dir / f"gradio_app_{datetime.now().strftime('%Y%m%d')}.log"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # 콘솔에도 출력
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 80)
logger.info("Gradio App 시작")
logger.info(f"로그 파일: {log_filename}")
logger.info("=" * 80)

# 서비스 직접 import
from app.services.character_chat_service import CharacterChatService
from app.services.scenario_management_service import ScenarioManagementService
from app.services.scenario_chat_service import ScenarioChatService
from app.services.api_key_manager import get_api_key_manager
from app.services.character_data_loader import CharacterDataLoader

# 전역 변수 (서비스 인스턴스는 공유 가능)
character_service = None
scenario_service = None
scenario_chat_service = None


def initialize_service():
    """서비스 초기화"""
    global character_service, scenario_service, scenario_chat_service
    
    logger.info("서비스 초기화 시작...")
    try:
        # API 키 매니저 초기화
        api_key_manager = get_api_key_manager()
        api_key = api_key_manager.get_current_key()
        
        # 서비스 인스턴스 생성
        character_service = CharacterChatService(api_key=api_key)
        scenario_service = ScenarioManagementService()
        scenario_chat_service = ScenarioChatService()
        
        # 캐릭터 목록 가져오기 (로깅용)
        available_characters = character_service.get_available_characters()
        
        logger.info(f"서비스 초기화 완료! (캐릭터 {len(available_characters)}개)")
        return True, f"✅ 서비스 초기화 완료! ({len(available_characters)}명의 캐릭터 로드됨)"
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {str(e)}", exc_info=True)
        return False, f"❌ 서비스 초기화 실패: {str(e)}"


def load_books_from_characters_folder() -> List[Dict]:
    """data/characters/ 폴더에서 책 목록 로드"""
    characters_dir = project_root / "data" / "characters"
    books = []
    
    if characters_dir.exists() and characters_dir.is_dir():
        json_files = list(characters_dir.glob("*.json"))
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    book_data = json.load(f)
                    books.append({
                        'book_title': book_data.get('book_title', ''),
                        'author': book_data.get('author', '')
                    })
            except Exception:
                continue
    
    # 책 제목으로 정렬
    books.sort(key=lambda x: x['book_title'])
    return books


def get_book_list():
    """책 목록 반환 (드롭다운용)"""
    books = load_books_from_characters_folder()
    if not books:
        return []
    # "책 제목 - 저자" 형식으로 표시
    return [f"{book['book_title']} - {book['author']}" for book in books]


def get_characters_by_book(book_display: str) -> List[str]:
    """선택된 책의 캐릭터 목록 반환"""
    if not book_display:
        return []
    
    # "책 제목 - 저자" 형식에서 책 제목 추출
    book_title = book_display.split(" - ")[0] if " - " in book_display else book_display
    
    characters_dir = project_root / "data" / "characters"
    if not characters_dir.exists():
        return []
    
    # 책 제목으로 파일 찾기 (대략적 매칭)
    json_files = list(characters_dir.glob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
                if book_data.get('book_title', '') == book_title:
                    characters = [char['character_name'] for char in book_data.get('characters', [])]
                    return characters
        except Exception:
            continue
    
    return []


def get_character_info(book_display: str, character_name: str):
    """캐릭터 정보 가져오기 (캐릭터 설명만 반환)"""
    if not character_service or not character_name or not book_display:
        return ""
    
    # 책 제목 추출
    book_title = book_display.split(" - ")[0] if " - " in book_display else book_display
    
    try:
        character = character_service.get_character_info(character_name, book_title)
        if character:
            # 한국어 캐릭터 설명만 반환
            persona_text = character.get('persona_ko') or character.get('persona', '')
            return persona_text
        return "캐릭터를 찾을 수 없습니다."
    except Exception as e:
        return f"오류: {str(e)}"


def create_scenario(
    scenario_name,
    book_display,
    character_name,
    character_property_desc,
    event_alteration_desc,
    setting_modification_desc,
    is_public,
    session_state
):
    """시나리오 생성"""
    logger.info(f"시나리오 생성 요청: character={character_name}, book={book_display}, scenario_name={scenario_name}")
    
    # 즉시 로딩 메시지 표시
    loading_msg = "⏳ 시나리오 생성 중... 잠시만 기다려주세요."
    
    if not scenario_service:
        logger.warning("시나리오 서비스가 초기화되지 않음")
        yield "❌ 서비스를 먼저 초기화해주세요.", "", "시나리오를 먼저 생성해주세요.", [], session_state, gr.update()
        return
    
    if not book_display or not character_name:
        yield "❌ 책과 주인공을 선택해주세요.", "", "시나리오를 먼저 생성해주세요.", [], session_state, gr.update()
        return
    
    # 로딩 메시지 즉시 표시
    yield loading_msg, "", "시나리오 생성 중...", [], session_state, gr.update()
    
    try:
        # 책 제목 추출
        book_title = book_display.split(" - ")[0] if " - " in book_display else book_display
        
        # 캐릭터 정보 가져오기
        character = character_service.get_character_info(character_name, book_title)
        if not character:
            yield f"❌ 캐릭터를 찾을 수 없습니다: {character_name} (책: {book_title})", "", "시나리오를 먼저 생성해주세요.", [], session_state, gr.update()
            return
        
        # 텍스트 입력 여부로 자동 활성화 판단
        character_property_enabled = bool(character_property_desc and character_property_desc.strip() and not character_property_desc.strip().startswith("예:"))
        event_alteration_enabled = bool(event_alteration_desc and event_alteration_desc.strip() and not event_alteration_desc.strip().startswith("예:"))
        setting_modification_enabled = bool(setting_modification_desc and setting_modification_desc.strip() and not setting_modification_desc.strip().startswith("예:"))
        
        # 변경사항이 하나도 없으면 기본 캐릭터 대화 모드
        has_any_changes = character_property_enabled or event_alteration_enabled or setting_modification_enabled
        
        # What If 시나리오 생성 시에만 시나리오 제목 필수
        if has_any_changes and not scenario_name:
            yield "❌ What If 시나리오를 생성하려면 시나리오 제목을 입력해주세요.", "", "시나리오를 먼저 생성해주세요.", [], session_state, gr.update()
            return
        
        if not has_any_changes:
            # 기본 캐릭터 대화 모드 설정
            session_state['is_basic_character_chat'] = True
            session_state['book_title'] = book_title
            session_state['character_name'] = character_name
            session_state['scenario_id'] = None
            session_state['conversation_id'] = None
            session_state['turn_count'] = 0
            
            # 다른 주인공 정보 미리 가져오기
            characters = CharacterDataLoader.load_characters()
            other_main_character = CharacterDataLoader.get_other_main_character(
                characters, character_name, book_title
            )
            session_state['other_main_character_name'] = other_main_character.get('character_name') if other_main_character else None
            
            scenario_info = f"""
**원본 캐릭터 대화 모드**

**캐릭터**: {character_name}
**책**: {book_title}

변경사항이 없어 원본 캐릭터와 대화합니다.

👉 **시나리오 대화 탭을 눌러 대화를 시작하세요!**
"""
            # 다른 주인공 이름으로 라디오 버튼 업데이트
            other_name = session_state.get('other_main_character_name', '')
            if other_name:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                    (f"{other_name} (책 속 인물)", "other_main_character")
                ]
            else:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                ]
            
            yield scenario_info, "", "원본 캐릭터 대화 모드", [], session_state, gr.update(choices=radio_choices, value="stranger", interactive=True)
            return
        
        # 시나리오 설명 구성
        descriptions = {
            "character_property_changes": {
                "enabled": character_property_enabled,
                "description": character_property_desc.strip() if character_property_enabled else ""
            },
            "event_alterations": {
                "enabled": event_alteration_enabled,
                "description": event_alteration_desc.strip() if event_alteration_enabled else ""
            },
            "setting_modifications": {
                "enabled": setting_modification_enabled,
                "description": setting_modification_desc.strip() if setting_modification_enabled else ""
            }
        }
        
        # 시나리오 생성
        result = scenario_service.create_scenario(
            scenario_name=scenario_name,
            book_title=book_title,
            character_name=character_name,
            descriptions=descriptions,
            creator_id="gradio_user",
            is_public=is_public
        )
        
        # 세션별 상태 업데이트
        session_state['is_basic_character_chat'] = False
        session_state['scenario_id'] = result['scenario_id']
        session_state['conversation_id'] = None
        session_state['turn_count'] = 0
        
        # 다른 주인공 정보 미리 가져오기
        characters = CharacterDataLoader.load_characters()
        other_main_character = CharacterDataLoader.get_other_main_character(
            characters, character_name, book_title
        )
        session_state['other_main_character_name'] = other_main_character.get('character_name') if other_main_character else None
        
        scenario_info = f"""
**시나리오 생성 완료!**

**시나리오 이름**: {scenario_name}
**캐릭터**: {character_name}
**책**: {book_title}
**시나리오 ID**: {session_state['scenario_id']}

👉 **시나리오 대화 탭을 눌러 대화를 시작하세요!**
"""
        
        logger.info(f"시나리오 생성 완료: scenario_id={session_state['scenario_id']}")
        
        # 다른 주인공 이름으로 라디오 버튼 업데이트
        other_name = session_state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        
        yield scenario_info, session_state['scenario_id'], session_state['scenario_id'], [], session_state, gr.update(choices=radio_choices, value="stranger", interactive=True)
    
    except Exception as e:
        logger.error(f"시나리오 생성 실패: {str(e)}", exc_info=True)
        yield f"❌ 시나리오 생성 실패: {str(e)}", "", "시나리오를 먼저 생성해주세요.", [], session_state, gr.update()


# 대화 기록 저장 (세션별)
conversation_histories = {}

def start_first_conversation(message, scenario_id, history, session_state):
    """첫 대화 시작"""
    output_language = "ko"  # 한국어로 고정
    
    # 기본 캐릭터 대화 모드인지 확인
    if session_state.get('is_basic_character_chat'):
        # 라디오 버튼 업데이트 준비 (공통)
        other_name = session_state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        current_partner_type = session_state.get('conversation_partner_type', 'stranger')
        is_interactive = not bool(session_state.get('conversation_id'))
        
        if not character_service:
            error_msg = "❌ 서비스를 먼저 초기화해주세요."
            return history, error_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
        
        if not message.strip():
            return history, "", "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
        
        try:
            # 기본 캐릭터 대화
            book_title = session_state.get('book_title')
            character_name = session_state.get('character_name')
            conversation_partner_type = session_state.get('conversation_partner_type', 'stranger')
            
            # 다른 주인공 정보 가져오기 (필요한 경우)
            other_main_character = None
            if conversation_partner_type == "other_main_character":
                characters = CharacterDataLoader.load_characters()
                other_main_character = CharacterDataLoader.get_other_main_character(
                    characters, character_name, book_title
                )
                if not other_main_character:
                    # 다른 주인공이 없으면 제3의 인물로 변경
                    conversation_partner_type = 'stranger'
            
            # 대화 기록에 사용자 메시지 추가
            history = history + [{"role": "user", "content": message}]
            
            # 기본 모드: conversation_id 사용하여 연속 대화
            result = character_service.chat(
                character_name=character_name,
                book_title=book_title,
                user_message=message,
                output_language=output_language,
                conversation_id=session_state.get('conversation_id'),
                conversation_partner_type=conversation_partner_type,
                other_main_character=other_main_character
            )
            
            # conversation_id와 turn_count 업데이트
            if 'conversation_id' in result:
                session_state['conversation_id'] = result['conversation_id']
            if 'turn_count' in result:
                session_state['turn_count'] = result['turn_count']
            
            if 'error' in result:
                error_msg = f"❌ {result['error']}"
                # 에러 시에도 라디오 버튼 상태 유지
                other_name = session_state.get('other_main_character_name', '')
                if other_name:
                    radio_choices = [
                        ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                        (f"{other_name} (책 속 인물)", "other_main_character")
                    ]
                else:
                    radio_choices = [
                        ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                    ]
                current_partner_type = session_state.get('conversation_partner_type', 'stranger')
                is_interactive = not bool(session_state.get('conversation_id'))
                return history, error_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
            
            # 대화 기록에 추가
            history = history + [
                {"role": "assistant", "content": result['response']}
            ]
            
            # 대화가 시작되었으므로 라디오 버튼 비활성화
            other_name = session_state.get('other_main_character_name', '')
            if other_name:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                    (f"{other_name} (책 속 인물)", "other_main_character")
                ]
            else:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                ]
            current_partner_type = session_state.get('conversation_partner_type', 'stranger')
            
            status_msg = "원본 캐릭터와 대화 중"
            return history, status_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=False)
        
        except Exception as e:
            logger.error(f"대화 시작 실패: {str(e)}", exc_info=True)
            error_msg = f"❌ 대화 시작 실패: {str(e)}"
            # 에러 시에도 라디오 버튼 상태 유지
            other_name = session_state.get('other_main_character_name', '')
            if other_name:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                    (f"{other_name} (책 속 인물)", "other_main_character")
                ]
            else:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                ]
            current_partner_type = session_state.get('conversation_partner_type', 'stranger')
            is_interactive = not bool(session_state.get('conversation_id'))
            return history, error_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
    
    # What If 시나리오 대화 모드
    if not scenario_chat_service or not scenario_id:
        error_msg = "❌ 시나리오를 먼저 생성해주세요."
        return history, error_msg, "턴: 0/5", gr.update(visible=False), gr.update(visible=False), "", session_state
    
    if not message.strip():
        return history, "", "턴: 0/5", gr.update(visible=False), gr.update(visible=False), "", session_state
    
    try:
        # 대화 상대 타입 및 다른 주인공 정보 가져오기
        conversation_partner_type = session_state.get('conversation_partner_type', 'stranger')
        other_main_character = None
        
        if conversation_partner_type == "other_main_character":
            # 시나리오에서 캐릭터 정보 가져오기
            scenario = scenario_chat_service.scenario_service.get_scenario(scenario_id)
            if scenario:
                characters = CharacterDataLoader.load_characters()
                other_main_character = CharacterDataLoader.get_other_main_character(
                    characters, 
                    scenario.get('character_name', ''),
                    scenario.get('book_title', '')
                )
                if not other_main_character:
                    # 다른 주인공이 없으면 제3의 인물로 변경
                    conversation_partner_type = 'stranger'
        
        # 통합 엔드포인트: conversation_id가 있으면 이어가기, 없으면 첫 대화
        result = scenario_chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=message,
            output_language=output_language,
            is_creator=True,
            conversation_id=session_state.get('conversation_id'),
            reference_first_conversation=None,  # 원본 시나리오이므로 None
            conversation_partner_type=conversation_partner_type,
            other_main_character=other_main_character
        )
        
        # 세션별 상태 업데이트
        session_state['conversation_id'] = result['conversation_id']
        session_state['turn_count'] = result['turn_count']
        
        # 대화 기록에 추가 (전체 응답 표시)
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result['response']}
        ]
        
        # 세션별 기록 저장
        conversation_histories[result['conversation_id']] = history
        
        status_msg = f"턴 {session_state['turn_count']}/{result['max_turns']}"
        turn_info = f"턴: {session_state['turn_count']}/{result['max_turns']}"
        
        # 대화가 시작되었으므로 라디오 버튼 비활성화
        other_name = session_state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        current_partner_type = session_state.get('conversation_partner_type', 'stranger')
        
        # 5턴 완료 시 저장/취소 버튼 표시
        if session_state['turn_count'] >= result['max_turns']:
            return history, status_msg, turn_info, gr.update(visible=True), gr.update(visible=True), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=False)
        else:
            return history, status_msg, turn_info, gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=False)
    
    except Exception as e:
        logger.error(f"What If 시나리오 대화 시작 실패: {str(e)}", exc_info=True)
        error_msg = f"❌ 대화 시작 실패: {str(e)}"
        turn_msg = "턴: 0/5"
        # 에러 시에도 라디오 버튼 상태 유지
        other_name = session_state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        current_partner_type = session_state.get('conversation_partner_type', 'stranger')
        is_interactive = not bool(session_state.get('conversation_id'))
        return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)


def continue_conversation(message, scenario_id, conversation_id, history, session_state):
    """대화 계속"""
    output_language = "ko"  # 한국어로 고정
    
    # 기본 캐릭터 대화 모드인지 확인
    if session_state.get('is_basic_character_chat'):
        if not character_service:
            error_msg = "❌ 서비스를 먼저 초기화해주세요."
            return history, error_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state
        
        if not message.strip():
            return history, "", "", gr.update(visible=False), gr.update(visible=False), "", session_state
        
        try:
            # 기본 캐릭터 대화
            book_title = session_state.get('book_title')
            character_name = session_state.get('character_name')
            
            # 대화 기록에 사용자 메시지 추가
            history = history + [{"role": "user", "content": message}]
            
            # 대화 상대 타입 및 다른 주인공 정보 가져오기
            conversation_partner_type = session_state.get('conversation_partner_type', 'stranger')
            other_main_character = None
            
            if conversation_partner_type == "other_main_character":
                characters = CharacterDataLoader.load_characters()
                other_main_character = CharacterDataLoader.get_other_main_character(
                    characters, character_name, book_title
                )
                if not other_main_character:
                    # 다른 주인공이 없으면 제3의 인물로 변경
                    conversation_partner_type = 'stranger'
            
            # 기본 모드: conversation_id 사용하여 연속 대화
            result = character_service.chat(
                character_name=character_name,
                book_title=book_title,
                user_message=message,
                output_language=output_language,
                conversation_id=conversation_id,
                conversation_partner_type=conversation_partner_type,
                other_main_character=other_main_character
            )
            
            # conversation_id와 turn_count 업데이트
            if 'conversation_id' in result:
                session_state['conversation_id'] = result['conversation_id']
            if 'turn_count' in result:
                session_state['turn_count'] = result['turn_count']
            
            if 'error' in result:
                error_msg = f"❌ {result['error']}"
                # 에러 시에도 라디오 버튼 상태 유지
                other_name = session_state.get('other_main_character_name', '')
                if other_name:
                    radio_choices = [
                        ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                        (f"{other_name} (책 속 인물)", "other_main_character")
                    ]
                else:
                    radio_choices = [
                        ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                    ]
                current_partner_type = session_state.get('conversation_partner_type', 'stranger')
                is_interactive = not bool(session_state.get('conversation_id'))
                return history, error_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
            
            # 대화 기록에 추가
            history = history + [
                {"role": "assistant", "content": result['response']}
            ]
            
            # 대화가 시작되었으므로 라디오 버튼 비활성화
            other_name = session_state.get('other_main_character_name', '')
            if other_name:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                    (f"{other_name} (책 속 인물)", "other_main_character")
                ]
            else:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                ]
            current_partner_type = session_state.get('conversation_partner_type', 'stranger')
            
            status_msg = "원본 캐릭터와 대화 중"
            return history, status_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=False)
        
        except Exception as e:
            logger.error(f"대화 계속 실패: {str(e)}", exc_info=True)
            error_msg = f"❌ 대화 계속 실패: {str(e)}"
            # 에러 시에도 라디오 버튼 상태 유지
            other_name = session_state.get('other_main_character_name', '')
            if other_name:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                    (f"{other_name} (책 속 인물)", "other_main_character")
                ]
            else:
                radio_choices = [
                    ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
                ]
            current_partner_type = session_state.get('conversation_partner_type', 'stranger')
            is_interactive = not bool(session_state.get('conversation_id'))
            return history, error_msg, "", gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
    
    # What If 시나리오 대화 모드
    if not scenario_chat_service or not scenario_id:
        error_msg = "❌ 시나리오를 먼저 생성해주세요."
        turn_msg = "턴: 0/5"
        return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state
    
    if not message.strip():
        turn_msg = f"턴: {session_state.get('turn_count', 0)}/5"
        return history, "", turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state
    
    try:
        # 대화 상대 타입 및 다른 주인공 정보 가져오기
        conversation_partner_type = session_state.get('conversation_partner_type', 'stranger')
        other_main_character = None
        
        if conversation_partner_type == "other_main_character":
            # 시나리오에서 캐릭터 정보 가져오기
            scenario = scenario_chat_service.scenario_service.get_scenario(scenario_id)
            if scenario:
                characters = CharacterDataLoader.load_characters()
                other_main_character = CharacterDataLoader.get_other_main_character(
                    characters, 
                    scenario.get('character_name', ''),
                    scenario.get('book_title', '')
                )
                if not other_main_character:
                    # 다른 주인공이 없으면 제3의 인물로 변경
                    conversation_partner_type = 'stranger'
        
        # 통합 엔드포인트: conversation_id가 있으면 이어가기
        result = scenario_chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=message,
            output_language=output_language,
            is_creator=True,
            conversation_id=conversation_id,
            reference_first_conversation=None,  # 원본 시나리오이므로 None
            conversation_partner_type=conversation_partner_type,
            other_main_character=other_main_character
        )
        
        # 세션별 상태 업데이트
        session_state['turn_count'] = result['turn_count']
        
        # 대화 기록에 추가 (전체 응답 표시)
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result['response']}
        ]
        
        # 세션별 기록 업데이트
        conversation_histories[conversation_id] = history
        
        status_msg = f"턴 {session_state['turn_count']}/{result['max_turns']}"
        turn_info = f"턴: {session_state['turn_count']}/{result['max_turns']}"
        
        # 대화가 시작되었으므로 라디오 버튼 비활성화
        other_name = session_state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        current_partner_type = session_state.get('conversation_partner_type', 'stranger')
        
        # 5턴 완료 시 저장/취소 버튼 표시
        if session_state['turn_count'] >= result['max_turns']:
            return history, status_msg, turn_info, gr.update(visible=True), gr.update(visible=True), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=False)
        else:
            return history, status_msg, turn_info, gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=False)
    
    except Exception as e:
        logger.error(f"What If 시나리오 대화 계속 실패: {str(e)}", exc_info=True)
        error_msg = f"❌ 대화 계속 실패: {str(e)}"
        turn_msg = f"턴: {session_state.get('turn_count', 0)}/5"
        # 에러 시에도 라디오 버튼 상태 유지
        other_name = session_state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        current_partner_type = session_state.get('conversation_partner_type', 'stranger')
        is_interactive = not bool(session_state.get('conversation_id'))
        return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)


def confirm_conversation(scenario_id, conversation_id, action, session_state):
    """대화 최종 확인 (통합 엔드포인트 사용)"""
    if not scenario_chat_service or not scenario_id or not conversation_id:
        return "❌ 시나리오와 대화를 먼저 생성해주세요.", session_state
    
    try:
        # 통합 엔드포인트: action을 사용하여 저장/취소 처리
        # action="save" 또는 "cancel"로 first_conversation을 호출하면 자동으로 처리됨
        # 하지만 서비스 레이어에서는 confirm_first_conversation을 별도로 호출해야 함
        result = scenario_chat_service.confirm_first_conversation(
            scenario_id=scenario_id,
            conversation_id=conversation_id,
            action=action
        )
        
        if action == "save":
            # 대화 기록 초기화
            if conversation_id in conversation_histories:
                del conversation_histories[conversation_id]
            # 세션별 상태 초기화
            session_state['scenario_id'] = None
            session_state['conversation_id'] = None
            session_state['turn_count'] = 0
            return f"✅ 대화가 저장되었습니다!\n\n{result.get('message', '')}", session_state
        else:
            # 대화 기록 초기화
            if conversation_id in conversation_histories:
                del conversation_histories[conversation_id]
            # 대화만 초기화 (시나리오는 유지)
            session_state['conversation_id'] = None
            session_state['turn_count'] = 0
            return "❌ 대화가 취소되었습니다.", session_state
    
    except Exception as e:
        logger.error(f"대화 확인 실패: {str(e)}", exc_info=True)
        return f"❌ 확인 실패: {str(e)}", session_state


# 서비스 초기화
_, init_message = initialize_service()

# Gradio UI 구성
with gr.Blocks(title="Gaji What If Scenario Chat") as demo:
    
    gr.Markdown(
        """
        # 🔀 Gaji What If Scenario Chat
        
        **"What If?" 시나리오를 생성하고, 대체 타임라인에서 캐릭터와 대화하세요!**
        
        ## 📖 사용 방법
        
        ### 1️⃣ 시나리오 설정 (1️⃣ 시나리오 생성 탭)
        - **책 선택**: 대화하고 싶은 책을 선택하세요
        - **주인공 선택**: 해당 책의 주인공 중 한 명을 선택하세요
        - **시나리오 제목 입력** (선택사항): What If 시나리오를 생성할 때만 필요합니다
        - **What If 변경사항 입력** (선택사항):
          - **캐릭터 속성 변경**: 캐릭터의 성격, 능력, 가치관 등이 달라졌다면?
          - **사건 변경**: 원작의 중요한 사건이 일어나지 않았거나 다르게 일어났다면?
          - **배경 변경**: 이야기가 다른 시대나 장소에서 일어났다면?
        - ⚠️ **주의**: 변경사항을 아무것도 입력하지 않으면 원본 캐릭터와 대화하게 됩니다
        
        ### 2️⃣ 시나리오 생성
        - "✨ 시나리오 생성" 버튼을 클릭하세요
        - What If 변경사항을 입력했다면 시나리오가 생성됩니다
        - 변경사항을 입력하지 않았다면 원본 캐릭터 대화 모드로 설정됩니다
        
        ### 3️⃣ 첫 대화 시작 (2️⃣ 시나리오 대화 탭)
        - 시나리오 생성 후 "2️⃣ 시나리오 대화" 탭으로 이동하세요
        - 대화창에 메시지를 입력하고 전송하거나 엔터 키를 누르세요
        - 시나리오에 맞는 캐릭터가 응답합니다
        - **최대 5턴**까지 대화할 수 있습니다
        
        ### 4️⃣ 대화 저장 또는 취소
        - 5턴 대화가 완료되면 "💾 대화 저장" 또는 "❌ 대화 취소" 버튼이 나타납니다
        - **대화 저장**: 만족스러운 대화라면 저장하여 시나리오에 첫 대화로 기록합니다
        - **대화 취소**: 만족스럽지 않다면 취소하고 다시 시작할 수 있습니다
        """
    )
    
    # 상태 표시
    status_text = gr.Textbox(
        value=init_message,
        label="서비스 상태",
        interactive=False,
        visible=True
    )
    
    with gr.Tabs():
        # 탭 1: 시나리오 생성
        with gr.Tab("1️⃣ 시나리오 생성"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 캐릭터 선택")
                    
                    book_dropdown = gr.Dropdown(
                        choices=get_book_list(),
                        label="📚 책 선택",
                        value=get_book_list()[0] if get_book_list() else None,
                        interactive=True
                    )
                    
                    # 초기 책 선택 시 캐릭터 목록 설정
                    initial_book = get_book_list()[0] if get_book_list() else None
                    initial_characters = get_characters_by_book(initial_book) if initial_book else []
                    initial_character = initial_characters[0] if initial_characters else None
                    initial_character_info = get_character_info(initial_book, initial_character) if initial_book and initial_character else "책과 주인공을 선택해주세요."
                    
                    character_dropdown = gr.Dropdown(
                        choices=initial_characters,
                        label="🎭 주인공 선택",
                        value=initial_character,
                        interactive=True
                    )
                    
                    character_info = gr.Textbox(
                        value=initial_character_info,
                        label="캐릭터 정보",
                        lines=29,
                        max_lines=29,
                        interactive=False
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 시나리오 제목")
                    
                    scenario_name = gr.Textbox(
                        label="시나리오 제목을 입력하세요!(제목은 what if 설정에 반영되지 않습니다.)",
                        interactive=True,
                        lines=2
                    )
                    
                    is_public = gr.Checkbox(
                        label="공개 시나리오",
                        value=False,
                        info="다른 사용자들이 볼 수 있게 공개"
                    )
                
                    gr.Markdown("### 🔀 What If 변경사항")
                    
                    gr.Markdown("#### 1. 캐릭터 속성 변경")
                    character_property_desc = gr.Textbox(
                        label="예: 빅터 프랑켄슈타인이 광적인 과학 열정 대신, 타인의 고통에 공감하는 깊은 연민을 가졌다면?",
                        lines=3,
                        interactive=True
                    )
                    
                    gr.Markdown("#### 2. 사건 변경")
                    event_alteration_desc = gr.Textbox(
                        label="예: 빅터가 피조물을 창조한 직후 도망치는 대신, 피조물에게 언어와 지식을 가르치고 사회에 적응시키려 했다면?",
                        lines=3,
                        interactive=True
                    )
                    
                    gr.Markdown("#### 3. 배경 변경")
                    setting_modification_desc = gr.Textbox(
                        label="예: 18세기 제네바/잉골슈타트가 아닌, 2040년 서울의 첨단 생명공학 연구소에서 빅터가 인공 생명체를 만들었다면?",
                        lines=3,
                        interactive=True
                    )
                    
                    gr.Markdown(
                        """
                        ⚠️ **주의**: 변경사항을 아무것도 입력하지 않으면 원본 캐릭터와 대화하게 됩니다.
                        """,
                        elem_classes=["warning-text"]
                        )
                    
                    create_scenario_btn = gr.Button("✨ 시나리오 생성", variant="primary", size="lg")
            
            scenario_result = gr.Markdown(label="시나리오 생성 결과")
            scenario_id_display = gr.Textbox(label="시나리오 ID", interactive=False, visible=False, value="")
        
        # 탭 2: 시나리오 대화
        with gr.Tab("2️⃣ 시나리오 대화"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 시나리오 정보")
                    
                    current_scenario_display = gr.Textbox(
                        label="현재 시나리오 ID",
                        interactive=False,
                        value="시나리오를 먼저 생성해주세요."
                    )
                    
                    # 대화 상대 선택 (동적으로 업데이트됨)
                    conversation_partner_radio = gr.Radio(
                        choices=[
                            ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                            ("다른 주인공 (책 속 인물)", "other_main_character")
                        ],
                        value="stranger",
                        label="대화 상대 선택",
                        info="대화 시작 전에만 선택 가능합니다"
                    )
                    
                    conversation_status = gr.Textbox(
                        label="대화 상태",
                        interactive=False,
                        lines=2,
                        value=""
                    )
                    
                    turn_info = gr.Textbox(
                        value="턴: 0/5",
                        label="진행 상황",
                        interactive=False
                    )
                    
                    with gr.Row():
                        save_btn = gr.Button("💾 대화 저장", variant="primary", visible=False)
                        cancel_btn = gr.Button("❌ 대화 취소", variant="stop", visible=False)
                    
                    confirm_result = gr.Markdown(label="저장 결과")
                
                with gr.Column(scale=3):
                    gr.Markdown("### 💬 대화창")
                    
                    chatbot = gr.Chatbot(
                        height=500,
                        label="대화창"
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="💬 메시지를 입력하세요",
                            placeholder="예: 안녕하세요! 이 대체 타임라인에서 당신의 인생은 어떻게 달라졌나요?",
                            scale=4,
                            lines=1,
                            max_lines=1,
                            container=False
                        )
                        submit_btn = gr.Button("전송", variant="primary", scale=1)
            
            # 예제 질문
            gr.Markdown("### 💡 예제 질문")
            with gr.Row():
                example1 = gr.Button("예제 1: 첫 인사", size="sm")
                example2 = gr.Button("예제 2: 변경사항 질문", size="sm")
                example3 = gr.Button("예제 3: 감정 질문", size="sm")
    
    # 이벤트 핸들러
    def set_example1():
        return "안녕하세요! 이 대체 타임라인에서 당신의 인생은 어떻게 달라졌나요?"
    
    def set_example2():
        return "원래 타임라인과 가장 큰 차이점은 무엇인가요?"
    
    def set_example3():
        return "이 변화가 당신의 감정과 가치관에 어떤 영향을 미쳤나요?"
    
    def on_book_selected(book_display):
        """책 선택 시 해당 책의 캐릭터 목록 업데이트"""
        if not book_display:
            return gr.update(choices=[], value=None), gr.update(value="책을 선택해주세요.")
        
        characters = get_characters_by_book(book_display)
        if characters:
            return gr.update(choices=characters, value=characters[0]), gr.update(value=get_character_info(book_display, characters[0]))
        else:
            return gr.update(choices=[], value=None), gr.update(value="이 책의 캐릭터를 찾을 수 없습니다.")
    
    def on_character_selected(book_display, character_name):
        """캐릭터 선택 시 정보 업데이트"""
        if not book_display or not character_name:
            return "책과 주인공을 선택해주세요."
        return get_character_info(book_display, character_name)
    
    # 책 선택 시 캐릭터 목록 업데이트
    book_dropdown.change(
        fn=on_book_selected,
        inputs=[book_dropdown],
        outputs=[character_dropdown, character_info]
    )
    
    # 캐릭터 선택 시 정보 업데이트
    character_dropdown.change(
        fn=on_character_selected,
        inputs=[book_dropdown, character_dropdown],
        outputs=[character_info]
    )
    
    # 세션별 상태 관리
    session_state = gr.State(value={
        'scenario_id': None,
        'conversation_id': None,
        'turn_count': 0,
        'is_basic_character_chat': False,
        'book_title': None,
        'character_name': None,
        'conversation_partner_type': 'stranger'  # 'stranger' or 'other_main_character'
    })
    
    # 시나리오 생성 (로딩 스피너 표시)
    create_scenario_btn.click(
        fn=create_scenario,
        inputs=[
            scenario_name,
            book_dropdown,
            character_dropdown,
            character_property_desc,
            event_alteration_desc,
            setting_modification_desc,
            is_public,
            session_state
        ],
        outputs=[scenario_result, scenario_id_display, current_scenario_display, chatbot, session_state, conversation_partner_radio],
        show_progress=True
    )
    
    # 메시지 전송
    def on_submit(message, history, partner_type, state):
        # 대화 상대 타입 저장
        state['conversation_partner_type'] = partner_type
        
        # 라디오 버튼 업데이트 준비 (공통)
        other_name = state.get('other_main_character_name', '')
        if other_name:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger"),
                (f"{other_name} (책 속 인물)", "other_main_character")
            ]
        else:
            radio_choices = [
                ("제3의 인물 (처음 보는 낯선 사람)", "stranger")
            ]
        current_partner_type = state.get('conversation_partner_type', 'stranger')
        is_interactive = not bool(state.get('conversation_id'))
        
        # 기본 캐릭터 대화 모드인지 확인
        if state.get('is_basic_character_chat'):
            if not message.strip():
                return history, "", "", gr.update(visible=False), gr.update(visible=False), "", state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
            # 기본 캐릭터 대화는 conversation_id가 없으므로 항상 start_first_conversation 호출
            return start_first_conversation(message, None, history, state)
        
        # What If 시나리오 대화 모드
        if not state.get('scenario_id'):
            error_msg = "❌ 시나리오를 먼저 생성해주세요."
            turn_msg = "턴: 0/5"
            return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
        
        if not message.strip():
            turn_msg = f"턴: {state.get('turn_count', 0)}/5"
            return history, "", turn_msg, gr.update(visible=False), gr.update(visible=False), "", state, gr.update(choices=radio_choices, value=current_partner_type, interactive=is_interactive)
        
        # 첫 대화인지 계속 대화인지 확인
        if not state.get('conversation_id'):
            return start_first_conversation(message, state['scenario_id'], history, state)
        else:
            return continue_conversation(message, state['scenario_id'], state['conversation_id'], history, state)
    
    msg.submit(
        fn=on_submit,
        inputs=[msg, chatbot, conversation_partner_radio, session_state],
        outputs=[chatbot, conversation_status, turn_info, save_btn, cancel_btn, msg, session_state, conversation_partner_radio]
    )
    
    submit_btn.click(
        fn=on_submit,
        inputs=[msg, chatbot, conversation_partner_radio, session_state],
        outputs=[chatbot, conversation_status, turn_info, save_btn, cancel_btn, msg, session_state, conversation_partner_radio]
    )
    
    # 대화 저장/취소
    def on_save(history, state):
        if not state.get('scenario_id') or not state.get('conversation_id'):
            return "❌ 저장할 대화가 없습니다.", [], state
        result_msg, updated_state = confirm_conversation(state['scenario_id'], state['conversation_id'], "save", state)
        return result_msg, [], updated_state
    
    def on_cancel(history, state):
        if not state.get('scenario_id') or not state.get('conversation_id'):
            return "❌ 취소할 대화가 없습니다.", [], state
        result_msg, updated_state = confirm_conversation(state['scenario_id'], state['conversation_id'], "cancel", state)
        return result_msg, [], updated_state
    
    save_btn.click(
        fn=on_save,
        inputs=[chatbot, session_state],
        outputs=[confirm_result, chatbot, session_state]
    )
    
    cancel_btn.click(
        fn=on_cancel,
        inputs=[chatbot, session_state],
        outputs=[confirm_result, chatbot, session_state]
    )
    
    # 예제 버튼
    example1.click(fn=set_example1, outputs=[msg])
    example2.click(fn=set_example2, outputs=[msg])
    example3.click(fn=set_example3, outputs=[msg])


if __name__ == "__main__":
    try:
        logger.info("Gradio 앱 실행 시작...")
        logger.info("Public 링크 생성을 시도합니다...")
        
        # public 링크 생성을 시도
        demo.launch(
            server_name="localhost",
            server_port=7860,
            share=True,
            show_error=True,
            quiet=False,
            theme=gr.themes.Soft()
        )
    except Exception as e:
        # public 링크 생성 실패 시 local URL만 사용
        logger.warning(f"⚠️ Public 링크 생성 실패: {str(e)}")
        logger.info("📍 Local URL만 사용합니다: http://localhost:7860")
        print(f"⚠️ Public 링크 생성 실패: {str(e)}")
        print("📍 Local URL만 사용합니다: http://localhost:7860")
        
        try:
            demo.launch(
                server_name="localhost",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False,
        theme=gr.themes.Soft()
    )
        except Exception as launch_error:
            logger.error(f"Gradio 앱 실행 실패: {str(launch_error)}", exc_info=True)
            raise
