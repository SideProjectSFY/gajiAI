"""
Gemini API Client

Retry logic, Circuit Breaker, Temperature 설정을 포함한 Gemini API 클라이언트
Updated for google-generativeai >= 0.8.3
"""

import time
import asyncio
from typing import Optional, AsyncGenerator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import google.generativeai as genai
import structlog

from app.config import settings

logger = structlog.get_logger()


class CircuitBreaker:
    """Circuit Breaker 패턴 구현"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Args:
            failure_threshold: Circuit을 열 실패 임계값
            timeout: Circuit을 다시 닫기 전 대기 시간 (초)
        """
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Circuit Breaker를 통한 함수 호출"""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                logger.info("circuit_breaker_half_open")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("circuit_breaker_closed")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error("circuit_breaker_opened", failures=self.failure_count)
            raise


class GeminiClient:
    """Gemini API 클라이언트"""
    
    def __init__(self):
        """Gemini 클라이언트 초기화"""
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self.embedding_model = "models/text-embedding-004"
        self.circuit_breaker = CircuitBreaker()
        logger.info("gemini_client_initialized", model=self.model_name)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),  # 1s, 2s, 4s
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 500,
        timeout: int = 30
    ) -> str:
        """
        Gemini API로 응답 생성 (Retry 로직 포함)
        
        Args:
            prompt: 입력 프롬프트
            temperature: 생성 온도 (0.7-0.8: 대화, 0.2: 검증)
            max_output_tokens: 최대 출력 토큰 수
            timeout: 타임아웃 (초)
        
        Returns:
            생성된 텍스트
        """
        try:
            model = genai.GenerativeModel(self.model_name)
            
            response = await asyncio.wait_for(
                model.generate_content_async(
                    prompt,
                    generation_config={
                        'temperature': temperature,
                        'max_output_tokens': max_output_tokens,
                        'top_p': 0.95
                    },
                    safety_settings={
                        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
                    }
                ),
                timeout=timeout
            )
            
            logger.info("gemini_response_generated", tokens=len(response.text))
            return response.text
        
        except asyncio.TimeoutError:
            logger.error("gemini_timeout", timeout=timeout)
            raise Exception(f"Gemini API timeout after {timeout}s")
        except Exception as e:
            logger.error("gemini_error", error=str(e))
            raise
    
    async def generate_response_with_circuit_breaker(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 500
    ) -> str:
        """Circuit Breaker를 통한 응답 생성"""
        return self.circuit_breaker.call(
            self.generate_response,
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
    
    async def generate_response_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 500
    ) -> AsyncGenerator[str, None]:
        """
        스트리밍 응답 생성
        
        Args:
            prompt: 입력 프롬프트
            temperature: 생성 온도
            max_output_tokens: 최대 출력 토큰 수
        
        Yields:
            생성된 텍스트 청크
        """
        try:
            model = genai.GenerativeModel(self.model_name)
            
            response = await model.generate_content_async(
                prompt,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': max_output_tokens,
                    'top_p': 0.95
                },
                safety_settings={
                    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
                },
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error("gemini_stream_error", error=str(e))
            raise
    
    def generate_embedding(self, text: str) -> list[float]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 입력 텍스트
        
        Returns:
            768차원 임베딩 벡터
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error("gemini_embedding_error", error=str(e))
            raise
    
    def generate_query_embedding(self, query: str) -> list[float]:
        """
        쿼리 임베딩 생성
        
        Args:
            query: 검색 쿼리
        
        Returns:
            768차원 임베딩 벡터
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error("gemini_query_embedding_error", error=str(e))
            raise
