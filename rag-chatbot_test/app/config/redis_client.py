"""
Redis Client Configuration

Long Polling 및 Celery 브로커용 Redis 클라이언트
"""

import redis
import json
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# 전역 Redis 클라이언트 인스턴스
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Redis 클라이언트 싱글톤 반환
    
    Returns:
        redis.Redis: Redis 클라이언트 인스턴스
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                socket_timeout=settings.redis_socket_timeout,
                decode_responses=True,  # 문자열로 자동 디코딩
                health_check_interval=30  # 30초마다 연결 상태 확인
            )
            
            # 연결 테스트
            _redis_client.ping()
            logger.info(f"Redis 연결 성공: {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
            
        except redis.ConnectionError as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis 클라이언트 초기화 실패: {e}")
            raise
    
    return _redis_client


def close_redis_client():
    """Redis 클라이언트 연결 종료"""
    global _redis_client
    
    if _redis_client is not None:
        try:
            _redis_client.close()
            logger.info("Redis 연결 종료")
        except Exception as e:
            logger.error(f"Redis 연결 종료 실패: {e}")
        finally:
            _redis_client = None


# Task Status 관리 함수들 (Long Polling용)

def set_task_status(
    task_id: str,
    status: str,
    progress: int = 0,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    task_type: Optional[str] = None,
    user_id: Optional[str] = None,
    result_data: Optional[dict] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    비동기 작업 상태를 Redis에 저장
    
    Args:
        task_id: 작업 ID
        status: 상태 ("PENDING", "IN_PROGRESS", "COMPLETED", "FAILED")
        progress: 진행률 (0-100)
        entity_id: 관련 엔티티 ID (예: conversation_id)
        entity_type: 엔티티 타입 (예: "conversation")
        task_type: 작업 타입 (예: "conversation_generation")
        user_id: 사용자 ID
        result_data: 결과 데이터 (dict)
        error_message: 에러 메시지 (실패 시)
    
    Returns:
        성공 여부
    """
    try:
        client = get_redis_client()
        
        import json
        from datetime import datetime
        
        task_data = {
            "status": status,
            "progress": progress,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if entity_id:
            task_data["entity_id"] = entity_id
        if entity_type:
            task_data["entity_type"] = entity_type
        if task_type:
            task_data["task_type"] = task_type
        if user_id:
            task_data["user_id"] = user_id
        if result_data:
            task_data["result_data"] = json.dumps(result_data)
        if error_message:
            task_data["error_message"] = error_message
        
        # Hash로 저장
        key = f"task:{task_id}"
        client.hset(key, mapping=task_data)
        
        # TTL 설정 (1시간)
        client.expire(key, 3600)
        
        logger.debug(f"Task status 저장: {task_id} -> {status} ({progress}%)")
        return True
        
    except Exception as e:
        logger.error(f"Task status 저장 실패 ({task_id}): {e}")
        return False


def get_task_status(task_id: str) -> Optional[dict]:
    """
    비동기 작업 상태 조회
    
    Args:
        task_id: 작업 ID
    
    Returns:
        작업 상태 정보 (dict) 또는 None
    """
    try:
        client = get_redis_client()
        key = f"task:{task_id}"
        
        task_data = client.hgetall(key)
        
        if not task_data:
            return None
        
        # result_data가 있으면 JSON 파싱
        if "result_data" in task_data and task_data["result_data"]:
            import json
            try:
                task_data["result_data"] = json.loads(task_data["result_data"])
            except json.JSONDecodeError:
                pass
        
        return task_data
        
    except Exception as e:
        logger.error(f"Task status 조회 실패 ({task_id}): {e}")
        return None


def update_task_progress(task_id: str, progress: int, status: Optional[str] = None) -> bool:
    """
    작업 진행률 업데이트
    
    Args:
        task_id: 작업 ID
        progress: 진행률 (0-100)
        status: 상태 (선택, 업데이트할 경우만)
    
    Returns:
        성공 여부
    """
    try:
        client = get_redis_client()
        key = f"task:{task_id}"
        
        from datetime import datetime
        
        updates = {
            "progress": progress,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if status:
            updates["status"] = status
        
        client.hset(key, mapping=updates)
        return True
        
    except Exception as e:
        logger.error(f"Task progress 업데이트 실패 ({task_id}): {e}")
        return False


def delete_task_status(task_id: str) -> bool:
    """
    작업 상태 삭제
    
    Args:
        task_id: 작업 ID
    
    Returns:
        성공 여부
    """
    try:
        client = get_redis_client()
        key = f"task:{task_id}"
        client.delete(key)
        logger.debug(f"Task status 삭제: {task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Task status 삭제 실패 ({task_id}): {e}")
        return False


# Temporary Conversation 관리 함수들 (임시 대화용)

def save_temp_conversation(conversation_id: str, conversation_data: dict, ttl: int = 3600) -> bool:
    """
    임시 대화를 Redis에 저장
    
    Args:
        conversation_id: 대화 ID
        conversation_data: 대화 데이터 (dict)
        ttl: TTL (초, 기본 1시간 = 3600초)
    
    Returns:
        성공 여부
    """
    try:
        import json as _json
        import os
        from datetime import datetime
        
        client = get_redis_client()
        key = f"temp_conv:{conversation_id}"
        
        # JSON 문자열로 저장
        json_str = json.dumps(conversation_data, ensure_ascii=False)
        result = client.setex(
            key,
            ttl,
            json_str
        )
        
        logger.debug(f"임시 대화 저장: {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"임시 대화 저장 실패 ({conversation_id}): {e}")
        return False


def get_temp_conversation(conversation_id: str) -> Optional[dict]:
    """
    임시 대화 조회
    
    Args:
        conversation_id: 대화 ID
    
    Returns:
        대화 데이터 (dict) 또는 None
    """
    try:
        client = get_redis_client()
        key = f"temp_conv:{conversation_id}"
        data = client.get(key)
        
        if not data:
            return None
        
        parsed_data = json.loads(data)
        return parsed_data
        
    except json.JSONDecodeError as e:
        logger.error(f"임시 대화 JSON 파싱 실패 ({conversation_id}): {e}")
        return None
    except Exception as e:
        logger.error(f"임시 대화 조회 실패 ({conversation_id}): {e}")
        return None


def delete_temp_conversation(conversation_id: str) -> bool:
    """
    임시 대화 삭제
    
    Args:
        conversation_id: 대화 ID
    
    Returns:
        성공 여부
    """
    try:
        client = get_redis_client()
        key = f"temp_conv:{conversation_id}"
        client.delete(key)
        logger.debug(f"임시 대화 삭제: {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"임시 대화 삭제 실패 ({conversation_id}): {e}")
        return False


def exists_temp_conversation(conversation_id: str) -> bool:
    """
    임시 대화 존재 여부 확인
    
    Args:
        conversation_id: 대화 ID
    
    Returns:
        존재 여부
    """
    try:
        client = get_redis_client()
        key = f"temp_conv:{conversation_id}"
        return client.exists(key) > 0
        
    except Exception as e:
        logger.error(f"임시 대화 존재 확인 실패 ({conversation_id}): {e}")
        return False
