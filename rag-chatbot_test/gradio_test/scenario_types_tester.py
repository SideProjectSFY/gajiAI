# -*- coding: utf-8 -*-
"""
Gradio UI for Testing Scenario Types

Tests the three scenario types:
1. Character Changes (character_changes)
2. Event Alterations (event_alterations)
3. Setting Modifications (setting_modifications)

Aligns with V16 database migration:
- novel_id reference
- Free-form text fields for each scenario type
"""

import os
import sys
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional
import json

# 프로젝트 루트를 Python 경로에 추가
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Mock data for testing
MOCK_NOVELS = [
    {"id": "novel-001", "title": "해리 포터와 마법사의 돌", "author": "J.K. 롤링"},
    {"id": "novel-002", "title": "위대한 개츠비", "author": "F. 스콧 피츠제럴드"},
    {"id": "novel-003", "title": "오만과 편견", "author": "제인 오스틴"},
    {"id": "novel-004", "title": "1984", "author": "조지 오웰"},
]

MOCK_CHARACTERS = {
    "novel-001": ["해리 포터", "헤르미온 그레인저", "론 위즐리", "덤블도어"],
    "novel-002": ["제이 개츠비", "닉 캐러웨이", "데이지 뷰캐넌"],
    "novel-003": ["엘리자베스 베넷", "미스터 다아시", "제인 베넷"],
    "novel-004": ["윈스턴 스미스", "줄리아", "오브라이언"],
}

# 시나리오 타입 예제 템플릿
SCENARIO_TYPE_TEMPLATES = {
    "character_changes": {
        "해리 포터": [
            "해리가 슬리데린에 배정되었다면? 야망이 더 강해지고 순수혈통 이념에 영향을 받는다.",
            "해리가 마법 능력이 없었다면? 마법 세계를 외부에서 관찰하는 평범한 인간으로 살아간다.",
            "해리가 볼드모트의 후계자로 선택되었다면? 어둠의 힘을 계승하고 내면의 선함과 갈등한다.",
        ],
        "헤르미온 그레인저": [
            "헤르미온이 순수혈통 가문 출신이었다면? 머글 태생에 대한 차별을 이해하지 못하고 특권의식이 있다.",
            "헤르미온이 라벤클로에 배정되었다면? 학문적 성취에만 집중하고 우정보다 지식을 우선시한다.",
            "헤르미온이 마법부 장관의 딸이었다면? 정치적 영향력을 가지고 권력의 부패를 목격한다.",
        ],
        "제이 개츠비": [
            "개츠비가 부유한 가문 출신이었다면? 데이지를 얻기 위해 노력할 필요가 없고 자만심이 강하다.",
            "개츠비가 전쟁에서 사망했다면? (유령으로 등장) 이루지 못한 사랑에 대한 미련과 후회로 가득하다.",
            "개츠비가 데이지와 결혼했다면? 이상화된 사랑이 현실과 마주하며 환멸을 느낀다.",
        ],
    },
    "event_alterations": {
        "해리 포터": [
            "볼드모트가 해리 대신 네빌을 공격했다면? 해리는 평범한 마법사로 성장하고 네빌이 '선택된 자'가 된다.",
            "제임스와 릴리가 살아있다면? 해리는 사랑받는 가정에서 자라고 더슬리 가족과의 고통이 없다.",
            "호그와트가 폐쇄되었다면? 마법 교육이 금지되고 마법사들이 비밀리에 모여 저항한다.",
        ],
        "위대한 개츠비": [
            "개츠비가 데이지를 만나지 않았다면? 그의 야망과 부의 축적에 대한 동기가 사라진다.",
            "머틀이 톰의 차에 치이지 않았다면? 개츠비의 몰락이 일어나지 않고 데이지와의 관계가 계속된다.",
            "금주법이 시행되지 않았다면? 개츠비의 부의 원천이 사라지고 사회적 지위 상승이 불가능해진다.",
        ],
    },
    "setting_modifications": {
        "해리 포터": [
            "현대 2024년 서울에서 일어난다면? 호그와트가 강남의 사립학교이고 SNS로 마법이 알려질 위험이 있다.",
            "머글 세계가 마법을 알고 있다면? 마법사와 머글 간의 긴장과 갈등, 마법 기술의 상업화가 일어난다.",
            "마법이 사라진 세계에서 일어난다면? 과거의 마법 유산을 찾아 복원하려는 모험이 펼쳐진다.",
        ],
        "오만과 편견": [
            "2024년 서울의 재벌 가문에서 일어난다면? 엘리자베스는 스타트업 CEO이고 다아시는 대기업 후계자이다.",
            "빅토리아 시대 미국 서부에서 일어난다면? 개척 시대의 거친 환경에서 계급 의식이 약화된다.",
            "디지털 시대의 소셜미디어를 통해 만난다면? 온라인에서 시작된 오해와 편견이 오프라인으로 이어진다.",
        ],
    },
}


