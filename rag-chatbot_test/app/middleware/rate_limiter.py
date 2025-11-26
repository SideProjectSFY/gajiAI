"""
Rate Limiting Middleware

SEC-001 Fix: Rate limiting for sensitive endpoints
100 requests/minute per user
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
import time
from datetime import datetime, timedelta
import structlog
from typing import Optional

from app.config import settings

logger = structlog.get_logger()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window counter
    
    Limits:
    - /api/ai/adapt-prompt: 100 requests/minute per user
    - Other sensitive endpoints: 200 requests/minute per user
    """
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.enabled = redis_client is not None
        
        # Rate limits by endpoint pattern
        self.rate_limits = {
            "/api/ai/adapt-prompt": {"limit": 100, "window": 60},  # 100/min
            "/api/ai/": {"limit": 200, "window": 60},  # 200/min for other AI endpoints
        }
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit before processing request"""
        
        # Skip rate limiting if Redis not configured
        if not self.enabled:
            logger.warning("rate_limiter_disabled", reason="redis_not_configured")
            return await call_next(request)
        
        # Check if endpoint needs rate limiting
        rate_config = self._get_rate_config(request.url.path)
        if not rate_config:
            return await call_next(request)
        
        # Extract user identifier (IP or user_id from header)
        user_id = self._get_user_id(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(
            user_id,
            request.url.path,
            rate_config
        )
        
        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                user_id=user_id,
                path=request.url.path,
                limit=rate_config["limit"],
                window=rate_config["window"]
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {rate_config['limit']} requests per {rate_config['window']} seconds",
                    "remaining": 0,
                    "reset_at": reset_time.isoformat()
                },
                headers={
                    "X-RateLimit-Limit": str(rate_config["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time.timestamp())),
                    "Retry-After": str(rate_config["window"])
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_config["limit"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
        
        return response
    
    def _get_rate_config(self, path: str) -> Optional[dict]:
        """Get rate limit config for path"""
        # Exact match first
        if path in self.rate_limits:
            return self.rate_limits[path]
        
        # Prefix match
        for pattern, config in self.rate_limits.items():
            if path.startswith(pattern):
                return config
        
        return None
    
    def _get_user_id(self, request: Request) -> str:
        """
        Extract user identifier from request
        Priority: X-User-ID header > X-Forwarded-For > client IP
        """
        # Check for user ID in header (from Spring Boot auth)
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP from X-Forwarded-For chain
            ip = forwarded_for.split(",")[0].strip()
            return f"ip:{ip}"
        
        # Use direct client IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(
        self,
        user_id: str,
        path: str,
        rate_config: dict
    ) -> tuple[bool, int, datetime]:
        """
        Check rate limit using Redis sliding window counter
        
        Returns:
            (is_allowed, remaining_requests, reset_time)
        """
        limit = rate_config["limit"]
        window = rate_config["window"]
        
        # Redis key: rate_limit:{endpoint}:{user_id}
        redis_key = f"rate_limit:{path}:{user_id}"
        current_time = time.time()
        window_start = current_time - window
        
        try:
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(redis_key)
            
            # Add current request
            pipe.zadd(redis_key, {str(current_time): current_time})
            
            # Set expiry to prevent memory leak
            pipe.expire(redis_key, window + 10)
            
            results = await pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            is_allowed = current_count < limit
            remaining = max(0, limit - current_count - 1)
            reset_time = datetime.fromtimestamp(current_time + window)
            
            logger.debug(
                "rate_limit_check",
                user_id=user_id,
                path=path,
                current_count=current_count,
                limit=limit,
                remaining=remaining,
                is_allowed=is_allowed
            )
            
            return is_allowed, remaining, reset_time
            
        except Exception as e:
            logger.error("rate_limit_check_failed", error=str(e), user_id=user_id)
            # Fail open: allow request if Redis fails
            return True, limit, datetime.fromtimestamp(current_time + window)
