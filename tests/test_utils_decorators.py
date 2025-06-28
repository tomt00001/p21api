"""Tests for utility decorators and helpers."""

import time
from unittest.mock import Mock

import pytest
from p21api.utils import CircuitBreaker, rate_limit, retry_on_failure


class TestRetryOnFailure:
    """Test the retry_on_failure decorator."""

    def test_success_on_first_try(self):
        """Test function succeeds on first attempt."""
        mock_func = Mock(return_value="success")
        decorated = retry_on_failure()(mock_func)

        result = decorated()

        assert result == "success"
        mock_func.assert_called_once()

    def test_success_after_retries(self):
        """Test function succeeds after some retries."""
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        decorated = retry_on_failure(max_retries=3, delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_failure_after_max_retries(self):
        """Test function fails after exhausting retries."""
        mock_func = Mock(side_effect=Exception("persistent failure"))
        decorated = retry_on_failure(max_retries=2, delay=0.01)(mock_func)

        with pytest.raises(Exception, match="persistent failure"):
            decorated()

        assert mock_func.call_count == 3  # Initial + 2 retries


class TestRateLimit:
    """Test the rate_limit decorator."""

    def test_rate_limiting_timing(self):
        """Test that rate limiting enforces timing constraints."""
        mock_func = Mock(return_value="result")
        decorated = rate_limit(calls_per_second=10.0)(mock_func)  # 0.1s between calls

        start_time = time.time()
        decorated()
        decorated()
        end_time = time.time()

        # Should take at least 0.1 seconds for two calls
        assert end_time - start_time >= 0.09  # Small tolerance for timing
        assert mock_func.call_count == 2


class TestCircuitBreaker:
    """Test the CircuitBreaker class."""

    def test_closed_state_normal_operation(self):
        """Test normal operation in CLOSED state."""
        mock_func = Mock(return_value="success")
        breaker = CircuitBreaker(failure_threshold=3)
        decorated = breaker(mock_func)

        result = decorated()

        assert result == "success"
        mock_func.assert_called_once()

    def test_opens_after_threshold_failures(self):
        """Test circuit opens after reaching failure threshold."""
        mock_func = Mock(side_effect=Exception("failure"))
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        decorated = breaker(mock_func)

        # First two calls should execute and fail
        with pytest.raises(Exception):
            decorated()
        with pytest.raises(Exception):
            decorated()

        # Third call should fail fast due to open circuit
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            decorated()

        assert mock_func.call_count == 2

    def test_half_open_state_on_recovery(self):
        """Test circuit moves to HALF_OPEN state after recovery timeout."""
        call_count = 0

        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("failure")
            return "success"

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)
        decorated = breaker(test_func)

        # Trigger failures to open circuit
        with pytest.raises(Exception):
            decorated()
        with pytest.raises(Exception):
            decorated()

        # Wait for recovery timeout
        time.sleep(0.02)

        # Next call should succeed and reset the circuit
        result = decorated()
        assert result == "success"

        # Verify the circuit is now closed and working normally
        result = decorated()
        assert result == "success"

    def test_retry_with_no_exception_raised(self):
        """Test retry decorator when no exception is raised."""
        mock_func = Mock(return_value="success")
        decorated = retry_on_failure(max_retries=3)(mock_func)

        result = decorated()

        assert result == "success"
        mock_func.assert_called_once()

    def test_retry_with_none_last_exception(self):
        """Test retry decorator edge case with None last_exception."""
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Test error")
            return "success"

        decorated = retry_on_failure(max_retries=3, delay=0.001)(failing_func)
        result = decorated()

        assert result == "success"
        assert call_count == 3

    def test_circuit_breaker_should_attempt_reset_no_last_failure(self):
        """Test circuit breaker reset logic when no previous failure."""
        breaker = CircuitBreaker(failure_threshold=2)
        # Manually set state to test internal method
        breaker._state = "OPEN"
        breaker._last_failure_time = None

        # Should attempt reset when no last failure time
        assert breaker._should_attempt_reset() is True
