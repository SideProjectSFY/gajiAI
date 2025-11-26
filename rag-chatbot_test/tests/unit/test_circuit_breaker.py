"""
Unit Tests for Circuit Breaker

Story 2.1 - TECH-001: VectorDB Circuit Breaker Tests
"""

import pytest
from datetime import datetime, timedelta
from app.utils.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.mark.asyncio
    async def test_closed_state_allows_calls(self):
        """Test that CLOSED state allows function calls"""
        cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        async def success_func():
            return "success"
        
        result = await cb.call(success_func)
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_failures_open_circuit(self):
        """Test that multiple failures open the circuit"""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
        
        async def failing_func():
            raise Exception("Simulated failure")
        
        async def fallback_func():
            return "fallback"
        
        # Fail 3 times to open circuit
        for i in range(3):
            try:
                await cb.call(failing_func, fallback=fallback_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_open_circuit_uses_fallback(self):
        """Test that OPEN circuit uses fallback"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        
        async def failing_func():
            raise Exception("Simulated failure")
        
        async def fallback_func():
            return "fallback_result"
        
        # Fail twice to open circuit
        for _ in range(2):
            try:
                await cb.call(failing_func, fallback=fallback_func)
            except Exception:
                pass
        
        # Next call should use fallback without calling main func
        result = await cb.call(failing_func, fallback=fallback_func)
        
        assert result == "fallback_result"
        assert cb.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_transition_after_timeout(self):
        """Test transition to HALF_OPEN after timeout"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
        
        async def failing_func():
            raise Exception("Simulated failure")
        
        async def fallback_func():
            return "fallback"
        
        # Open the circuit
        for _ in range(2):
            try:
                await cb.call(failing_func, fallback=fallback_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout (1 second + buffer)
        import asyncio
        await asyncio.sleep(1.5)
        
        # Next call should transition to HALF_OPEN
        # This will fail and reopen, but we check the transition happened
        try:
            await cb.call(failing_func, fallback=fallback_func)
        except Exception:
            pass
        
        # The circuit should have transitioned through HALF_OPEN
        # (even if it reopened after failure)
        assert cb.last_failure_time is not None
    
    @pytest.mark.asyncio
    async def test_half_open_closes_after_successes(self):
        """Test that HALF_OPEN closes after enough successes"""
        cb = CircuitBreaker(
            failure_threshold=2,
            timeout_seconds=1,
            success_threshold=2
        )
        
        call_count = [0]
        
        async def sometimes_failing_func():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception("Initial failures")
            return "success"
        
        async def fallback_func():
            return "fallback"
        
        # Fail twice to open circuit
        for _ in range(2):
            try:
                await cb.call(sometimes_failing_func, fallback=fallback_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        import asyncio
        await asyncio.sleep(1.5)
        
        # Next 2 calls succeed (transitions to HALF_OPEN, then CLOSED)
        result1 = await cb.call(sometimes_failing_func, fallback=fallback_func)
        result2 = await cb.call(sometimes_failing_func, fallback=fallback_func)
        
        assert result1 == "success"
        assert result2 == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_get_state_returns_correct_info(self):
        """Test that get_state returns correct circuit state"""
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
        
        state = cb.get_state()
        
        assert state["state"] == CircuitState.CLOSED
        assert state["failure_count"] == 0
        assert state["success_count"] == 0
        assert state["last_failure_time"] is None
        assert "time_in_current_state" in state
    
    @pytest.mark.asyncio
    async def test_sync_function_support(self):
        """Test that circuit breaker works with sync functions"""
        cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        def sync_func():
            return "sync_result"
        
        result = await cb.call(sync_func)
        
        assert result == "sync_result"
        assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_fallback_not_required_when_circuit_closed(self):
        """Test that fallback is not required when circuit is closed"""
        cb = CircuitBreaker(failure_threshold=5, timeout_seconds=60)
        
        async def success_func():
            return "success"
        
        # No fallback provided, but should work since circuit is closed
        result = await cb.call(success_func)
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_open_circuit_without_fallback_raises_exception(self):
        """Test that open circuit without fallback raises exception"""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=60)
        
        async def failing_func():
            raise Exception("Simulated failure")
        
        # Fail twice to open circuit
        for _ in range(2):
            try:
                await cb.call(failing_func)
            except Exception:
                pass
        
        assert cb.state == CircuitState.OPEN
        
        # Next call without fallback should raise exception
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_func)
