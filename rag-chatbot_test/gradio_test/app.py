# -*- coding: utf-8 -*-
"""
Gradio UI for What If Scenario Chat

What If 시나리오를 생성하고 시나리오대로 캐릭터와 대화하는 인터페이스
"""

import os
import sys
import json
import gradio as gr
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 서비스 직접 import
from app.services.character_chat_service import CharacterChatService
from app.services.scenario_management_service import ScenarioManagementService
from app.services.scenario_chat_service import ScenarioChatService
from app.services.api_key_manager import get_api_key_manager

# 전역 변수 (서비스 인스턴스는 공유 가능)
character_service = None
scenario_service = None
scenario_chat_service = None
available_characters = []

# 세션별 상태는 gr.State로 관리 (전역 변수 제거)
# current_scenario_id, current_conversation_id, current_turn_count는 gr.State로 이동


def initialize_service():
    """서비스 초기화"""
    global character_service, scenario_service, scenario_chat_service, available_characters
    
    try:
        # API 키 매니저 초기화
        api_key_manager = get_api_key_manager()
        api_key = api_key_manager.get_current_key()
        
        # 서비스 인스턴스 생성
        character_service = CharacterChatService(api_key=api_key)
        scenario_service = ScenarioManagementService()
        scenario_chat_service = ScenarioChatService()
        
        # 캐릭터 목록 가져오기
        available_characters = character_service.get_available_characters()
        
        return True, f"✅ 서비스 초기화 완료! ({len(available_characters)}명의 캐릭터 로드됨)"
    except Exception as e:
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
                        'author': book_data.get('author', ''),
                        'filepath': str(json_file)
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


def get_character_info(book_display: str, character_name: str, language: str = "ko"):
    """캐릭터 정보 가져오기"""
    if not character_service or not character_name or not book_display:
        return ""
    
    # 책 제목 추출
    book_title = book_display.split(" - ")[0] if " - " in book_display else book_display
    
    try:
        character = character_service.get_character_info(character_name, book_title)
        if character:
            # 언어에 맞는 라벨 선택
            if language == "ko":
                persona_label = "캐릭터 설명"
                persona_text = character.get('persona_ko') or character.get('persona', '')
            else:
                persona_label = "Character Description"
                persona_text = character.get('persona_en') or character.get('persona', '')
            
            info = f"""**캐릭터 / Character**: {character['character_name']}
**책 / Book**: {character['book_title']}
**저자 / Author**: {character['author']}

**{persona_label}**:
{persona_text}
"""
            return info
        return "캐릭터를 찾을 수 없습니다." if language == "ko" else "Character not found."
    except Exception as e:
        return f"오류: {str(e)}" if language == "ko" else f"Error: {str(e)}"


def create_scenario(
    scenario_name,
    book_display,
    character_name,
    character_property_desc,
    event_alteration_desc,
    setting_modification_desc,
    is_public,
    session_state  # gr.State로 세션별 상태 전달
):
    """시나리오 생성"""
    if not scenario_service:
        return "❌ 서비스를 먼저 초기화해주세요.", "", "시나리오를 먼저 생성해주세요.", [], session_state
    
    if not scenario_name or not book_display or not character_name:
        return "❌ 시나리오 이름, 책, 주인공을 모두 선택해주세요.", "", "시나리오를 먼저 생성해주세요.", [], session_state
    
    try:
        # 책 제목 추출
        book_title = book_display.split(" - ")[0] if " - " in book_display else book_display
        
        # 캐릭터 정보 가져오기
        character = character_service.get_character_info(character_name, book_title)
        if not character:
            return f"❌ 캐릭터를 찾을 수 없습니다: {character_name} (책: {book_title})", "", "시나리오를 먼저 생성해주세요.", [], session_state
        
        # 텍스트 입력 여부로 자동 활성화 판단
        character_property_enabled = bool(character_property_desc and character_property_desc.strip())
        event_alteration_enabled = bool(event_alteration_desc and event_alteration_desc.strip())
        setting_modification_enabled = bool(setting_modification_desc and setting_modification_desc.strip())
        
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
        session_state['scenario_id'] = result['scenario_id']
        session_state['conversation_id'] = None
        session_state['turn_count'] = 0
        
        scenario_info = f"""
**시나리오 생성 완료!**

**시나리오 이름**: {scenario_name}
**캐릭터**: {character_name}
**책**: {book_title}
**시나리오 ID**: {session_state['scenario_id']}

이제 첫 대화를 시작하세요!
"""
        
        return scenario_info, session_state['scenario_id'], session_state['scenario_id'], [], session_state
    
    except Exception as e:
        return f"❌ 시나리오 생성 실패: {str(e)}", "", "시나리오를 먼저 생성해주세요.", [], session_state


