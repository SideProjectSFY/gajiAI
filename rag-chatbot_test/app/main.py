"""
FastAPI 메인 애플리케이션

RAG 기반 "What If" 챗봇 API 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = FastAPI(
    title="Gaji AI Backend - Character Chat",
    description="책 속 인물과 대화하는 AI 챗봇 (Gemini File Search 기반)",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from app.routers import character_chat
app.include_router(character_chat.router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Gaji AI Backend - Character Chat API",
        "version": "2.0.0",
        "description": "책 속 인물과 대화하는 AI 챗봇 (Gemini File Search 기반)",
        "endpoints": {
            "character_list": "/character/list",
            "character_info": "/character/info/{character_name}",
            "chat": "/character/chat",
            "chat_stream": "/character/chat/stream",
            "health": "/character/health"
        }
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