class ScenarioTypesTester:
    """시나리오 타입 테스터"""
    
    def __init__(self):
        self.scenarios = []
        self.current_scenario = None
    
    def get_novel_titles(self) -> List[str]:
        """소설 제목 목록 반환"""
        return [novel["title"] for novel in MOCK_NOVELS]
    
    def get_novel_by_title(self, title: str) -> Optional[Dict]:
        """제목으로 소설 찾기"""
        for novel in MOCK_NOVELS:
            if novel["title"] == title:
                return novel
        return None
    
    def get_characters_for_novel(self, novel_title: str) -> List[str]:
        """소설의 캐릭터 목록 반환"""
        novel = self.get_novel_by_title(novel_title)
        if novel:
            return MOCK_CHARACTERS.get(novel["id"], [])
        return []
    
    def get_template_suggestions(self, scenario_type: str, character_name: str) -> List[str]:
        """시나리오 타입과 캐릭터에 대한 템플릿 제안"""
        templates = SCENARIO_TYPE_TEMPLATES.get(scenario_type, {})
        return templates.get(character_name, [])
    
    def create_scenario(
        self,
        scenario_name: str,
        novel_title: str,
        character_name: str,
        character_changes: str,
        event_alterations: str,
        setting_modifications: str,
    ) -> Dict:
        """시나리오 생성"""
        
        if not scenario_name:
            return {"success": False, "message": "❌ 시나리오 이름을 입력하세요."}
        
        if not novel_title:
            return {"success": False, "message": "❌ 소설을 선택하세요."}
        
        # 최소한 하나의 시나리오 타입은 입력되어야 함
        if not any([character_changes, event_alterations, setting_modifications]):
            return {"success": False, "message": "❌ 최소 하나의 시나리오 타입을 입력하세요."}
        
        # 입력된 필드는 최소 10자 이상이어야 함 (DB 제약조건)
        errors = []
        if character_changes and len(character_changes.strip()) < 10:
            errors.append("캐릭터 변경")
        if event_alterations and len(event_alterations.strip()) < 10:
            errors.append("사건 변경")
        if setting_modifications and len(setting_modifications.strip()) < 10:
            errors.append("배경 변경")
        
        if errors:
            return {
                "success": False,
                "message": f"❌ 다음 필드는 최소 10자 이상 입력해야 합니다: {', '.join(errors)}"
            }
        
        novel = self.get_novel_by_title(novel_title)
        
        scenario = {
            "scenario_id": f"scenario-{len(self.scenarios) + 1:03d}",
            "scenario_name": scenario_name,
            "novel_id": novel["id"],
            "novel_title": novel_title,
            "author": novel["author"],
            "character_name": character_name,
            "character_changes": character_changes.strip() if character_changes else None,
            "event_alterations": event_alterations.strip() if event_alterations else None,
            "setting_modifications": setting_modifications.strip() if setting_modifications else None,
        }
        
        self.scenarios.append(scenario)
        self.current_scenario = scenario
        
        return {
            "success": True,
            "message": "✅ 시나리오가 생성되었습니다!",
            "scenario": scenario
        }
    
    def get_scenario_summary(self, scenario: Dict) -> str:
        """시나리오 요약 생성"""
        summary = f"""
## ✨ 시나리오 생성 완료!

**시나리오 ID**: `{scenario['scenario_id']}`  
**시나리오 이름**: {scenario['scenario_name']}

---

### 📚 원작 정보

**소설**: {scenario['novel_title']}  
**저자**: {scenario['author']}  
**캐릭터**: {scenario['character_name']}

---

### 🔀 What If 변경사항

"""
        
        if scenario['character_changes']:
            summary += f"""
#### 1️⃣ 캐릭터 변경

```
{scenario['character_changes']}
```

"""
        
        if scenario['event_alterations']:
            summary += f"""
#### 2️⃣ 사건 변경

```
{scenario['event_alterations']}
```

"""
        
        if scenario['setting_modifications']:
            summary += f"""
#### 3️⃣ 배경 변경

```
{scenario['setting_modifications']}
```

"""
        
        summary += """
---

### 📊 데이터베이스 저장 정보

**테이블**: `root_user_scenarios`  
**필드**:
- `novel_id` (UUID) ✅
- `character_changes` (TEXT) ✅
- `event_alterations` (TEXT) ✅
- `setting_modifications` (TEXT) ✅

**검증 결과**:
- ✅ 모든 필드가 최소 길이 요구사항(10자) 충족
- ✅ FREE-FORM TEXT 형식으로 저장 가능
- ✅ NULL 값 허용 (선택적 필드)
"""
        
        return summary
    
    def export_scenario_json(self, scenario: Dict) -> str:
        """시나리오를 JSON 형식으로 내보내기"""
        return json.dumps(scenario, ensure_ascii=False, indent=2)
    
    def export_scenario_sql(self, scenario: Dict) -> str:
        """시나리오를 SQL INSERT 문으로 내보내기"""
        def escape_sql(text):
            if text is None:
                return "NULL"
            escaped_text = text.replace("'", "''")
            return f"'{escaped_text}'"
        
        sql = f"""
-- 시나리오: {scenario['scenario_name']}
INSERT INTO root_user_scenarios (
    scenario_id,
    novel_id,
    character_name,
    character_changes,
    event_alterations,
    setting_modifications
) VALUES (
    '{scenario['scenario_id']}',
    '{scenario['novel_id']}',
    '{scenario['character_name']}',
    {escape_sql(scenario['character_changes'])},
    {escape_sql(scenario['event_alterations'])},
    {escape_sql(scenario['setting_modifications'])}
);
"""
        return sql


