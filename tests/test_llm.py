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
    is_valid_openrouter_response
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
            with pytest.raises(ValueError, match="System prompt must be specified"):
                load_prompt(None)

    @patch("rubot.llm.requests.post")
    @patch("time.sleep")  # Mock time.sleep to avoid waiting
    def test_process_with_openrouter_success(self, mock_sleep, mock_post, temp_env):
        """Test successful OpenRouter API call"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = process_with_openrouter("Test markdown content", None, "test-model")

        # Verify the result is valid JSON
        parsed_result = json.loads(result)
        assert "choices" in parsed_result

        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "test-model"
        assert call_args[1]["json"]["messages"][1]["content"] == "Test markdown content"

    def test_process_with_openrouter_no_api_key(self, temp_env):
        """Test OpenRouter API call without API key"""
        # Remove the API key from the environment
        del temp_env["OPENROUTER_API_KEY"]

        with pytest.raises(
            ValueError, match="OPENROUTER_API_KEY environment variable is required"
        ):
            process_with_openrouter("Test content", None, None)

    @patch("rubot.llm.requests.post")
    @patch("time.sleep")  # Mock time.sleep to avoid waiting
    def test_process_with_openrouter_api_error(self, mock_sleep, mock_post, temp_env):
        """Test OpenRouter API call with error"""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with pytest.raises(
            requests.RequestException, match="OpenRouter API request failed"
        ):
            process_with_openrouter("Test content", None, "test-model")
        
        # Verify that time.sleep was called (due to the retry mechanism)
        mock_sleep.assert_called()

    @patch("rubot.llm.requests.post")
    @patch("time.sleep")  # Mock time.sleep to avoid waiting
    def test_process_with_openrouter_default_model(self, mock_sleep, mock_post, temp_env):
        """Test OpenRouter API call with default model from environment"""
        # Set a custom model in the environment
        temp_env["DEFAULT_MODEL"] = "custom-model"

        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "response"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        process_with_openrouter("Test content", None, None)

        # Verify default model was used
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "custom-model"
        
    def test_is_valid_openrouter_response(self):
        """Test the is_valid_openrouter_response function"""
        # Valid response
        valid_response = {
            "choices": [
                {"message": {"content": "This is a valid response"}}
            ]
        }
        assert is_valid_openrouter_response(valid_response) is True
        
        # Invalid responses
        invalid_responses = [
            {},  # Empty response
            {"choices": []},  # Empty choices
            {"choices": [{"message": {}}]},  # No content
            {"choices": [{"message": {"content": ""}}]},  # Empty content
            {"choices": [{"message": {"content": "   "}}]},  # Whitespace content
        ]
        
        for response in invalid_responses:
            assert is_valid_openrouter_response(response) is False
            
    @patch("rubot.llm.process_with_openrouter")
    @patch("time.sleep")
    def test_process_with_openrouter_backoff_success_first_try(self, mock_sleep, mock_process):
        """Test backoff when first try succeeds"""
        # Mock successful response
        mock_process.return_value = json.dumps({
            "choices": [{"message": {"content": "Valid response"}}]
        })
        
        result = process_with_openrouter_backoff("Test content", None, "test-model")
        
        # Should succeed on first try
        mock_process.assert_called_once()
        mock_sleep.assert_not_called()
        
        # Result should be valid
        parsed = json.loads(result)
        assert parsed["choices"][0]["message"]["content"] == "Valid response"
        
    @patch("rubot.llm.process_with_openrouter")
    @patch("time.sleep")
    def test_process_with_openrouter_backoff_empty_response_then_success(self, mock_sleep, mock_process):
        """Test backoff when first response is empty, second succeeds"""
        # First response is empty, second is valid
        mock_process.side_effect = [
            json.dumps({"choices": [{"message": {"content": ""}}]}),  # Empty content
            json.dumps({"choices": [{"message": {"content": "Valid response"}}]})
        ]
        
        result = process_with_openrouter_backoff("Test content", None, "test-model")
        
        # Should be called twice
        assert mock_process.call_count == 2
        mock_sleep.assert_called_once_with(60)  # Should sleep for 1 minute
        
        # Result should be valid
        parsed = json.loads(result)
        assert parsed["choices"][0]["message"]["content"] == "Valid response"
        
    @patch("rubot.llm.process_with_openrouter")
    @patch("time.sleep")
    def test_process_with_openrouter_backoff_all_attempts_fail(self, mock_sleep, mock_process):
        """Test backoff when all attempts fail with empty responses"""
        # All responses are empty
        mock_process.return_value = json.dumps({"choices": [{"message": {"content": ""}}]})
        
        with pytest.raises(ValueError, match="Empty or invalid content in OpenRouter response"):
            process_with_openrouter_backoff("Test content", None, "test-model")
        
        # Should be called 6 times (initial + 5 retries)
        assert mock_process.call_count == 6
        assert mock_sleep.call_count == 5
        
        # Verify exponential backoff sleep times
        mock_sleep.assert_has_calls([
            call(60),    # 1 minute
            call(120),   # 2 minutes
            call(240),   # 4 minutes
            call(480),   # 8 minutes
            call(960),   # 16 minutes
        ])
        
    @patch("rubot.llm.process_with_openrouter")
    @patch("time.sleep")
    def test_process_with_openrouter_backoff_exception_then_success(self, mock_sleep, mock_process):
        """Test backoff when first attempt throws exception, second succeeds"""
        # First call raises exception, second succeeds
        mock_process.side_effect = [
            requests.RequestException("API Error"),
            json.dumps({"choices": [{"message": {"content": "Valid response"}}]})
        ]
        
        result = process_with_openrouter_backoff("Test content", None, "test-model")
        
        # Should be called twice
        assert mock_process.call_count == 2
        mock_sleep.assert_called_once_with(60)  # Should sleep for 1 minute
        
        # Result should be valid
        parsed = json.loads(result)
        assert parsed["choices"][0]["message"]["content"] == "Valid response"
        
    @patch("rubot.llm.process_with_openrouter")
    @patch("time.sleep")
    def test_process_with_openrouter_backoff_all_exceptions(self, mock_sleep, mock_process):
        """Test backoff when all attempts throw exceptions"""
        # All calls raise exceptions
        mock_process.side_effect = requests.RequestException("API Error")
        
        with pytest.raises(requests.RequestException):
            process_with_openrouter_backoff("Test content", None, "test-model")
        
        # Should be called 6 times (initial + 5 retries)
        assert mock_process.call_count == 6
        assert mock_sleep.call_count == 5
