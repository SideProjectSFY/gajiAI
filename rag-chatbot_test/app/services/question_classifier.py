"""
질문 분류기

질문 유형을 분석하여 RAG 사용 여부 및 질문 의도(창의적/사실적)를 결정합니다.
"""

import re
from typing import Dict, Tuple, Optional


class QuestionClassifier:
    """질문 유형을 분류하여 RAG 필요 여부 및 질문 의도를 판단"""
    
    # RAG가 필요한 키워드 (구체적 인용/장면 요구)
    RAG_KEYWORDS = [
        "quote", "quoted", "exact words", "what did", "what said",
        "chapter", "scene", "describe the", "what happened at",
        "specific", "precise", "exact", "where does", "when did",
        "compare", "contrast", "dialogue", "conversation"
    ]
    
    # RAG가 불필요한 키워드 (일반 주제/해석)
    NO_RAG_KEYWORDS = [
        "theme", "main idea", "what is", "who is", "explain",
        "meaning", "symbolize", "represent", "significance",
        "why", "how does", "what does it mean"
    ]
    
    # What If 질문 키워드 (창의적 질문)
    WHAT_IF_KEYWORDS = [
        "what if", "만약", "if", "suppose", "imagine",
        "alternate", "alternative", "different", "changed"
    ]
    
    def __init__(self):
        """질문 분류기 초기화"""
        # 키워드 정규식 컴파일
        self.rag_pattern = re.compile(
            "|".join([f"\\b{kw}\\b" for kw in self.RAG_KEYWORDS]),
            re.IGNORECASE
        )
        self.no_rag_pattern = re.compile(
            "|".join([f"\\b{kw}\\b" for kw in self.NO_RAG_KEYWORDS]),
            re.IGNORECASE
        )
        self.what_if_pattern = re.compile(
            "|".join([f"\\b{kw}\\b" for kw in self.WHAT_IF_KEYWORDS]),
            re.IGNORECASE
        )
    
    def classify(
        self, 
        question: str, 
        scenario_context: Optional[str] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        질문을 분류하여 RAG 사용 여부 및 질문 의도 결정
        
        Args:
            question: 사용자 질문
            scenario_context: 시나리오 컨텍스트 (What If 질문 판단용)
        
        Returns:
            (use_rag: bool, metadata: dict) 튜플
            metadata에는 다음이 포함됨:
            - use_rag: RAG 사용 여부
            - is_creative: 창의적 질문 여부 (What If)
            - is_factual: 사실적 질문 여부
            - confidence: 분류 신뢰도
            - reason: 분류 이유
        """
        question_lower = question.lower()
        
        # 1단계: What If 질문인지 판단 (창의적 질문)
        has_scenario = scenario_context is not None and scenario_context.strip() != ""
        has_what_if_keyword = bool(self.what_if_pattern.search(question_lower))
        is_creative = has_scenario or has_what_if_keyword
        
        # RAG 필요 키워드 점수
        rag_score = len(self.rag_pattern.findall(question_lower))
        
        # RAG 불필요 키워드 점수
        no_rag_score = len(self.no_rag_pattern.findall(question_lower))
        
        # 질문 길이 (긴 질문은 더 구체적일 가능성)
        question_length = len(question.split())
        
        # 결정 로직
        use_rag = False
        confidence = 0.5
        reason = ""
        
        # 창의적 질문인 경우: RAG는 세부 사항 참조용으로 사용 (항상 사용)
        if is_creative:
            use_rag = True
            confidence = 0.9
            if has_scenario:
                reason = "시나리오 컨텍스트 존재 - 창의적 질문 (RAG는 세부 사항 참조용)"
            else:
                reason = "What If 키워드 발견 - 창의적 질문 (RAG는 세부 사항 참조용)"
        # 사실적 질문인 경우: 기존 로직 사용
        else:
            if rag_score > no_rag_score:
                use_rag = True
                confidence = min(0.9, 0.5 + (rag_score - no_rag_score) * 0.1)
                reason = f"사실적 질문 - RAG 키워드 {rag_score}개 발견"
            elif no_rag_score > rag_score:
                use_rag = False
                confidence = min(0.9, 0.5 + (no_rag_score - rag_score) * 0.1)
                reason = f"사실적 질문 - 일반 키워드 {no_rag_score}개 발견"
            else:
                # 동점인 경우 질문 길이와 특정 패턴으로 판단
                if question_length > 15 or "?" in question:
                    # 긴 질문이거나 여러 질문은 구체적일 가능성
                    use_rag = True
                    confidence = 0.6
                    reason = "사실적 질문 - 긴 질문 또는 복합 질문"
                else:
                    # 짧은 일반 질문
                    use_rag = False
                    confidence = 0.6
                    reason = "사실적 질문 - 짧은 일반 질문"
        
        return use_rag, {
            "use_rag": use_rag,
            "is_creative": is_creative,
            "is_factual": not is_creative,
            "confidence": confidence,
            "reason": reason,
            "rag_score": rag_score,
            "no_rag_score": no_rag_score,
            "question_length": question_length,
            "has_scenario": has_scenario,
            "has_what_if_keyword": has_what_if_keyword
        }

