"""
Tests for retry module
"""

import pytest
import time
from unittest.mock import patch, MagicMock, call
import requests

from rubot.retry import retry_on_failure, exponential_backoff


class TestRetry:

    def test_retry_on_failure_success_first_try(self):
        """Test retry decorator when function succeeds on first try"""

        @retry_on_failure(max_retries=3)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_retry_on_failure_success_after_retries(self):
        """Test retry decorator when function succeeds after retries"""
        call_count = 0

        @retry_on_failure(
            max_retries=3, delay=0.01
        )  # Very short delay for testing
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.RequestException("Temporary error")
            return "success"

        result = test_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_on_failure_max_retries_exceeded(self):
        """Test retry decorator when max retries are exceeded"""

        @retry_on_failure(max_retries=2, delay=0.01)
        def test_function():
            raise requests.RequestException("Persistent error")

        with pytest.raises(
            requests.RequestException, match="Persistent error"
        ):
            test_function()

    def test_retry_on_failure_non_retryable_exception(self):
        """Test retry decorator with non-retryable exception"""

        @retry_on_failure(
            max_retries=3, exceptions=(requests.RequestException,)
        )
        def test_function():
            raise ValueError("Not retryable")

        with pytest.raises(ValueError, match="Not retryable"):
            test_function()

    def test_retry_on_failure_custom_exceptions(self):
        """Test retry decorator with custom exception types"""

        @retry_on_failure(
            max_retries=2, delay=0.01, exceptions=(ValueError, TypeError)
        )
        def test_function():
            raise ValueError("Custom error")

        with pytest.raises(ValueError, match="Custom error"):
            test_function()

    @patch("time.sleep")
    def test_retry_on_failure_backoff(self, mock_sleep):
        """Test retry decorator backoff timing"""
        call_count = 0

        @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 4:  # Fail on all 4 attempts (1 + 3 retries)
                raise requests.RequestException("Error")
            return "success"

        with pytest.raises(requests.RequestException):
            test_function()

        # Check that sleep was called with increasing delays
        expected_calls = [1.0, 2.0, 4.0]  # delay * backoff^attempt
        actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_calls == expected_calls

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff calculation"""

        # Test basic exponential growth
        assert exponential_backoff(0, 1.0) == 1.0
        assert exponential_backoff(1, 1.0) == 2.0
        assert exponential_backoff(2, 1.0) == 4.0
        assert exponential_backoff(3, 1.0) == 8.0

    def test_exponential_backoff_max_delay(self):
        """Test exponential backoff with maximum delay"""

        # Test that delay doesn't exceed maximum
        result = exponential_backoff(10, 1.0, max_delay=5.0)
        assert result == 5.0

    def test_exponential_backoff_custom_base(self):
        """Test exponential backoff with custom base delay"""

        result = exponential_backoff(2, 0.5)
        assert result == 2.0  # 0.5 * 2^2 = 2.0

    @patch("time.sleep")  # Patch sleep to avoid actual waiting
    def test_retry_with_multiple_exception_types(self, mock_sleep):
        """Test retry with multiple exception types"""
        call_count = 0

        @retry_on_failure(
            max_retries=3,
            delay=0.01,
            exceptions=(ValueError, TypeError, requests.RequestException),
        )
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First error")
            elif call_count == 2:
                raise TypeError("Second error")
            elif call_count == 3:
                raise requests.RequestException("Third error")
            elif call_count == 4:
                return "success"
            raise Exception("Should not reach here")

        # The function will make 4 attempts (original + 3 retries)
        # and will succeed on the 4th attempt
        result = test_function()
        assert result == "success"
        assert call_count == 4
        assert mock_sleep.call_count == 3

    @patch("time.sleep")
    @patch("sys.stderr")
    def test_retry_error_output(self, mock_stderr, mock_sleep):
        """Test that retry prints appropriate error messages"""
        call_count = 0

        @retry_on_failure(max_retries=2, delay=0.1)
        def test_function():
            nonlocal call_count
            call_count += 1
            raise requests.RequestException("Test error")

        with pytest.raises(requests.RequestException):
            test_function()

        # Check that print to stderr was called for each retry
        assert mock_stderr.write.call_count >= 2

    def test_retry_with_function_arguments(self):
        """Test retry with function that takes arguments"""
        call_count = 0

        @retry_on_failure(max_retries=2, delay=0.01)
        def test_function(a, b, c=None):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.RequestException("Temporary error")
            return a + b + (c or 0)

        result = test_function(1, 2, c=3)
        assert result == 6
        assert call_count == 2

    def test_retry_with_zero_retries(self):
        """Test retry behavior with zero retries"""
        call_count = 0

        @retry_on_failure(max_retries=0)
        def test_function():
            nonlocal call_count
            call_count += 1
            raise requests.RequestException("Error")

        with pytest.raises(requests.RequestException):
            test_function()

        assert call_count == 1  # Should only try once

    @patch("time.sleep")
    def test_retry_with_custom_backoff_factor(self, mock_sleep):
        """Test retry with custom backoff factor"""
        call_count = 0

        @retry_on_failure(
            max_retries=3, delay=1.0, backoff=3.0
        )  # Use higher backoff
        def test_function():
            nonlocal call_count
            call_count += 1
            raise requests.RequestException("Error")

        with pytest.raises(requests.RequestException):
            test_function()

        # Check delays follow the 3x pattern
        expected_calls = [call(1.0), call(3.0), call(9.0)]  # 1, 1*3, 1*3*3
        mock_sleep.assert_has_calls(expected_calls)