# 대화 기록 저장 (세션별)
conversation_histories = {}

def start_first_conversation(message, scenario_id, history, output_language, session_state):
    """첫 대화 시작"""
    if not scenario_chat_service or not scenario_id:
        error_msg = "❌ 시나리오를 먼저 생성해주세요." if output_language == "ko" else "❌ Please create a scenario first."
        return history, error_msg, "턴: 0/5" if output_language == "ko" else "Turn: 0/5", gr.update(visible=False), gr.update(visible=False), "", session_state
    
    if not message.strip():
        return history, "", "턴: 0/5" if output_language == "ko" else "Turn: 0/5", gr.update(visible=False), gr.update(visible=False), "", session_state
    
    try:
        result = scenario_chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=message,
            output_language=output_language,
            is_creator=True,
            conversation_id=session_state.get('conversation_id')
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
        
        if output_language == "ko":
            status_msg = f"턴 {session_state['turn_count']}/{result['max_turns']}"
            turn_info = f"턴: {session_state['turn_count']}/{result['max_turns']}"
        else:
            status_msg = f"Turn {session_state['turn_count']}/{result['max_turns']}"
            turn_info = f"Turn: {session_state['turn_count']}/{result['max_turns']}"
        
        # 5턴 완료 시 저장/취소 버튼 표시
        if session_state['turn_count'] >= result['max_turns']:
            return history, status_msg, turn_info, gr.update(visible=True), gr.update(visible=True), "", session_state
        else:
            return history, status_msg, turn_info, gr.update(visible=False), gr.update(visible=False), "", session_state
    
    except Exception as e:
        error_msg = f"❌ 대화 시작 실패: {str(e)}" if output_language == "ko" else f"❌ Failed to start conversation: {str(e)}"
        turn_msg = "턴: 0/5" if output_language == "ko" else "Turn: 0/5"
        return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state


def continue_conversation(message, scenario_id, conversation_id, history, output_language, session_state):
    """대화 계속"""
    if not scenario_chat_service or not scenario_id:
        error_msg = "❌ 시나리오를 먼저 생성해주세요." if output_language == "ko" else "❌ Please create a scenario first."
        turn_msg = "턴: 0/5" if output_language == "ko" else "Turn: 0/5"
        return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state
    
    if not message.strip():
        turn_msg = f"턴: {session_state.get('turn_count', 0)}/5" if output_language == "ko" else f"Turn: {session_state.get('turn_count', 0)}/5"
        return history, "", turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state
    
    try:
        result = scenario_chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=message,
            output_language=output_language,
            is_creator=True,
            conversation_id=conversation_id
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
        
        if output_language == "ko":
            status_msg = f"턴 {session_state['turn_count']}/{result['max_turns']}"
            turn_info = f"턴: {session_state['turn_count']}/{result['max_turns']}"
        else:
            status_msg = f"Turn {session_state['turn_count']}/{result['max_turns']}"
            turn_info = f"Turn: {session_state['turn_count']}/{result['max_turns']}"
        
        # 5턴 완료 시 저장/취소 버튼 표시
        if session_state['turn_count'] >= result['max_turns']:
            return history, status_msg, turn_info, gr.update(visible=True), gr.update(visible=True), "", session_state
        else:
            return history, status_msg, turn_info, gr.update(visible=False), gr.update(visible=False), "", session_state
    
    except Exception as e:
        error_msg = f"❌ 대화 계속 실패: {str(e)}" if output_language == "ko" else f"❌ Failed to continue conversation: {str(e)}"
        turn_msg = f"턴: {session_state.get('turn_count', 0)}/5" if output_language == "ko" else f"Turn: {session_state.get('turn_count', 0)}/5"
        return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", session_state


def confirm_conversation(scenario_id, conversation_id, action, session_state):
    """대화 최종 확인"""
    if not scenario_chat_service or not scenario_id or not conversation_id:
        return "❌ 시나리오와 대화를 먼저 생성해주세요.", session_state
    
    try:
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
        return f"❌ 확인 실패: {str(e)}", session_state


# 서비스 초기화
init_success, init_message = initialize_service()

