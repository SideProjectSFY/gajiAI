# -*- coding: utf-8 -*-
"""
Gradio UI for What If Scenario Chat

What If 시나리오를 생성하고 시나리오대로 캐릭터와 대화하는 인터페이스
"""

import os
import sys
import gradio as gr
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 서비스 직접 import
from app.services.character_chat_service import CharacterChatService
from app.services.scenario_management_service import ScenarioManagementService
from app.services.scenario_chat_service import ScenarioChatService
from app.services.api_key_manager import get_api_key_manager

# 전역 변수
character_service = None
scenario_service = None
scenario_chat_service = None
available_characters = []
current_scenario_id = None
current_conversation_id = None
current_turn_count = 0
max_turns = 5


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


def get_character_names():
    """캐릭터 이름 목록 반환"""
    if not available_characters:
        return []
    return [char['character_name'] for char in available_characters]


def get_character_info(character_name):
    """캐릭터 정보 가져오기"""
    if not character_service or not character_name:
        return ""
    
    try:
        character = character_service.get_character_info(character_name)
        if character:
            info = f"""
**캐릭터**: {character['character_name']}
**책**: {character['book_title']}
**저자**: {character['author']}
"""
            if 'persona' in character:
                info += f"\n**페르소나**: {character['persona'][:200]}..."
            return info
        return "캐릭터를 찾을 수 없습니다."
    except Exception as e:
        return f"오류: {str(e)}"


def create_scenario(
    scenario_name,
    character_name,
    character_property_enabled,
    character_property_desc,
    event_alteration_enabled,
    event_alteration_desc,
    setting_modification_enabled,
    setting_modification_desc,
    is_public
):
    """시나리오 생성"""
    global current_scenario_id, current_conversation_id, current_turn_count
    
    if not scenario_service:
        return "❌ 서비스를 먼저 초기화해주세요.", "", "시나리오를 먼저 생성해주세요.", []
    
    if not scenario_name or not character_name:
        return "❌ 시나리오 이름과 캐릭터를 선택해주세요.", "", "시나리오를 먼저 생성해주세요.", []
    
    try:
        # 캐릭터 정보 가져오기
        character = character_service.get_character_info(character_name)
        if not character:
            return f"❌ 캐릭터를 찾을 수 없습니다: {character_name}", "", "시나리오를 먼저 생성해주세요.", []
        
        book_title = character['book_title']
        
        # 시나리오 설명 구성
        descriptions = {
            "character_property_changes": {
                "enabled": character_property_enabled,
                "description": character_property_desc if character_property_enabled else ""
            },
            "event_alterations": {
                "enabled": event_alteration_enabled,
                "description": event_alteration_desc if event_alteration_enabled else ""
            },
            "setting_modifications": {
                "enabled": setting_modification_enabled,
                "description": setting_modification_desc if setting_modification_enabled else ""
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
        
        current_scenario_id = result['scenario_id']
        current_conversation_id = None
        current_turn_count = 0
        
        scenario_info = f"""
**시나리오 생성 완료!**

**시나리오 이름**: {scenario_name}
**캐릭터**: {character_name}
**책**: {book_title}
**시나리오 ID**: {current_scenario_id}

이제 첫 대화를 시작하세요!
"""
        
        return scenario_info, current_scenario_id, current_scenario_id, []
    
    except Exception as e:
        return f"❌ 시나리오 생성 실패: {str(e)}", "", "시나리오를 먼저 생성해주세요.", []


# 대화 기록 저장 (세션별)
conversation_histories = {}

def start_first_conversation(message, scenario_id, history):
    """첫 대화 시작"""
    global current_conversation_id, current_turn_count
    
    if not scenario_chat_service or not scenario_id:
        return history, "❌ 시나리오를 먼저 생성해주세요.", "턴: 0/5", gr.update(visible=False), gr.update(visible=False)
    
    if not message.strip():
        return history, "", "턴: 0/5", gr.update(visible=False), gr.update(visible=False)
    
    try:
        result = scenario_chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=message,
            output_language="ko",
            is_creator=True,
            conversation_id=current_conversation_id
        )
        
        current_conversation_id = result['conversation_id']
        current_turn_count = result['turn_count']
        
        # 대화 기록에 추가
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result['response']}
        ]
        
        # 세션별 기록 저장
        conversation_histories[current_conversation_id] = history
        
        status_msg = f"턴 {current_turn_count}/{result['max_turns']}"
        turn_info = f"턴: {current_turn_count}/{result['max_turns']}"
        
        # 5턴 완료 시 저장/취소 버튼 표시
        if current_turn_count >= result['max_turns']:
            return history, status_msg, turn_info, gr.update(visible=True), gr.update(visible=True)
        else:
            return history, status_msg, turn_info, gr.update(visible=False), gr.update(visible=False)
    
    except Exception as e:
        return history, f"❌ 대화 시작 실패: {str(e)}", "턴: 0/5", gr.update(visible=False), gr.update(visible=False)


