"""
Correlation ID Middleware

Story 0.6: Inter-Service Health Check & API Contract

Adds correlation ID support for distributed tracing:
- Reads X-Correlation-ID from incoming request header
- Generates new UUID if not present
- Adds to structlog context
- Returns in response header
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

CORRELATION_ID_HEADER = "X-Correlation-ID"

# Context variable for correlation ID
_correlation_id_ctx_var = None

def get_correlation_id() -> str:
    """Get current correlation ID from context"""
    global _correlation_id_ctx_var
    if _correlation_id_ctx_var:
        return _correlation_id_ctx_var
    return ""


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation ID propagation"""

    async def dispatch(self, request: Request, call_next) -> Response:
        global _correlation_id_ctx_var

        # Get or generate correlation ID
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in context
        _correlation_id_ctx_var = correlation_id

        # Bind to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Process request
        response = await call_next(request)

        # Add correlation ID to response header
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        # Clear context
        _correlation_id_ctx_var = None

        return response

