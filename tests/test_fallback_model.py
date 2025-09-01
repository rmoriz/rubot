"""
Tests for fallback model functionality
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import requests

from rubot.llm import process_with_openrouter_backoff
from rubot.config import RubotConfig


class TestFallbackModel:

    @patch("rubot.llm.process_with_openrouter")
    @patch("rubot.llm.time.sleep")
    def test_fallback_model_success_after_primary_fails(self, mock_sleep, mock_process):
        """Test fallback model is used when primary model fails all retries"""
        # Mock primary model failures
        primary_failures = [
            requests.RequestException("Primary model unavailable"),
            requests.RequestException("Primary model unavailable"),
            requests.RequestException("Primary model unavailable"),
            requests.RequestException("Primary model unavailable"),  # Initial + 3 retries
        ]
        
        # Mock successful fallback response
        fallback_response = {
            "choices": [{"message": {"content": "Fallback model response"}}]
        }
        
        mock_process.side_effect = primary_failures + [json.dumps(fallback_response)]
        
        result = process_with_openrouter_backoff(
            "test content",
            None,
            "primary-model",
            fallback_model="fallback-model"
        )
        
        # Should have made 4 calls to primary model + 1 to fallback
        assert mock_process.call_count == 5
        
        # Verify the result is from fallback model
        result_json = json.loads(result)
        assert result_json["choices"][0]["message"]["content"] == "Fallback model response"

    @patch("rubot.llm.process_with_openrouter")
    @patch("rubot.llm.time.sleep")
    def test_no_fallback_when_primary_succeeds(self, mock_sleep, mock_process):
        """Test fallback model is not used when primary model succeeds"""
        success_response = {
            "choices": [{"message": {"content": "Primary model response"}}]
        }
        
        mock_process.return_value = json.dumps(success_response)
        
        result = process_with_openrouter_backoff(
            "test content",
            None,
            "primary-model",
            fallback_model="fallback-model"
        )
        
        # Should only make 1 call to primary model
        assert mock_process.call_count == 1
        
        # Verify the result is from primary model
        result_json = json.loads(result)
        assert result_json["choices"][0]["message"]["content"] == "Primary model response"

    @patch("rubot.llm.process_with_openrouter")
    @patch("rubot.llm.time.sleep")
    def test_fallback_model_also_fails(self, mock_sleep, mock_process):
        """Test behavior when both primary and fallback models fail"""
        # All calls fail
        mock_process.side_effect = requests.RequestException("All models unavailable")
        
        with pytest.raises(requests.RequestException, match="All models unavailable"):
            process_with_openrouter_backoff(
                "test content",
                None,
                "primary-model",
                fallback_model="fallback-model"
            )
        
        # Should have made 4 calls to primary model + 1 to fallback
        assert mock_process.call_count == 5

    @patch("rubot.llm.process_with_openrouter")
    @patch("rubot.llm.time.sleep")
    def test_no_fallback_model_configured(self, mock_sleep, mock_process):
        """Test behavior when no fallback model is configured"""
        mock_process.side_effect = requests.RequestException("Primary model unavailable")
        
        with pytest.raises(requests.RequestException, match="Primary model unavailable"):
            process_with_openrouter_backoff(
                "test content",
                None,
                "primary-model",
                fallback_model=None
            )
        
        # Should only make 4 calls to primary model (initial + 3 retries)
        assert mock_process.call_count == 4

    @patch("rubot.llm.process_with_openrouter")
    @patch("rubot.llm.time.sleep")
    def test_fallback_same_as_primary_skipped(self, mock_sleep, mock_process):
        """Test fallback is skipped when it's the same as primary model"""
        mock_process.side_effect = requests.RequestException("Model unavailable")
        
        with pytest.raises(requests.RequestException, match="Model unavailable"):
            process_with_openrouter_backoff(
                "test content",
                None,
                "same-model",
                fallback_model="same-model"
            )
        
        # Should only make 4 calls to primary model (no fallback attempt)
        assert mock_process.call_count == 4

    @patch("rubot.llm.process_with_openrouter")
    @patch("rubot.llm.time.sleep")
    def test_fallback_with_invalid_response(self, mock_sleep, mock_process):
        """Test fallback model with invalid response"""
        # Primary model fails
        primary_failures = [requests.RequestException("Primary unavailable")] * 4
        
        # Fallback model returns invalid response (empty content)
        invalid_response = {"choices": [{"message": {"content": ""}}]}
        
        mock_process.side_effect = primary_failures + [json.dumps(invalid_response)]
        
        # Should raise the last exception from primary model attempts (since fallback fails)
        with pytest.raises(requests.RequestException, match="Primary unavailable"):
            process_with_openrouter_backoff(
                "test content",
                None,
                "primary-model",
                fallback_model="fallback-model"
            )
        
        # Should have made 4 calls to primary model + 1 to fallback
        assert mock_process.call_count == 5

    def test_config_includes_fallback_model(self):
        """Test that RubotConfig includes fallback_model field"""
        with patch.dict("os.environ", {
            "OPENROUTER_API_KEY": "test-key",
            "DEFAULT_MODEL": "primary-model",
            "FALLBACK_MODEL": "fallback-model"
        }):
            config = RubotConfig.from_env()
            assert config.fallback_model == "fallback-model"

    def test_config_fallback_model_optional(self):
        """Test that fallback_model is optional in config"""
        with patch.dict("os.environ", {
            "OPENROUTER_API_KEY": "test-key",
            "DEFAULT_MODEL": "primary-model"
        }, clear=True):
            config = RubotConfig.from_env()
            assert config.fallback_model is None

    def test_config_to_dict_includes_fallback_model(self):
        """Test that config.to_dict() includes fallback_model"""
        with patch.dict("os.environ", {
            "OPENROUTER_API_KEY": "test-key",
            "DEFAULT_MODEL": "primary-model",
            "FALLBACK_MODEL": "fallback-model"
        }):
            config = RubotConfig.from_env()
            config_dict = config.to_dict()
            assert "fallback_model" in config_dict
            assert config_dict["fallback_model"] == "fallback-model"