def continue_conversation(message, scenario_id, conversation_id, history):
    """대화 계속"""
    global current_turn_count
    
    if not scenario_chat_service or not scenario_id:
        return history, "❌ 시나리오를 먼저 생성해주세요.", "턴: 0/5", gr.update(visible=False), gr.update(visible=False)
    
    if not message.strip():
        return history, "", f"턴: {current_turn_count}/5", gr.update(visible=False), gr.update(visible=False)
    
    try:
        result = scenario_chat_service.first_conversation(
            scenario_id=scenario_id,
            initial_message=message,
            output_language="ko",
            is_creator=True,
            conversation_id=conversation_id
        )
        
        current_turn_count = result['turn_count']
        
        # 대화 기록에 추가
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result['response']}
        ]
        
        # 세션별 기록 업데이트
        conversation_histories[conversation_id] = history
        
        status_msg = f"턴 {current_turn_count}/{result['max_turns']}"
        turn_info = f"턴: {current_turn_count}/{result['max_turns']}"
        
        # 5턴 완료 시 저장/취소 버튼 표시
        if current_turn_count >= result['max_turns']:
            return history, status_msg, turn_info, gr.update(visible=True), gr.update(visible=True)
        else:
            return history, status_msg, turn_info, gr.update(visible=False), gr.update(visible=False)
    
    except Exception as e:
        return history, f"❌ 대화 계속 실패: {str(e)}", f"턴: {current_turn_count}/5", gr.update(visible=False), gr.update(visible=False)


def confirm_conversation(scenario_id, conversation_id, action):
    """대화 최종 확인"""
    global current_scenario_id, current_conversation_id, current_turn_count
    
    if not scenario_chat_service or not scenario_id or not conversation_id:
        return "❌ 시나리오와 대화를 먼저 생성해주세요."
    
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
            current_conversation_id = None
            current_turn_count = 0
            return f"✅ 대화가 저장되었습니다!\n\n{result.get('message', '')}"
        else:
            # 대화 기록 초기화
            if conversation_id in conversation_histories:
                del conversation_histories[conversation_id]
            current_conversation_id = None
            current_turn_count = 0
            return "❌ 대화가 취소되었습니다."
    
    except Exception as e:
        return f"❌ 확인 실패: {str(e)}"


# 서비스 초기화
init_success, init_message = initialize_service()

