"""
Tests for utils module
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import tempfile
from pathlib import Path

from rubot.utils import validate_date, load_env_config, ensure_directory


class TestUtils:

    def test_validate_date_valid(self):
        """Test valid date validation"""
        assert validate_date("2024-01-15") is True
        assert validate_date("2023-12-31") is True
        assert validate_date("2024-02-29") is True  # Leap year

    def test_validate_date_invalid_format(self):
        """Test invalid date format"""
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("2024-1-15")

        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("24-01-15")

        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("2024/01/15")

    def test_validate_date_invalid_date(self):
        """Test invalid date values"""
        with pytest.raises(ValueError, match="Invalid date"):
            validate_date("2024-02-30")

        with pytest.raises(ValueError, match="Invalid date"):
            validate_date("2024-13-01")

        with pytest.raises(ValueError, match="Invalid date"):
            validate_date("2023-02-29")  # Not a leap year

    @patch('pathlib.Path.exists')
    @patch('rubot.utils.load_dotenv')
    @patch.dict('os.environ', {
        'OPENROUTER_API_KEY': 'test-key',
        'DEFAULT_MODEL': 'test/model',
        'DEFAULT_PROMPT_FILE': 'prompt.txt',
        'DEFAULT_SYSTEM_PROMPT': 'Test prompt'
    })
    def test_load_env_config_with_env_file(self, mock_load_dotenv, mock_exists):
        """Test loading config from .env file"""
        mock_exists.return_value = True

        config = load_env_config()

        # Check that load_dotenv was called
        mock_load_dotenv.assert_called_once()
        
        # Check config values from env vars
        assert config['OPENROUTER_API_KEY'] == 'test-key'
        assert config['DEFAULT_MODEL'] == 'test/model'
        assert config['DEFAULT_PROMPT_FILE'] == 'prompt.txt'
        assert config['DEFAULT_SYSTEM_PROMPT'] == 'Test prompt'

    @patch('pathlib.Path.exists')
    @patch('rubot.utils.load_dotenv')
    @patch.dict('os.environ', {}, clear=True)
    def test_load_env_config_empty_env(self, mock_load_dotenv, mock_exists):
        """Test loading config with empty environment"""
        mock_exists.return_value = False

        config = load_env_config()

        # load_dotenv should not be called if .env doesn't exist
        mock_load_dotenv.assert_not_called()
        
        # Check empty values
        assert config['OPENROUTER_API_KEY'] == ''
        assert config['DEFAULT_MODEL'] == ''
        assert config['DEFAULT_PROMPT_FILE'] == ''
        assert config['DEFAULT_SYSTEM_PROMPT'] == ''

    @patch('pathlib.Path.exists')
    @patch('rubot.utils.load_dotenv')
    @patch.dict('os.environ', {
        'OPENROUTER_API_KEY': 'test-key',
        'DEFAULT_MODEL': 'test/model',
        'DEFAULT_PROMPT_FILE': '',  # Explicitly set to empty
        'DEFAULT_SYSTEM_PROMPT': ''  # Explicitly set to empty
    }, clear=True)  # Use clear=True to ensure no other environment variables interfere
    def test_load_env_config_partial_env(self, mock_load_dotenv, mock_exists):
        """Test loading config with partial environment variables"""
        mock_exists.return_value = True

        config = load_env_config()
        
        # Check partial values
        assert config['OPENROUTER_API_KEY'] == 'test-key'
        assert config['DEFAULT_MODEL'] == 'test/model'
        assert config['DEFAULT_PROMPT_FILE'] == ''
        assert config['DEFAULT_SYSTEM_PROMPT'] == ''

    def test_ensure_directory_new(self):
        """Test ensuring a new directory exists"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            new_dir = os.path.join(tmp_dir, "new_directory")
            
            # Directory should not exist yet
            assert not os.path.exists(new_dir)
            
            # Create directory
            ensure_directory(new_dir)
            
            # Directory should now exist
            assert os.path.isdir(new_dir)

    def test_ensure_directory_existing(self):
        """Test ensuring an existing directory"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Directory already exists
            ensure_directory(tmp_dir)
            
            # Should not raise an exception
            assert os.path.isdir(tmp_dir)

    def test_ensure_directory_nested(self):
        """Test ensuring a nested directory structure"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_dir = os.path.join(tmp_dir, "level1", "level2", "level3")
            
            # Directory should not exist yet
            assert not os.path.exists(nested_dir)
            
            # Create nested directories
            ensure_directory(nested_dir)
            
            # All directories should now exist
            assert os.path.isdir(nested_dir)
            assert os.path.isdir(os.path.join(tmp_dir, "level1"))
            assert os.path.isdir(os.path.join(tmp_dir, "level1", "level2"))