# Gradio UI 구성
# Gradio 6.0에서는 theme를 launch()에서 설정
with gr.Blocks(title="Gaji What If Scenario Chat") as demo:
    gr.Markdown(
        """
        # 🔀 Gaji What If Scenario Chat
        
        **"What If?" 시나리오를 생성하고, 대체 타임라인에서 캐릭터와 대화하세요!**
        
        **사용 방법:**
        1. 시나리오 설정: 캐릭터 선택 및 변경사항 설명
        2. 시나리오 생성: "What If" 시나리오 생성
        3. 첫 대화 시작: 시나리오에 맞는 캐릭터와 대화 (최대 5턴)
        4. 대화 저장: 만족스러우면 저장, 아니면 취소
        """
    )
    
    # 언어 선택 (상단)
    with gr.Row():
        language_radio = gr.Radio(
            choices=[("한국어", "ko"), ("English", "en")],
            value="ko",
            label="🌐 언어 선택 / Language Selection",
            interactive=True
        )
    
    # 상태 표시
    status_text = gr.Textbox(
        value=init_message,
        label="서비스 상태",
        interactive=False,
        visible=True
    )
    
    with gr.Tabs() as tabs:
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
                    initial_character_info = get_character_info(initial_book, initial_character, "ko") if initial_book and initial_character else "책과 주인공을 선택해주세요."
                    
                    character_dropdown = gr.Dropdown(
                        choices=initial_characters,
                        label="🎭 주인공 선택",
                        value=initial_character,
                        interactive=True
                    )
                    
                    character_info = gr.Textbox(
                        value=initial_character_info,
                        label="캐릭터 정보",
                        lines=15,
                        max_lines=20,
                        interactive=False
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 📝 시나리오 설정")
                    
                    scenario_name = gr.Textbox(
                        label="시나리오 이름",
                        placeholder="예: 헤르미온이가 슬리데린에 배정되었다면?",
                        interactive=True
                    )
                    
                    is_public = gr.Checkbox(
                        label="공개 시나리오",
                        value=False,
                        info="다른 사용자들이 볼 수 있게 공개"
                    )
                    
                    gr.Markdown("### 🔀 What If 변경사항")
                    
                    with gr.Accordion("1. 캐릭터 속성 변경", open=True):
                        character_property_desc = gr.Textbox(
                            label="변경 설명",
                            placeholder="예: 헤르미온이가 그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해졌다면?",
                            lines=3,
                            interactive=True
                        )
                    
                    with gr.Accordion("2. 사건 변경", open=True):
                        event_alteration_desc = gr.Textbox(
                            label="변경 설명",
                            placeholder="예: 게츠비가 데이지를 만나지 않았다면?",
                            lines=3,
                            interactive=True
                        )
                    
                    with gr.Accordion("3. 배경 변경", open=True):
                        setting_modification_desc = gr.Textbox(
                            label="변경 설명",
                            placeholder="예: 오만과 편견이 2024년 서울에서 일어났다면?",
                            lines=3,
                            interactive=True
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
                    
                    conversation_status = gr.Textbox(
                        label="대화 상태",
                        interactive=False,
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
                        # Gradio 6.0에서는 type, show_copy_button 파라미터가 제거됨
                        # Chatbot은 기본적으로 긴 텍스트를 표시할 수 있음
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="💬 메시지를 입력하세요",
                            placeholder="예: 안녕하세요! 이 대체 타임라인에서 당신의 인생은 어떻게 달라졌나요?",
                            scale=4,
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
    
    def on_book_selected(book_display, language):
        """책 선택 시 해당 책의 캐릭터 목록 업데이트"""
        if not book_display:
            msg = "책을 선택해주세요." if language == "ko" else "Please select a book."
            return gr.update(choices=[], value=None), gr.update(value=msg)
        
        characters = get_characters_by_book(book_display)
        if characters:
            msg = "주인공을 선택해주세요." if language == "ko" else "Please select a character."
            return gr.update(choices=characters, value=characters[0]), gr.update(value=msg)
        else:
            msg = "이 책의 캐릭터를 찾을 수 없습니다." if language == "ko" else "No characters found for this book."
            return gr.update(choices=[], value=None), gr.update(value=msg)
    
    def on_character_selected(book_display, character_name, language):
        """캐릭터 선택 시 정보 업데이트"""
        if not book_display or not character_name:
            return "책과 주인공을 선택해주세요." if language == "ko" else "Please select a book and character."
        return get_character_info(book_display, character_name, language)
    
    def on_language_changed(language, book_display, character_name):
        """언어 변경 시 캐릭터 정보 업데이트"""
        if book_display and character_name:
            return get_character_info(book_display, character_name, language)
        return "책과 주인공을 선택해주세요." if language == "ko" else "Please select a book and character."
    
    # 언어 변경 시 캐릭터 정보 업데이트
    language_radio.change(
        fn=on_language_changed,
        inputs=[language_radio, book_dropdown, character_dropdown],
        outputs=[character_info]
    )
    
    # 책 선택 시 캐릭터 목록 업데이트
    book_dropdown.change(
        fn=on_book_selected,
        inputs=[book_dropdown, language_radio],
        outputs=[character_dropdown, character_info]
    )
    
    # 캐릭터 선택 시 정보 업데이트
    character_dropdown.change(
        fn=on_character_selected,
        inputs=[book_dropdown, character_dropdown, language_radio],
        outputs=[character_info]
    )
    
    # 세션별 상태 관리 (gr.State 사용) - 시나리오 생성 전에 정의
    session_state = gr.State(value={
        'scenario_id': None,
        'conversation_id': None,
        'turn_count': 0
    })
    
    # 시나리오 생성
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
        outputs=[scenario_result, scenario_id_display, current_scenario_display, chatbot, session_state]
    )
    
    # 메시지 전송
    def on_submit(message, history, current_scenario_display_val, language, state):
        # 세션별 상태에서 시나리오 ID 가져오기
        if not state.get('scenario_id'):
            error_msg = "❌ 시나리오를 먼저 생성해주세요." if language == "ko" else "❌ Please create a scenario first."
            turn_msg = "턴: 0/5" if language == "ko" else "Turn: 0/5"
            return history, error_msg, turn_msg, gr.update(visible=False), gr.update(visible=False), "", state
        
        if not message.strip():
            turn_msg = f"턴: {state.get('turn_count', 0)}/5" if language == "ko" else f"Turn: {state.get('turn_count', 0)}/5"
            return history, "", turn_msg, gr.update(visible=False), gr.update(visible=False), "", state
        
        # 첫 대화인지 계속 대화인지 확인
        if not state.get('conversation_id'):
            return start_first_conversation(message, state['scenario_id'], history, language, state)
        else:
            return continue_conversation(message, state['scenario_id'], state['conversation_id'], history, language, state)
    
    msg.submit(
        fn=on_submit,
        inputs=[msg, chatbot, current_scenario_display, language_radio, session_state],
        outputs=[chatbot, conversation_status, turn_info, save_btn, cancel_btn, msg, session_state]
    )
    
    submit_btn.click(
        fn=on_submit,
        inputs=[msg, chatbot, current_scenario_display, language_radio, session_state],
        outputs=[chatbot, conversation_status, turn_info, save_btn, cancel_btn, msg, session_state]
    )
    
    # 대화 저장/취소
    def on_save(current_scenario_display_val, history, state):
        if not state.get('scenario_id') or not state.get('conversation_id'):
            return "❌ 저장할 대화가 없습니다.", [], state
        result_msg, updated_state = confirm_conversation(state['scenario_id'], state['conversation_id'], "save", state)
        return result_msg, [], updated_state
    
    def on_cancel(current_scenario_display_val, history, state):
        if not state.get('scenario_id') or not state.get('conversation_id'):
            return "❌ 취소할 대화가 없습니다.", [], state
        result_msg, updated_state = confirm_conversation(state['scenario_id'], state['conversation_id'], "cancel", state)
        return result_msg, [], updated_state
    
    save_btn.click(
        fn=on_save,
        inputs=[current_scenario_display, chatbot, session_state],
        outputs=[confirm_result, chatbot, session_state]
    )
    
    cancel_btn.click(
        fn=on_cancel,
        inputs=[current_scenario_display, chatbot, session_state],
        outputs=[confirm_result, chatbot, session_state]
    )
    
    # 예제 버튼
    example1.click(fn=set_example1, outputs=[msg])
    example2.click(fn=set_example2, outputs=[msg])
    example3.click(fn=set_example3, outputs=[msg])


if __name__ == "__main__":
    try:
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
        print(f"⚠️ Public 링크 생성 실패: {str(e)}")
        print("📍 Local URL만 사용합니다: http://localhost:7860")
        demo.launch(
            server_name="localhost",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False,
            theme=gr.themes.Soft()
        )
