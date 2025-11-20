"""
Gemini API Key Manager

여러 API 키를 관리하고, 할당량 초과 시 자동으로 다음 키로 전환합니다.
"""

import os
import time
from typing import List, Optional
from dotenv import load_dotenv


class APIKeyManager:
    """API 키 관리 및 자동 로테이션"""
    
    def __init__(self):
        """API 키 매니저 초기화"""
        # .env 파일 로드
        load_dotenv()
        
        # 모든 API 키 로드
        self.api_keys = self._load_api_keys()
        if not self.api_keys:
            raise ValueError("최소 하나의 GEMINI_API_KEY가 필요합니다.")
        
        # 현재 사용 중인 키 인덱스
        self.current_key_index = 0
        
        # 실패한 키 추적 (키: 실패 시간)
        self.failed_keys = {}
        
        # 실패한 키 재시도 대기 시간 (초)
        self.retry_delay = 300  # 5분
        
        # 초기 키 로그
        print(f"[OK] API 키 #{self.current_key_index + 1} 사용 중")
    
    def _load_api_keys(self) -> List[str]:
        """환경변수에서 모든 API 키 로드"""
        keys = []
        
        # 방법 1: GEMINI_API_KEYS (쉼표로 구분)
        keys_str = os.getenv("GEMINI_API_KEYS")
        if keys_str:
            keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        
        # 방법 2: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
        if not keys:
            i = 1
            while True:
                key = os.getenv(f"GEMINI_API_KEY_{i}")
                if not key:
                    break
                keys.append(key)
                i += 1
        
        # 방법 3: 레거시 단일 키 (GEMINI_API_KEY)
        if not keys:
            legacy_key = os.getenv("GEMINI_API_KEY")
            if legacy_key:
                keys.append(legacy_key)
        
        return keys
    
    def get_current_key(self) -> str:
        """현재 사용 중인 API 키 반환"""
        return self.api_keys[self.current_key_index]
    
    def _is_quota_error(self, error: Exception) -> bool:
        """할당량 초과 에러인지 확인"""
        error_str = str(error).lower()
        quota_keywords = [
            "429",
            "quota",
            "rate limit",
            "resource exhausted",
            "too many requests"
        ]
        return any(keyword in error_str for keyword in quota_keywords)
    
    def _get_next_available_key_index(self) -> Optional[int]:
        """사용 가능한 다음 키 인덱스 찾기"""
        current_time = time.time()
        
        # 모든 키를 순회하며 사용 가능한 키 찾기
        for i in range(len(self.api_keys)):
            next_index = (self.current_key_index + i + 1) % len(self.api_keys)
            
            # 실패한 키인지 확인
            if next_index in self.failed_keys:
                failed_time = self.failed_keys[next_index]
                # 재시도 대기 시간이 지났는지 확인
                if current_time - failed_time < self.retry_delay:
                    continue
                else:
                    # 대기 시간이 지났으면 실패 기록 제거
                    del self.failed_keys[next_index]
            
            return next_index
        
        return None
    
    def switch_to_next_key(self) -> bool:
        """다음 사용 가능한 키로 전환
        
        Returns:
            성공 여부 (True: 전환 성공, False: 사용 가능한 키 없음)
        """
        next_index = self._get_next_available_key_index()
        
        if next_index is None:
            print("[ERROR] 사용 가능한 API 키가 없습니다. 모든 키가 할당량을 초과했습니다.")
            return False
        
        # 현재 키를 실패 목록에 추가
        self.failed_keys[self.current_key_index] = time.time()
        
        # 키 전환
        self.current_key_index = next_index
        print(f"[OK] API 키 #{self.current_key_index + 1}로 전환되었습니다.")
        return True
    
    def mark_key_failed(self, api_key: str):
        """특정 API 키를 실패로 표시하고 다음 키로 전환
        
        Args:
            api_key: 실패한 API 키
        """
        # 키 인덱스 찾기
        try:
            key_index = self.api_keys.index(api_key)
            self.failed_keys[key_index] = time.time()
            # 다음 키로 전환
            self.switch_to_next_key()
        except ValueError:
            print(f"[경고] 실패한 API 키를 찾을 수 없습니다.")
    
    def handle_api_error(self, error: Exception) -> bool:
        """API 에러 처리 및 키 전환
        
        Args:
            error: 발생한 에러
        
        Returns:
            키 전환 성공 여부
        """
        if self._is_quota_error(error):
            print(f"[WARNING] API 할당량 초과: {str(error)}")
            return self.switch_to_next_key()
        return False
    
    def execute_with_retry(self, func, *args, max_retries: int = None, **kwargs):
        """API 호출을 재시도하며 실행
        
        Args:
            func: 실행할 함수
            *args: 함수 인자
            max_retries: 최대 재시도 횟수 (None이면 모든 키 시도)
            **kwargs: 함수 키워드 인자
        
        Returns:
            함수 실행 결과
        
        Raises:
            마지막 에러 (모든 키 실패 시)
        """
        if max_retries is None:
            max_retries = len(self.api_keys)
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 함수 실행
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # 할당량 에러가 아니면 즉시 전파
                if not self._is_quota_error(e):
                    raise
                
                # 마지막 시도면 에러 전파
                if attempt >= max_retries - 1:
                    raise
                
                # 다음 키로 전환 시도
                if not self.switch_to_next_key():
                    raise Exception("모든 API 키의 할당량이 초과되었습니다.") from last_error
                
                # 잠시 대기 후 재시도
                time.sleep(1)
        
        # 모든 재시도 실패
        raise last_error
    
    def get_status(self) -> dict:
        """현재 API 키 상태 반환"""
        current_time = time.time()
        
        status = {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "failed_keys": [],
            "available_keys": []
        }
        
        for i in range(len(self.api_keys)):
            if i in self.failed_keys:
                failed_time = self.failed_keys[i]
                remaining_time = max(0, self.retry_delay - (current_time - failed_time))
                status["failed_keys"].append({
                    "index": i,
                    "retry_in_seconds": int(remaining_time)
                })
            else:
                status["available_keys"].append(i)
        
        return status


# 싱글톤 인스턴스
_api_key_manager = None


def get_api_key_manager() -> APIKeyManager:
    """API 키 매니저 싱글톤 인스턴스 반환"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


# 전역 인스턴스는 lazy initialization으로 변경 (import 시 블로킹 방지)
# 필요할 때 get_api_key_manager()를 호출하여 사용

