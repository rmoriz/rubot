"""
Tests for LLM module
"""

import pytest
import requests
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from rubot.llm import load_prompt, process_with_openrouter


class TestLLM:
    
    def test_load_prompt_from_file(self):
        """Test loading prompt from file"""
        mock_content = "This is a test prompt"
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_content)):
                result = load_prompt('test_prompt.txt')
        
        assert result == "This is a test prompt"
    
    @patch.dict(os.environ, {'DEFAULT_SYSTEM_PROMPT': 'Environment prompt'})
    def test_load_prompt_from_env(self):
        """Test loading prompt from environment variable"""
        with patch('pathlib.Path.exists', return_value=False):
            result = load_prompt('nonexistent.txt')
        
        assert result == "Environment prompt"
    
    def test_load_prompt_default(self):
        """Test loading default prompt"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                result = load_prompt(None)
        
        assert "Analyze the following Rathaus-Umschau content" in result
    
    @patch('rubot.llm.requests.post')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_process_with_openrouter_success(self, mock_post):
        """Test successful OpenRouter API call"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = process_with_openrouter(
            "Test markdown content",
            None,
            "test-model"
        )
        
        # Verify the result is valid JSON
        parsed_result = json.loads(result)
        assert "choices" in parsed_result
        
        # Verify API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == 'test-model'
        assert call_args[1]['json']['messages'][1]['content'] == 'Test markdown content'
    
    def test_process_with_openrouter_no_api_key(self):
        """Test OpenRouter API call without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
                process_with_openrouter("Test content", None, None)
    
    @patch('rubot.llm.requests.post')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_process_with_openrouter_api_error(self, mock_post):
        """Test OpenRouter API call with error"""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        with pytest.raises(requests.RequestException, match="OpenRouter API request failed"):
            process_with_openrouter("Test content", None, None)
    
    @patch('rubot.llm.requests.post')
    @patch.dict(os.environ, {
        'OPENROUTER_API_KEY': 'test_key',
        'DEFAULT_MODEL': 'custom-model'
    })
    def test_process_with_openrouter_default_model(self, mock_post):
        """Test OpenRouter API call with default model from environment"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "response"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        process_with_openrouter("Test content", None, None)
        
        # Verify default model was used
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == 'custom-model'