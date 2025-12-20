from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from app.config.settings import settings
import structlog

logger = structlog.get_logger()

security = HTTPBearer(auto_error=False)

class JWTAuth:
    """JWT 인증 미들웨어"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
    
    def decode_token(self, token: str) -> Optional[dict]:
        """JWT 토큰 검증 및 디코드"""
        try:
            allowed_algorithms = ["HS256", "HS384", "HS512"]
            if self.algorithm not in allowed_algorithms:
                logger.warning("jwt_algorithm_not_supported", algorithm=self.algorithm)
                return None
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=allowed_algorithms
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("jwt_expired", token=token[:20])
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("jwt_invalid", error=str(e), token=token[:20])
            return None
    
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """FastAPI Dependency로 사용"""
        # DEBUG: Log all headers and credentials
        auth_header = request.headers.get("Authorization", "")
        logger.info(
            "jwt_auth_called",
            path=request.url.path,
            has_credentials=credentials is not None,
            auth_header_present=bool(auth_header),
            auth_header_prefix=auth_header[:50] if auth_header else "None",
            all_headers=dict(request.headers)
        )
        
        if not credentials:
            logger.warning("jwt_auth_no_credentials", path=request.url.path)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )
        
        payload = self.decode_token(credentials.credentials)
        if not payload:
            logger.warning("jwt_auth_decode_failed", token_prefix=credentials.credentials[:30])
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        logger.info("jwt_auth_success", user_id=payload.get("sub"))
        request.state.user = payload
        return payload

jwt_auth = JWTAuth()

def get_current_user(request: Request) -> dict:
    """현재 인증된 사용자 정보 반환"""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user

def get_jwt_token(request: Request) -> str:
    """요청에서 JWT 토큰 추출"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing JWT token"
        )
    return auth_header.split(" ", 1)[1]

