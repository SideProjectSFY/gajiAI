#!/bin/bash

# Scenario Types Tester 실행 스크립트

echo "🧪 Starting Scenario Types Tester..."
echo ""
echo "📍 URL: http://localhost:7861"
echo "📚 소설: 해리 포터, 위대한 개츠비, 오만과 편견, 1984"
echo ""
echo "💡 사용법:"
echo "  1. 소설과 캐릭터 선택"
echo "  2. 3가지 시나리오 타입 중 최소 1개 입력 (각 10자 이상)"
echo "  3. 시나리오 생성 버튼 클릭"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 가상환경 확인
if [ ! -d "../.venv" ]; then
    echo "❌ 가상환경이 없습니다. 먼저 생성하세요:"
    echo "   python -m venv ../.venv"
    echo "   source ../.venv/bin/activate"
    echo "   pip install -r scenario_types_requirements.txt"
    exit 1
fi

# 가상환경 활성화
source ../.venv/bin/activate

# Gradio 설치 확인 및 설치
if ! python -c "import gradio" 2>/dev/null; then
    echo "📦 Installing Gradio in virtual environment..."
    pip install gradio>=4.0.0
fi

# 앱 실행
python scenario_types_tester.py
