"""
Tests for LLM module
"""

import pytest
import requests
import json
import os
import time
from unittest.mock import patch, mock_open, MagicMock, call

from rubot.llm import (
    load_prompt,
    process_with_openrouter,
    process_with_openrouter_backoff,
    is_valid_openrouter_response,
)


class TestLLM:

    def test_load_prompt_from_file(self):
        """Test loading prompt from file"""
        mock_content = "This is a test prompt"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=mock_content)):
                result = load_prompt("test_prompt.txt")

        assert result == "This is a test prompt"

    def test_load_prompt_from_env(self, temp_env):
        """Test loading prompt from environment variable"""
        temp_env["DEFAULT_SYSTEM_PROMPT"] = "Environment prompt"

        with patch("pathlib.Path.exists", return_value=False):
            result = load_prompt("nonexistent.txt")

        assert result == "Environment prompt"

    def test_load_prompt_default(self, temp_env):
        """Test loading prompt fails without configuration"""
        # Remove the DEFAULT_SYSTEM_PROMPT from the environment
        if "DEFAULT_SYSTEM_PROMPT" in temp_env:
            del temp_env["DEFAULT_SYSTEM_PROMPT"]

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(
                ValueError, match="System prompt must be specified"
            ):
                load_prompt(None)

    def test_process_with_openrouter_success(self, mock_openrouter_requests, temp_env):
        """Test successful OpenRouter API call"""
        from tests.conftest import OpenRouterMockResponses
        
        # Set up successful response
        mock_openrouter_requests.set_single_response(
            OpenRouterMockResponses.successful_response("Test response")
        )

        result = process_with_openrouter(
            "Test markdown content", None, "test-model"
        )

        # Verify the result is valid JSON
        parsed_result = json.loads(result)
        assert "choices" in parsed_result
        assert parsed_result["choices"][0]["message"]["content"] == "Test response"

        # Verify API call was made correctly
        assert mock_openrouter_requests.get_call_count() == 1
        last_request = mock_openrouter_requests.get_last_request()
        assert last_request["json"]["model"] == "test-model"
        assert last_request["json"]["messages"][1]["content"] == "Test markdown content"

    def test_process_with_openrouter_no_api_key(self, temp_env):
        """Test OpenRouter API call without API key"""
        # Remove the API key from the environment
        del temp_env["OPENROUTER_API_KEY"]

        with pytest.raises(
            ValueError,
            match="OPENROUTER_API_KEY environment variable is required",
        ):
            process_with_openrouter("Test content", None, None)

    def test_process_with_openrouter_api_error(self, temp_env):
        """Test OpenRouter API call with error"""
        with patch("rubot.llm.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException("API Error")

            with pytest.raises(
                requests.RequestException, match="OpenRouter API request failed"
            ):
                process_with_openrouter("Test content", None, "test-model")

    def test_process_with_openrouter_default_model(self, mock_openrouter_requests, temp_env):
        """Test OpenRouter API call with default model from environment"""
        from tests.conftest import OpenRouterMockResponses
        
        # Set a custom model in the environment
        temp_env["DEFAULT_MODEL"] = "custom-model"

        mock_openrouter_requests.set_single_response(
            OpenRouterMockResponses.successful_response()
        )

        process_with_openrouter("Test content", None, None)

        # Verify default model was used
        last_request = mock_openrouter_requests.get_last_request()
        assert last_request["json"]["model"] == "custom-model"

    def test_is_valid_openrouter_response(self):
        """Test the is_valid_openrouter_response function"""
        # Valid response
        valid_response = {
            "choices": [{"message": {"content": "This is a valid response"}}]
        }
        assert is_valid_openrouter_response(valid_response) is True

        # Invalid responses
        invalid_responses = [
            {},  # Empty response
            {"choices": []},  # Empty choices
            {"choices": [{"message": {}}]},  # No content
            {"choices": [{"message": {"content": ""}}]},  # Empty content
            {
                "choices": [{"message": {"content": "   "}}]
            },  # Whitespace content
        ]

        for response in invalid_responses:
            assert is_valid_openrouter_response(response) is False

    @patch("time.sleep")
    def test_process_with_openrouter_backoff_success_first_try(
        self, mock_sleep, mock_openrouter_requests, temp_env
    ):
        """Test backoff when first try succeeds"""
        from tests.conftest import OpenRouterMockResponses
        
        # Mock successful response
        mock_openrouter_requests.set_single_response(
            OpenRouterMockResponses.successful_response("Valid response")
        )

        result = process_with_openrouter_backoff(
            "Test content", None, "test-model"
        )

        # Should succeed on first try
        assert mock_openrouter_requests.get_call_count() == 1
        mock_sleep.assert_not_called()

        # Result should be valid
        parsed = json.loads(result)
        assert parsed["choices"][0]["message"]["content"] == "Valid response"

    @patch("time.sleep")
    def test_process_with_openrouter_backoff_empty_response_then_success(
        self, mock_sleep, mock_openrouter_requests, temp_env
    ):
        """Test backoff when first response is empty, second succeeds"""
        from tests.conftest import OpenRouterMockResponses
        
        # First response is empty, second is valid
        mock_openrouter_requests.set_responses([
            OpenRouterMockResponses.empty_response(),
            OpenRouterMockResponses.successful_response("Valid response")
        ])

        result = process_with_openrouter_backoff(
            "Test content", None, "test-model"
        )

        # Should be called twice
        assert mock_openrouter_requests.get_call_count() == 2
        mock_sleep.assert_called_once_with(60)  # Should sleep for 1 minute

        # Result should be valid
        parsed = json.loads(result)
        assert parsed["choices"][0]["message"]["content"] == "Valid response"

    @patch("time.sleep")
    def test_process_with_openrouter_backoff_all_attempts_fail(
        self, mock_sleep, mock_openrouter_requests, temp_env
    ):
        """Test backoff when all attempts fail with empty responses"""
        from tests.conftest import OpenRouterMockResponses
        
        # All responses are empty
        mock_openrouter_requests.set_single_response(
            OpenRouterMockResponses.empty_response()
        )

        with pytest.raises(
            ValueError, match="Empty or invalid content in OpenRouter response"
        ):
            process_with_openrouter_backoff("Test content", None, "test-model")

        # Should be called 6 times (initial + 5 retries)
        assert mock_openrouter_requests.get_call_count() == 6
        assert mock_sleep.call_count == 5

        # Verify exponential backoff sleep times
        mock_sleep.assert_has_calls(
            [
                call(60),  # 1 minute
                call(120),  # 2 minutes
                call(240),  # 4 minutes
                call(480),  # 8 minutes
                call(960),  # 16 minutes
            ]
        )

    @patch("time.sleep")
    def test_process_with_openrouter_backoff_exception_then_success(
        self, mock_sleep, temp_env
    ):
        """Test backoff when first attempt throws exception, second succeeds"""
        from tests.conftest import OpenRouterMockResponses
        
        call_count = 0
        def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise requests.RequestException("API Error")
            else:
                # Return successful response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = OpenRouterMockResponses.successful_response("Valid response")
                return mock_response

        with patch("rubot.llm.requests.post", side_effect=mock_post_side_effect):
            result = process_with_openrouter_backoff(
                "Test content", None, "test-model"
            )

        # Should be called more than twice due to retry_on_failure decorator in process_with_openrouter
        # First call fails -> process_with_openrouter retries 2 times with 10s delays -> then backoff retries with 60s
        assert call_count >= 2
        # The backoff mechanism sleeps for 60s, but process_with_openrouter retries sleep for 10s
        # Both 10.0 and 60 could be called depending on which retry mechanism triggers
        assert any(call.args[0] in [10.0, 60] for call in mock_sleep.call_args_list)

        # Result should be valid
        parsed = json.loads(result)
        assert parsed["choices"][0]["message"]["content"] == "Valid response"

    @patch("time.sleep")
    def test_process_with_openrouter_backoff_all_exceptions(
        self, mock_sleep, temp_env
    ):
        """Test backoff when all attempts throw exceptions"""
        with patch("rubot.llm.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("API Error")

            with pytest.raises(requests.RequestException):
                process_with_openrouter_backoff("Test content", None, "test-model")

            # Should be called multiple times due to retry mechanisms in both functions
            # process_with_openrouter has max_retries=2, so it will be called up to 3 times per backoff attempt
            # Then process_with_openrouter_backoff can retry up to 6 times total
            # So total calls could be much higher: up to 3 calls * 6 backoff attempts = 18 calls
            assert mock_post.call_count >= 6
            # process_with_openrouter will sleep 2 times (for its 2 retries) with 10s delays
            # process_with_openrouter_backoff will sleep 5 times with backoff delays
            # So total sleep calls should be at least 5 (from backoff) + potentially more from inner retries
            assert mock_sleep.call_count >= 5
