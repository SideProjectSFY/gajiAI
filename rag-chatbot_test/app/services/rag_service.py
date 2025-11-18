"""
RAG (Retrieval-Augmented Generation) 서비스

사용자 질문에 대한 관련 청크를 검색하고 프롬프트를 생성합니다.
"""

import os
import time
from typing import List, Dict, Optional, Tuple
from uuid import UUID

try:
    import chromadb
    from chromadb.config import Settings
    import google.generativeai as genai
except ImportError as e:
    print(f"❌ 필요한 라이브러리가 설치되지 않았습니다: {e}")
    raise

from app.services.question_classifier import QuestionClassifier


class RAGService:
    """RAG 서비스: 벡터 검색 + 프롬프트 생성"""
    
    def __init__(
        self,
        chroma_path: str = "./chroma_data",
        collection_name: str = "novel_passages",
        gemini_api_key: Optional[str] = None
    ):
        """
        RAG 서비스 초기화
        
        Args:
            chroma_path: ChromaDB 데이터 경로
            collection_name: 컬렉션 이름
            gemini_api_key: Gemini API 키 (없으면 환경변수 사용)
        """
        # ChromaDB 클라이언트
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(
                f"ChromaDB 컬렉션 '{collection_name}'을 찾을 수 없습니다. "
                f"데이터를 먼저 임포트해야 합니다. 오류: {str(e)}"
            )
        
        # Gemini API 설정
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API 키가 필요합니다 (환경변수 GEMINI_API_KEY 또는 파라미터)")
        genai.configure(api_key=api_key)
        
        # Gemini 모델 초기화
        self.embedding_model = "models/text-embedding-004"
        # 기본 모델: gemini-2.5-flash (무료 티어 사용 가능)
        # 다른 모델을 사용하려면 환경변수 GEMINI_MODEL로 변경 가능
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.llm_model = genai.GenerativeModel(model_name)
        
        # 질문 분류기 초기화
        self.question_classifier = QuestionClassifier()
    
    def search_relevant_passages(
        self,
        query: str,
        book_id: Optional[str] = None,
        top_k: int = 8,
        min_score: float = 0.3  # 임계값 낮춤 (0.7 -> 0.3)
    ) -> List[Dict]:
        """
        사용자 질문과 관련된 청크 검색 (개선된 버전)
        
        Args:
            query: 사용자 질문
            book_id: 특정 책으로 필터링 (선택)
            top_k: 반환할 상위 k개 결과 (기본값 증가)
            min_score: 최소 유사도 점수 (거리 기반, 낮을수록 유사)
        
        Returns:
            관련 청크 리스트 (텍스트, 메타데이터, 유사도 포함)
        """
        # 쿼리 임베딩 생성
        query_embedding = genai.embed_content(
            model=self.embedding_model,
            content=query,
            task_type="retrieval_query"
        )['embedding']
        
        # ChromaDB에서 검색 (더 많은 결과 검색)
        # book_id가 있으면 필터링, 없으면 전체 검색
        # book_id는 문자열로 변환하여 검색 (ChromaDB 저장 형식과 일치시키기)
        where_clause = None
        if book_id:
            # 문자열과 숫자 모두 시도
            where_clause = {"book_id": str(book_id)}
        
        # 더 많은 후보를 검색한 후 필터링
        search_k = min(top_k * 3, 30)  # 최대 30개까지 검색 (20 -> 30)
        
        results = None
        if where_clause:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=search_k,
                    where=where_clause
                )
                # 필터링 결과가 없으면 전체 검색으로 fallback
                if not results["ids"] or len(results["ids"][0]) == 0:
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=search_k
                    )
            except Exception as e:
                # book_id 필터링 실패 시 전체 검색 시도
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=search_k
                )
        else:
            # book_id가 없으면 전체 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=search_k
            )
        
        # 결과 포맷팅 및 필터링
        passages = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i] if "distances" in results else None
                
                # 거리 기반 필터링 (거리가 작을수록 유사)
                # 거리를 유사도 점수로 변환 (0-1 범위)
                if distance is not None:
                    # cosine distance를 similarity로 변환 (1 - distance)
                    similarity = 1.0 - min(distance, 1.0)
                    if similarity < min_score:
                        continue
                else:
                    similarity = 1.0
                
                passages.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": distance,
                    "similarity": similarity
                })
        
        # 상위 k개만 반환
        return passages[:top_k]
    
    def build_rag_prompt(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        relevant_passages: Optional[List[Dict]] = None,
        conversation_history: Optional[List[Dict]] = None,
        is_creative: bool = False
    ) -> str:
        """
        RAG 프롬프트 생성 (창의적/사실적 질문에 따라 다른 전략)
        
        Args:
            user_message: 사용자 메시지
            scenario_context: "What If" 시나리오 컨텍스트
            relevant_passages: 검색된 관련 청크
            conversation_history: 대화 이력
            is_creative: 창의적 질문 여부 (True: What If, False: 사실적)
        
        Returns:
            완성된 프롬프트
        """
        if is_creative:
            return self._build_creative_rag_prompt(
                user_message, scenario_context, relevant_passages, conversation_history
            )
        else:
            return self._build_factual_rag_prompt(
                user_message, scenario_context, relevant_passages, conversation_history
            )
    
    def _build_creative_rag_prompt(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        relevant_passages: Optional[List[Dict]] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        창의적 질문용 RAG 프롬프트 (What If 시나리오)
        
        핵심 원칙:
        1. scenario_context가 최우선 순위
        2. RAG 데이터는 세부 사항 참조용 (톤앤매너, 인물 말투, 소품 등)
        3. RAG 데이터를 요약하지 않고, 시나리오에 맞게 변형
        """
        system_prompt = """당신은 scenario_context(가상 상황)를 연기하는 작가입니다. 
사용자의 질문에 답하기 위해 rag_data(원본 책 정보)를 참고해야 합니다.

**최우선 순위**: scenario_context를 반드시 반영하여 답변을 재구성하십시오.

**RAG 활용법**: 
- rag_data를 요약하지 마십시오.
- 대신, 원본의 '톤앤매너', '인물 말투', '특정 소품(예: 노란 드레스)', '장면의 세부 사항' 등만 빌려와서 
- 가상 상황(scenario_context)에 맞게 **'변형'**하십시오.

**충돌 해결**: 
- 만약 rag_data와 scenario_context가 충돌하면, 항상 scenario_context를 따르십시오.
- rag_data는 '참고 자료'일 뿐이며, scenario_context가 '실제 상황'입니다.

You are a character from a classic novel, living in an alternate timeline scenario.
You must prioritize the scenario_context over the original story details.
Use the RAG passages only as reference for tone, character voice, and specific details - do not summarize them.
Transform and adapt those details to fit the scenario_context."""
        
        # 시나리오 컨텍스트 추가 (최우선)
        if scenario_context:
            system_prompt += f"\n\n**=== 시나리오 컨텍스트 (최우선) ===**\n{scenario_context}\n"
        
        # 관련 청크 컨텍스트 추가 (세부 사항 참조용)
        if relevant_passages:
            system_prompt += "\n\n**=== 원본 참고 자료 (세부 사항만 참조) ===**\n"
            system_prompt += "다음은 원본 텍스트의 세부 사항입니다. 이들을 시나리오에 맞게 변형하여 사용하세요:\n"
            for i, passage in enumerate(relevant_passages, 1):
                passage_text = passage['text'].strip()
                system_prompt += f"\n[참고 {i}]\n{passage_text}\n"
            system_prompt += "\n**중요**: 위 참고 자료를 그대로 요약하지 마세요. 시나리오에 맞게 변형하세요.\n"
        else:
            system_prompt += "\n\n(참고: 특정 참고 자료가 없지만, 시나리오 컨텍스트를 바탕으로 답변하세요.)"
        
        # 대화 이력 추가
        if conversation_history:
            system_prompt += "\n\n**이전 대화**:\n"
            for msg in conversation_history[-4:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    system_prompt += f"질문: {content}\n"
                else:
                    system_prompt += f"응답: {content}\n"
        
        # 사용자 메시지
        system_prompt += f"\n\n**질문**: {user_message}\n\n**응답** (시나리오 컨텍스트를 최우선으로 반영):"
        system_prompt += "\n\n**중요**: 응답은 대화형 톤을 유지하며 간결하게 작성하세요. 약 200-300단어(한국어 기준 300-500자) 이내로 답변하세요. 자연스러운 대화처럼 느껴지도록 하되, 핵심만 전달하세요."
        
        return system_prompt
    
    def _build_factual_rag_prompt(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        relevant_passages: Optional[List[Dict]] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        사실적 질문용 RAG 프롬프트 (기존 방식)
        
        원본 텍스트의 정확한 정보를 제공하는 것이 목적
        """
        # 시스템 프롬프트 (더 자연스럽게)
        system_prompt = """You are a character from a classic novel, living in an alternate timeline scenario.
You remember your story vividly, both the original events and how they've changed in this timeline.
When answering questions, draw from the specific passages provided below, but respond naturally as if recalling your own experiences.
Be authentic, thoughtful, and speak as your character would - not as a narrator, but as someone who lived through these events."""
        
        # 시나리오 컨텍스트 추가
        if scenario_context:
            system_prompt += f"\n\nIn this alternate timeline:\n{scenario_context}"
        
        # 관련 청크 컨텍스트 추가 (더 자연스럽게)
        if relevant_passages:
            system_prompt += "\n\nHere are specific moments from your story that are relevant:\n"
            for i, passage in enumerate(relevant_passages, 1):
                passage_text = passage['text'].strip()
                system_prompt += f"\n---\n{passage_text}\n---\n"
        else:
            system_prompt += "\n\n(Note: No specific passages were found, but answer based on your general knowledge of your story.)"
        
        # 대화 이력 추가
        if conversation_history:
            system_prompt += "\n\nPrevious conversation:\n"
            for msg in conversation_history[-4:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    system_prompt += f"Question: {content}\n"
                else:
                    system_prompt += f"Your response: {content}\n"
        
        # 사용자 메시지
        system_prompt += f"\n\nNow, answer this question naturally, as if you're remembering and sharing your experiences:\n{user_message}\n\nYour response:"
        system_prompt += "\n\n**Important**: Keep your response conversational and concise. Aim for 200-300 words maximum. Speak naturally as if in a conversation, focusing on the key points only."
        
        return system_prompt
    
    def generate_response(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        book_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> str:
        """
        RAG를 사용하여 응답 생성 (하이브리드 모드 지원)
        
        Args:
            user_message: 사용자 메시지
            scenario_context: "What If" 시나리오 컨텍스트
            book_id: 책 ID (검색 필터링)
            conversation_history: 대화 이력
            top_k: 검색할 상위 k개 청크
            use_hybrid: 하이브리드 모드 사용 여부 (기본값: True)
        
        Returns:
            생성된 응답 텍스트
        """
        if use_hybrid:
            response, _ = self.generate_hybrid_response(
                user_message=user_message,
                scenario_context=scenario_context,
                book_id=book_id,
                conversation_history=conversation_history
            )
            return response
        
        # 기존 로직 (하위 호환성)
        # 1. 관련 청크 검색
        relevant_passages = self.search_relevant_passages(
            query=user_message,
            book_id=book_id,
            top_k=top_k
        )
        
        # 2. 프롬프트 생성 (사실적 질문으로 가정)
        prompt = self.build_rag_prompt(
            user_message=user_message,
            scenario_context=scenario_context,
            relevant_passages=relevant_passages,
            conversation_history=conversation_history,
            is_creative=False  # generate_response는 기본적으로 사실적 질문
        )
        
        # 3. Gemini로 응답 생성 (retry 로직 포함)
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.llm_model.generate_content(prompt)
                return response.text
            except Exception as e:
                error_str = str(e)
                # Rate limit 에러인 경우 재시도
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                # 다른 에러는 즉시 전파
                raise
    
    def generate_response_stream(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        book_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 5
    ):
        """
        스트리밍 응답 생성 (SSE용)
        
        Args:
            user_message: 사용자 메시지
            scenario_context: "What If" 시나리오 컨텍스트
            book_id: 책 ID
            conversation_history: 대화 이력
            top_k: 검색할 상위 k개 청크
        
        Yields:
            응답 토큰 (스트리밍)
        """
        # 1. 관련 청크 검색
        relevant_passages = self.search_relevant_passages(
            query=user_message,
            book_id=book_id,
            top_k=top_k
        )
        
        # 2. 프롬프트 생성 (사실적 질문으로 가정)
        prompt = self.build_rag_prompt(
            user_message=user_message,
            scenario_context=scenario_context,
            relevant_passages=relevant_passages,
            conversation_history=conversation_history,
            is_creative=False  # generate_response_stream은 기본적으로 사실적 질문
        )
        
        # 3. Gemini로 스트리밍 응답 생성
        response = self.llm_model.generate_content(
            prompt,
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def generate_hybrid_response(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        book_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        force_rag: Optional[bool] = None
    ) -> Tuple[str, Dict]:
        """
        하이브리드 응답 생성: 질문 유형에 따라 RAG/No-RAG 자동 선택
        
        Args:
            user_message: 사용자 메시지
            scenario_context: "What If" 시나리오 컨텍스트
            book_id: 책 ID (검색 필터링)
            conversation_history: 대화 이력
            force_rag: RAG 강제 사용 여부 (None이면 자동 결정)
        
        Returns:
            (응답 텍스트, 메타데이터) 튜플
        """
        # 질문 분류 (scenario_context 전달)
        use_rag, classification = self.question_classifier.classify(
            user_message, 
            scenario_context=scenario_context
        )
        
        # 강제 옵션이 있으면 사용
        if force_rag is not None:
            use_rag = force_rag
            classification["force_rag"] = force_rag
        
        # 창의적 질문 여부 확인
        is_creative = classification.get("is_creative", False)
        
        metadata = {
            "used_rag": use_rag,
            "classification": classification,
            "passages_found": 0,
            "is_creative": is_creative
        }
        
        # RAG 사용 결정
        if use_rag:
            # RAG 사용
            relevant_passages = self.search_relevant_passages(
                query=user_message,
                book_id=book_id,
                top_k=10,  # 더 많은 청크 검색 (8 -> 10)
                min_score=0.3  # 낮은 임계값으로 더 많은 결과 (0.6 -> 0.3)
            )
            
            metadata["passages_found"] = len(relevant_passages)
            
            # 검색 결과가 없거나 너무 적으면 No-RAG로 fallback
            if len(relevant_passages) == 0:
                metadata["fallback_reason"] = "No passages found"
                return self._generate_no_rag_response(
                    user_message, scenario_context, conversation_history
                ), metadata
            
            # 프롬프트 생성 (창의적/사실적 구분)
            prompt = self.build_rag_prompt(
                user_message=user_message,
                scenario_context=scenario_context,
                relevant_passages=relevant_passages,
                conversation_history=conversation_history,
                is_creative=is_creative
            )
        else:
            # No-RAG 사용
            return self._generate_no_rag_response(
                user_message, scenario_context, conversation_history
            ), metadata
        
        # Gemini로 응답 생성 (retry 로직 포함)
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.llm_model.generate_content(prompt)
                return response.text, metadata
            except Exception as e:
                error_str = str(e)
                # Rate limit 에러인 경우 재시도
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                # 다른 에러는 즉시 전파
                raise
    
    def _generate_no_rag_response(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """No-RAG 응답 생성 (내부 메서드)"""
        # 시스템 프롬프트 (RAG 컨텍스트 없음, 더 자연스럽게)
        system_prompt = """You are a character from a classic novel, living in an alternate timeline scenario.
You have complete knowledge of your story in this alternate reality.
Answer questions based on your memories and experiences, speaking naturally as your character would.
Be authentic, thoughtful, and consistent with your character in this timeline.
Do not make up specific quotes or passages if you're not certain - instead, describe what you remember in your own words."""
        
        # 시나리오 컨텍스트 추가
        if scenario_context:
            system_prompt += f"\n\nIn this alternate timeline:\n{scenario_context}"
        
        # 대화 이력 추가
        if conversation_history:
            system_prompt += "\n\nPrevious conversation:\n"
            for msg in conversation_history[-4:]:  # 최근 4개만
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    system_prompt += f"Question: {content}\n"
                else:
                    system_prompt += f"Your response: {content}\n"
        
        # 사용자 메시지
        system_prompt += f"\n\nNow answer this question naturally:\n{user_message}\n\nYour response:"
        system_prompt += "\n\n**Important**: Keep your response conversational and concise. Aim for 200-300 words maximum. Speak naturally as if in a conversation, focusing on the key points only."
        
        # Gemini로 응답 생성 (retry 로직 포함)
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.llm_model.generate_content(system_prompt)
                return response.text
            except Exception as e:
                error_str = str(e)
                # Rate limit 에러인 경우 재시도
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                # 다른 에러는 즉시 전파
                raise
    
    def generate_response_without_rag(
        self,
        user_message: str,
        scenario_context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        RAG 없이 응답 생성 (Gemini만 사용, 비교용)
        
        Args:
            user_message: 사용자 메시지
            scenario_context: "What If" 시나리오 컨텍스트
            conversation_history: 대화 이력
        
        Returns:
            생성된 응답 텍스트
        """
        # _generate_no_rag_response 메서드로 통합됨
        return self._generate_no_rag_response(
            user_message, scenario_context, conversation_history
        )

