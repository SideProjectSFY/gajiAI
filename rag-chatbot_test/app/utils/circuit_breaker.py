"""
Circuit Breaker Pattern for VectorDB

TECH-001 Fix: VectorDB fallback with circuit breaker
Prevents cascading failures when VectorDB is unavailable
"""

from enum import Enum
from datetime import datetime, timedelta
import structlog
from typing import Optional, Callable, Any
import asyncio

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for VectorDB operations
    
    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Too many failures, use fallback
    - HALF_OPEN: Testing if service recovered
    
    Configuration:
    - failure_threshold: 5 failures to open circuit
    - timeout: 60 seconds before trying half_open
    - success_threshold: 2 successes to close circuit
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.now()
        
        logger.info(
            "circuit_breaker_initialized",
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds,
            success_threshold=success_threshold
        )
    
    async def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            fallback: Fallback function if circuit is open
            *args, **kwargs: Arguments for func
        
        Returns:
            Result from func or fallback
        
        Raises:
            Exception if circuit is open and no fallback provided
        """
        
        # Check if circuit should transition to half_open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                # Circuit still open, use fallback
                logger.warning(
                    "circuit_breaker_open",
                    failures=self.failure_count,
                    time_since_last_failure=(
                        datetime.now() - self.last_failure_time
                    ).total_seconds() if self.last_failure_time else None
                )
                if fallback:
                    logger.info("circuit_breaker_using_fallback")
                    return await self._execute_fallback(fallback, *args, **kwargs)
                else:
                    raise Exception("Circuit breaker is OPEN and no fallback provided")
        
        # Try to execute function
        try:
            result = await self._execute(func, *args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            logger.error(
                "circuit_breaker_call_failed",
                error=str(e),
                state=self.state,
                failure_count=self.failure_count
            )
            
            # Use fallback if circuit is now open
            if self.state == CircuitState.OPEN and fallback:
                logger.info("circuit_breaker_fallback_after_failure")
                return await self._execute_fallback(fallback, *args, **kwargs)
            
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try half_open"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure >= self.timeout
    
    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN"""
        logger.info(
            "circuit_breaker_half_open",
            previous_state=self.state,
            time_in_open=(datetime.now() - self.last_state_change).total_seconds()
        )
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.now()
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                "circuit_breaker_success_in_half_open",
                success_count=self.success_count,
                threshold=self.success_threshold
            )
            
            if self.success_count >= self.success_threshold:
                # Close the circuit
                logger.info("circuit_breaker_closed", previous_failures=self.failure_count)
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = datetime.now()
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            if self.failure_count > 0:
                logger.debug("circuit_breaker_failure_count_reset")
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        logger.warning(
            "circuit_breaker_failure",
            state=self.state,
            failure_count=self.failure_count,
            threshold=self.failure_threshold
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test, reopen circuit
            logger.warning("circuit_breaker_reopened_from_half_open")
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.last_state_change = datetime.now()
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                # Open the circuit
                logger.error(
                    "circuit_breaker_opened",
                    failures=self.failure_count,
                    threshold=self.failure_threshold
                )
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()
    
    async def _execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function (async or sync)"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def _execute_fallback(self, fallback: Callable, *args, **kwargs) -> Any:
        """Execute fallback function (async or sync)"""
        if asyncio.iscoroutinefunction(fallback):
            return await fallback(*args, **kwargs)
        else:
            return fallback(*args, **kwargs)
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "time_in_current_state": (datetime.now() - self.last_state_change).total_seconds()
        }
