"""
FastAPI 메인 애플리케이션

RAG 기반 "What If" 챗봇 API 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import chat

app = FastAPI(
    title="Gaji AI Backend - RAG Chatbot",
    description="RAG 기반 What If 챗봇 API",
    version="0.1.0"
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
app.include_router(chat.router)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Gaji AI Backend - RAG Chatbot API",
        "version": "0.1.0",
        "endpoints": {
            "chat": "/api/ai/conversations/{id}/messages",
            "chat_stream": "/api/ai/conversations/{id}/messages/stream",
            "search": "/api/ai/search/passages"
        }
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

