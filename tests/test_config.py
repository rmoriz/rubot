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
    
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_missing_api_key(self):
        """Test config loading fails without API key"""
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is required"):
            RubotConfig.from_env()
    
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
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_from_env_missing_model(self):
        """Test config loading fails without DEFAULT_MODEL"""
        with pytest.raises(ValueError, match="DEFAULT_MODEL environment variable is required"):
            RubotConfig.from_env()
    
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_to_dict_masks_api_key(self):
        """Test config to_dict masks sensitive information"""
        config = RubotConfig.from_env()
        config_dict = config.to_dict()
        
        assert config_dict['openrouter_api_key'] == '***'
        assert config_dict['default_model'] == 'test_key'  # Uses the test value
    
    @patch('pathlib.Path.exists')
    @patch('rubot.config.load_dotenv')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key'})
    def test_from_env_with_file(self, mock_load_dotenv, mock_exists):
        """Test config loading with .env file"""
        mock_exists.return_value = True
        
        config = RubotConfig.from_env('custom.env')
        
        mock_load_dotenv.assert_called_once_with('custom.env')
        assert config.openrouter_api_key == 'test_key'