"""
Middleware package

Story 0.6: Inter-Service Health Check & API Contract
"""

from app.middleware.correlation_id import CorrelationIdMiddleware, get_correlation_id, CORRELATION_ID_HEADER

__all__ = ["CorrelationIdMiddleware", "get_correlation_id", "CORRELATION_ID_HEADER"]
