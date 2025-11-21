"""
Redis Utilities

Long Polling 및 Task 결과 저장
Updated for redis >= 5.2.1
Redis is now OPTIONAL - falls back to no-op cache if unavailable
"""

import json
from typing import Optional, Dict
import structlog

from app.config import settings

logger = structlog.get_logger()

# Try to import redis, but make it optional
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis_not_installed", message="Redis package not installed. Using no-op cache.")


class RedisClient:
    """Redis 클라이언트 - redis 5.2.1+ compatible (optional)"""
    
    def __init__(self):
        self.client = None
        self.is_available = False
        
        if not REDIS_AVAILABLE:
            logger.warning("redis_unavailable", message="Redis package not available")
            return
            
        try:
            self.client = redis.from_url(
                settings.redis_url, 
                decode_responses=True,
                protocol=3  # Redis 5.2.1+ 권장 프로토콜
            )
            self.is_available = True
            logger.info("redis_client_initialized", url=settings.redis_url, version="5.2.1+")
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e), message="Falling back to no-op cache")
            self.is_available = False
    
    async def store_task_result(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        ttl: int = 600
    ):
        """
        작업 결과 저장 (Long Polling용)
        
        Args:
            task_id: 작업 ID
            status: 상태 (processing|completed|failed)
            result: 결과 데이터
            error: 에러 메시지
            ttl: TTL (초, 기본 600초)
        """
        if not self.is_available:
            logger.debug("redis_unavailable", task_id=task_id, message="No-op: Redis not available")
            return
            
        try:
            data = {
                "status": status,
                "result": result,
                "error": error
            }
            
            await self.client.setex(
                f"task:{task_id}",
                ttl,
                json.dumps(data)
            )
            
            logger.info("task_result_stored", task_id=task_id, status=status)
        except Exception as e:
            logger.error("redis_store_error", error=str(e), task_id=task_id)
            # Don't raise - fall back gracefully
            logger.warning("redis_operation_failed", task_id=task_id, operation="store")
    
    async def get_task_status(self, task_id: str) -> Dict:
        """
        작업 상태 조회
        
        Args:
            task_id: 작업 ID
        
        Returns:
            작업 상태 딕셔너리
        """
        if not self.is_available:
            logger.debug("redis_unavailable", task_id=task_id, message="No-op: Redis not available")
            return {
                "status": "not_found",
                "result": None,
                "error": "Redis not available - task status tracking disabled"
            }
            
        try:
            data = await self.client.get(f"task:{task_id}")
            
            if not data:
                return {
                    "status": "not_found",
                    "result": None,
                    "error": "Task expired or not found"
                }
            
            return json.loads(data)
        except Exception as e:
            logger.error("redis_get_error", error=str(e), task_id=task_id)
            return {
                "status": "error",
                "result": None,
                "error": str(e)
            }
    
    async def close(self):
        """연결 종료"""
        if self.is_available and self.client:
            await self.client.close()


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Redis 클라이언트 싱글톤"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