# Gradio UI 구성
with gr.Blocks(title="Gaji What If Scenario Chat", theme=gr.themes.Soft()) as demo:
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
                    gr.Markdown("### 📝 시나리오 기본 정보")
                    
                    scenario_name = gr.Textbox(
                        label="시나리오 이름",
                        placeholder="예: 헤르미온이가 슬리데린에 배정되었다면?",
                        interactive=True
                    )
                    
                    character_dropdown = gr.Dropdown(
                        choices=get_character_names(),
                        label="🎭 캐릭터 선택",
                        value=get_character_names()[0] if get_character_names() else None,
                        interactive=True
                    )
                    
                    character_info = gr.Markdown(
                        value="캐릭터를 선택하면 정보가 표시됩니다.",
                        label="캐릭터 정보"
                    )
                    
                    is_public = gr.Checkbox(
                        label="공개 시나리오",
                        value=False,
                        info="다른 사용자들이 볼 수 있게 공개"
                    )
                
                with gr.Column(scale=2):
                    gr.Markdown("### 🔀 What If 변경사항")
                    
                    with gr.Accordion("1. 캐릭터 속성 변경", open=False):
                        character_property_enabled = gr.Checkbox(
                            label="활성화",
                            value=False
                        )
                        character_property_desc = gr.Textbox(
                            label="변경 설명",
                            placeholder="예: 헤르미온이가 그리핀도르 대신 슬리데린에 배정되고, 야망이 더 강해졌다면?",
                            lines=3,
                            interactive=True
                        )
                    
                    with gr.Accordion("2. 사건 변경", open=False):
                        event_alteration_enabled = gr.Checkbox(
                            label="활성화",
                            value=False
                        )
                        event_alteration_desc = gr.Textbox(
                            label="변경 설명",
                            placeholder="예: 게츠비가 데이지를 만나지 않았다면?",
                            lines=3,
                            interactive=True
                        )
                    
                    with gr.Accordion("3. 배경 변경", open=False):
                        setting_modification_enabled = gr.Checkbox(
                            label="활성화",
                            value=False
                        )
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
                        label="대화창",
                        type="messages",
                        show_copy_button=True
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
    
    # 캐릭터 선택 시 정보 업데이트
    character_dropdown.change(
        fn=get_character_info,
        inputs=[character_dropdown],
        outputs=[character_info]
    )
    
    # 시나리오 생성
    create_scenario_btn.click(
        fn=create_scenario,
        inputs=[
            scenario_name,
            character_dropdown,
            character_property_enabled,
            character_property_desc,
            event_alteration_enabled,
            event_alteration_desc,
            setting_modification_enabled,
            setting_modification_desc,
            is_public
        ],
        outputs=[scenario_result, scenario_id_display, current_scenario_display, chatbot]
    )
    
    # 메시지 전송
    def on_submit(message, history, scenario_id_display_val):
        if not scenario_id_display_val or scenario_id_display_val == "":
            return history, "❌ 시나리오를 먼저 생성해주세요.", "턴: 0/5", gr.update(visible=False), gr.update(visible=False), ""
        
        if not message.strip():
            return history, "", f"턴: {current_turn_count}/5", gr.update(visible=False), gr.update(visible=False), ""
        
        # 첫 대화인지 계속 대화인지 확인
        if not current_conversation_id:
            return start_first_conversation(message, scenario_id_display_val, history)
        else:
            return continue_conversation(message, scenario_id_display_val, current_conversation_id, history)
    
    msg.submit(
        fn=on_submit,
        inputs=[msg, chatbot, scenario_id_display],
        outputs=[chatbot, conversation_status, turn_info, save_btn, cancel_btn, msg]
    )
    
    submit_btn.click(
        fn=on_submit,
        inputs=[msg, chatbot, scenario_id_display],
        outputs=[chatbot, conversation_status, turn_info, save_btn, cancel_btn, msg]
    )
    
    # 대화 저장/취소
    def on_save(scenario_id_display_val, history):
        if not scenario_id_display_val or not current_conversation_id:
            return "❌ 저장할 대화가 없습니다.", []
        result_msg = confirm_conversation(scenario_id_display_val, current_conversation_id, "save")
        return result_msg, []
    
    def on_cancel(scenario_id_display_val, history):
        if not scenario_id_display_val or not current_conversation_id:
            return "❌ 취소할 대화가 없습니다.", []
        result_msg = confirm_conversation(scenario_id_display_val, current_conversation_id, "cancel")
        return result_msg, []
    
    save_btn.click(
        fn=on_save,
        inputs=[scenario_id_display, chatbot],
        outputs=[confirm_result, chatbot]
    )
    
    cancel_btn.click(
        fn=on_cancel,
        inputs=[scenario_id_display, chatbot],
        outputs=[confirm_result, chatbot]
    )
    
    # 예제 버튼
    example1.click(fn=set_example1, outputs=[msg])
    example2.click(fn=set_example2, outputs=[msg])
    example3.click(fn=set_example3, outputs=[msg])


if __name__ == "__main__":
    # 로컬 실행
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,  # 공개 URL 생성 (72시간 동안 유효)
        show_error=True
    )
