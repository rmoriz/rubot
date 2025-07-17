"""
Tests for config module
"""

import pytest
import os
from unittest.mock import patch, mock_open
from pathlib import Path

from rubot.config import RubotConfig


class TestRubotConfig:
    
    @patch.dict(os.environ, {
        'OPENROUTER_API_KEY': 'test_key',
        'DEFAULT_MODEL': 'test_model',
        'REQUEST_TIMEOUT': '60',
        'CACHE_ENABLED': 'false'
    })
    def test_from_env_with_values(self):
        """Test loading config from environment variables"""
        config = RubotConfig.from_env()
        
        assert config.openrouter_api_key == 'test_key'
        assert config.default_model == 'test_model'
        assert config.request_timeout == 60
        assert config.cache_enabled is False
    
    def test_from_env_missing_api_key(self):
        """Test config loading uses defaults when API key missing"""
        with patch.dict(os.environ, {}, clear=True):
            config = RubotConfig.from_env()
            assert config.openrouter_api_key == "your_openrouter_api_key_here"
    
    @patch.dict(os.environ, {
        'OPENROUTER_API_KEY': 'test_key',
        'DEFAULT_MODEL': 'test/model'
    })
    def test_from_env_defaults(self):
        """Test config loading with required values and defaults"""
        config = RubotConfig.from_env()
        
        assert config.openrouter_api_key == 'test_key'
        assert config.default_model == 'test/model'
        assert config.request_timeout == 30
        assert config.cache_enabled is True
        assert config.max_pdf_pages == 100
    
    def test_from_env_missing_model(self):
        """Test config loading uses defaults when model missing"""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'}):
            config = RubotConfig.from_env()
            assert config.default_model == "moonshotai/kimi-k2:free"
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key', 'DEFAULT_MODEL': 'test/model'})
    def test_to_dict_masks_api_key(self):
        """Test config to_dict masks sensitive information"""
        config = RubotConfig.from_env()
        config_dict = config.to_dict()
        
        assert config_dict['openrouter_api_key'] == '***'
        assert config_dict['default_model'] == 'test/model'
    
    @patch('pathlib.Path.exists')
    @patch('rubot.config.load_dotenv')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_from_env_with_file(self, mock_load_dotenv, mock_exists):
        """Test config loading with .env file"""
        mock_exists.return_value = True
        
        config = RubotConfig.from_env('custom.env')
        
        mock_load_dotenv.assert_called_once_with('custom.env')
        assert config.openrouter_api_key == 'test_key'