# 테스터 인스턴스 생성
tester = ScenarioTypesTester()


def create_ui():
    """Gradio UI 생성"""
    
    with gr.Blocks(title="Scenario Types Tester") as demo:
        gr.Markdown(
            """
            # 🧪 Scenario Types Tester
            
            **V16 Migration 테스트**: 3가지 시나리오 타입 (Character Changes, Event Alterations, Setting Modifications)
            
            이 도구는 다음을 테스트합니다:
            - 📝 Free-form text 입력 (최소 10자)
            - 🔗 Novel ID 참조 관계
            - ✅ NULL 허용 (선택적 필드)
            - 💾 데이터베이스 저장 형식
            """
        )
        
        with gr.Tabs() as tabs:
            # 탭 1: 시나리오 생성
            with gr.Tab("1️⃣ 시나리오 생성"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📚 기본 정보")
                        
                        scenario_name_input = gr.Textbox(
                            label="시나리오 이름",
                            placeholder="예: 슬리데린의 헤르미온",
                            info="시나리오를 설명하는 이름"
                        )
                        
                        novel_dropdown = gr.Dropdown(
                            choices=tester.get_novel_titles(),
                            label="소설 선택",
                            info="원작 소설 선택"
                        )
                        
                        character_dropdown = gr.Dropdown(
                            choices=[],
                            label="캐릭터 선택",
                            info="시나리오의 주인공"
                        )
                        
                        create_btn = gr.Button("✨ 시나리오 생성", variant="primary", size="lg")
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 🔀 What If 시나리오 타입")
                        
                        with gr.Accordion("1️⃣ Character Changes (캐릭터 변경)", open=True):
                            gr.Markdown(
                                """
                                캐릭터의 **속성, 성격, 배경, 능력**이 변경된다면?
                                
                                **예시**:
                                - 해리가 슬리데린에 배정되었다면?
                                - 헤르미온이 순수혈통 가문 출신이었다면?
                                - 개츠비가 부유한 가문 출신이었다면?
                                """
                            )
                            
                            character_changes_input = gr.Textbox(
                                label="캐릭터 변경 설명",
                                placeholder="예: 헤르미온이 슬리데린에 배정되고, 야망이 더 강해지며 순수혈통 이념에 영향을 받는다면?",
                                lines=4,
                                info="최소 10자 이상 입력 (선택사항)"
                            )
                            
                            character_template_btn = gr.Button("💡 템플릿 제안 보기", size="sm")
                        
                        with gr.Accordion("2️⃣ Event Alterations (사건 변경)", open=False):
                            gr.Markdown(
                                """
                                원작의 **핵심 사건, 만남, 결정**이 변경된다면?
                                
                                **예시**:
                                - 볼드모트가 해리 대신 네빌을 공격했다면?
                                - 개츠비가 데이지를 만나지 않았다면?
                                - 엘리자베스가 다아시의 첫 청혼을 받아들였다면?
                                """
                            )
                            
                            event_alterations_input = gr.Textbox(
                                label="사건 변경 설명",
                                placeholder="예: 볼드모트가 해리 대신 네빌을 공격했다면? 해리는 평범한 마법사로 성장하고 네빌이 '선택된 자'가 된다.",
                                lines=4,
                                info="최소 10자 이상 입력 (선택사항)"
                            )
                            
                            event_template_btn = gr.Button("💡 템플릿 제안 보기", size="sm")
                        
                        with gr.Accordion("3️⃣ Setting Modifications (배경 변경)", open=False):
                            gr.Markdown(
                                """
                                **시간적 배경, 공간적 배경, 사회적 맥락**이 변경된다면?
                                
                                **예시**:
                                - 해리 포터가 2024년 서울에서 일어난다면?
                                - 오만과 편견이 현대 미국에서 일어난다면?
                                - 1984가 디지털 감시 시대에 일어난다면?
                                """
                            )
                            
                            setting_modifications_input = gr.Textbox(
                                label="배경 변경 설명",
                                placeholder="예: 호그와트가 2024년 강남의 사립학교이고, SNS로 마법이 세상에 알려질 위험이 있다면?",
                                lines=4,
                                info="최소 10자 이상 입력 (선택사항)"
                            )
                            
                            setting_template_btn = gr.Button("💡 템플릿 제안 보기", size="sm")
                
                gr.Markdown("### 📋 생성 결과")
                
                result_message = gr.Markdown(value="시나리오를 생성하면 결과가 여기에 표시됩니다.")
            
            # 탭 2: 생성된 시나리오 보기
            with gr.Tab("2️⃣ 생성된 시나리오"):
                gr.Markdown("### 📊 생성된 시나리오 목록")
                
                scenario_list = gr.Dataframe(
                    headers=["ID", "이름", "소설", "캐릭터"],
                    datatype=["str", "str", "str", "str"],
                    interactive=False,
                    value=[],
                )
                
                refresh_btn = gr.Button("🔄 새로고침", size="sm")
                
                gr.Markdown("### 📄 시나리오 상세")
                
                scenario_detail = gr.Markdown(value="시나리오를 선택하면 상세 정보가 표시됩니다.")
            
            # 탭 3: 데이터 내보내기
            with gr.Tab("3️⃣ 데이터 내보내기"):
                gr.Markdown("### 💾 내보내기 형식")
                
                with gr.Row():
                    json_btn = gr.Button("📄 JSON 내보내기", variant="secondary")
                    sql_btn = gr.Button("🗄️ SQL 내보내기", variant="secondary")
                
                export_output = gr.Code(label="내보내기 결과", language="json", lines=20)
                
                gr.Markdown(
                    """
                    ### 📝 데이터베이스 스키마 참고
                    
                    ```sql
                    ALTER TABLE root_user_scenarios 
                    ADD COLUMN novel_id UUID REFERENCES novels(id) ON DELETE CASCADE,
                    ADD COLUMN character_changes TEXT,
                    ADD COLUMN event_alterations TEXT,
                    ADD COLUMN setting_modifications TEXT;
                    ```
                    
                    **제약조건**:
                    - `character_changes`: 최소 10자 (입력 시)
                    - `event_alterations`: 최소 10자 (입력 시)
                    - `setting_modifications`: 최소 10자 (입력 시)
                    - 모든 필드는 NULL 허용 (선택사항)
                    """
                )
        
        # 이벤트 핸들러
        
        def on_novel_select(novel_title):
            """소설 선택 시 캐릭터 목록 업데이트"""
            characters = tester.get_characters_for_novel(novel_title)
            return gr.update(choices=characters, value=characters[0] if characters else None)
        
        novel_dropdown.change(
            fn=on_novel_select,
            inputs=[novel_dropdown],
            outputs=[character_dropdown]
        )
        
        def on_create_scenario(scenario_name, novel_title, character_name, 
                              character_changes, event_alterations, setting_modifications):
            """시나리오 생성"""
            result = tester.create_scenario(
                scenario_name,
                novel_title,
                character_name,
                character_changes,
                event_alterations,
                setting_modifications
            )
            
            if result["success"]:
                summary = tester.get_scenario_summary(result["scenario"])
                return summary
            else:
                return result["message"]
        
        create_btn.click(
            fn=on_create_scenario,
            inputs=[
                scenario_name_input,
                novel_dropdown,
                character_dropdown,
                character_changes_input,
                event_alterations_input,
                setting_modifications_input
            ],
            outputs=[result_message]
        )
        
        def on_refresh_list():
            """시나리오 목록 새로고침"""
            data = [
                [s["scenario_id"], s["scenario_name"], s["novel_title"], s["character_name"]]
                for s in tester.scenarios
            ]
            return data
        
        refresh_btn.click(
            fn=on_refresh_list,
            outputs=[scenario_list]
        )
        
        def show_character_templates(character_name):
            """캐릭터 변경 템플릿 표시"""
            if not character_name:
                return "캐릭터를 먼저 선택하세요."
            
            templates = tester.get_template_suggestions("character_changes", character_name)
            if templates:
                result = f"### 💡 {character_name}의 캐릭터 변경 템플릿\n\n"
                for i, template in enumerate(templates, 1):
                    result += f"{i}. {template}\n\n"
                return result
            return f"{character_name}에 대한 템플릿이 아직 없습니다."
        
        def show_event_templates(character_name):
            """사건 변경 템플릿 표시"""
            if not character_name:
                return "캐릭터를 먼저 선택하세요."
            
            templates = tester.get_template_suggestions("event_alterations", character_name)
            if templates:
                result = f"### 💡 {character_name}의 사건 변경 템플릿\n\n"
                for i, template in enumerate(templates, 1):
                    result += f"{i}. {template}\n\n"
                return result
            return f"{character_name}에 대한 템플릿이 아직 없습니다."
        
        def show_setting_templates(character_name):
            """배경 변경 템플릿 표시"""
            if not character_name:
                return "캐릭터를 먼저 선택하세요."
            
            templates = tester.get_template_suggestions("setting_modifications", character_name)
            if templates:
                result = f"### 💡 {character_name}의 배경 변경 템플릿\n\n"
                for i, template in enumerate(templates, 1):
                    result += f"{i}. {template}\n\n"
                return result
            return f"{character_name}에 대한 템플릿이 아직 없습니다."
        
        # 템플릿 버튼 클릭 시 팝업 대신 텍스트 영역 업데이트
        character_template_btn.click(
            fn=show_character_templates,
            inputs=[character_dropdown],
            outputs=[result_message]
        )
        
        event_template_btn.click(
            fn=show_event_templates,
            inputs=[character_dropdown],
            outputs=[result_message]
        )
        
        setting_template_btn.click(
            fn=show_setting_templates,
            inputs=[character_dropdown],
            outputs=[result_message]
        )
        
        def export_json():
            """JSON 내보내기"""
            if not tester.current_scenario:
                return "시나리오를 먼저 생성하세요."
            return tester.export_scenario_json(tester.current_scenario)
        
        def export_sql():
            """SQL 내보내기"""
            if not tester.current_scenario:
                return "시나리오를 먼저 생성하세요."
            return tester.export_scenario_sql(tester.current_scenario)
        
        json_btn.click(fn=export_json, outputs=[export_output])
        sql_btn.click(fn=export_sql, outputs=[export_output])
    
    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="localhost",
        server_port=7861,
        share=False,
        show_error=True
    )
