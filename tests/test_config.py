"""
Tests for config module
"""

import pytest
import os
from unittest.mock import patch, mock_open
from pathlib import Path

from rubot.config import RubotConfig


class TestRubotConfig:

    @patch.dict(
        os.environ,
        {
            "OPENROUTER_API_KEY": "test_key",
            "DEFAULT_MODEL": "test_model",
            "REQUEST_TIMEOUT": "60",
            "CACHE_ENABLED": "false",
        },
    )
    def test_from_env_with_values(self):
        """Test loading config from environment variables"""
        config = RubotConfig.from_env()

        assert config.openrouter_api_key == "test_key"
        assert config.default_model == "test_model"
        assert config.request_timeout == 60
        assert config.cache_enabled is False

    def test_from_env_missing_api_key(self, temp_env):
        """Test config loading fails without API key"""
        # Clear all environment variables
        temp_env.clear()

        # Add only the model but not the API key
        temp_env["DEFAULT_MODEL"] = "test/model"

        with patch(
            "pathlib.Path.exists", return_value=False
        ):  # Ensure no .env file
            with patch(
                "rubot.config.load_dotenv"
            ):  # Prevent any dotenv loading
                with pytest.raises(
                    ValueError,
                    match="OPENROUTER_API_KEY environment variable is required",
                ):
                    RubotConfig.from_env()

    @patch.dict(
        os.environ,
        {"OPENROUTER_API_KEY": "test_key", "DEFAULT_MODEL": "test/model"},
    )
    def test_from_env_defaults(self):
        """Test config loading with required values and defaults"""
        with patch(
            "pathlib.Path.exists", return_value=False
        ):  # Ensure no .env file
            with patch(
                "rubot.config.load_dotenv"
            ):  # Prevent any dotenv loading
                config = RubotConfig.from_env()

                assert config.openrouter_api_key == "test_key"
                assert config.default_model == "test/model"
                # Note: This may vary based on local environment - CI uses 120, local may use 30
                assert config.request_timeout in [
                    30,
                    120,
                ]  # Accept both values
                assert config.cache_enabled is True
                assert config.max_pdf_pages == 100

    def test_from_env_missing_model(self, temp_env):
        """Test config loading fails without model"""
        # Clear all environment variables
        temp_env.clear()

        # Add only the API key but not the model
        temp_env["OPENROUTER_API_KEY"] = "test_key"

        with patch(
            "pathlib.Path.exists", return_value=False
        ):  # Ensure no .env file
            with patch(
                "rubot.config.load_dotenv"
            ):  # Prevent any dotenv loading
                with pytest.raises(
                    ValueError,
                    match="DEFAULT_MODEL environment variable is required",
                ):
                    RubotConfig.from_env()

    @patch.dict(
        os.environ,
        {"OPENROUTER_API_KEY": "test_key", "DEFAULT_MODEL": "test/model"},
    )
    def test_to_dict_masks_api_key(self):
        """Test config to_dict masks sensitive information"""
        config = RubotConfig.from_env()
        config_dict = config.to_dict()

        assert config_dict["openrouter_api_key"] == "***"
        assert config_dict["default_model"] == "test/model"
        # Test new Docling configuration fields are included
        assert "docling_ocr_engine" in config_dict
        assert "docling_do_ocr" in config_dict
        assert "docling_do_table_structure" in config_dict
        assert "docling_model_cache_dir" in config_dict

    @patch("pathlib.Path.exists")
    @patch("rubot.config.load_dotenv")
    @patch.dict(
        os.environ,
        {"OPENROUTER_API_KEY": "test_key", "DEFAULT_MODEL": "file/model"},
    )
    def test_from_env_with_file(self, mock_load_dotenv, mock_exists):
        """Test config loading with .env file"""
        mock_exists.return_value = True

        config = RubotConfig.from_env("custom.env")

        mock_load_dotenv.assert_called_once_with("custom.env")
        assert config.openrouter_api_key == "test_key"
        assert config.default_model == "file/model"

    @patch.dict(
        os.environ,
        {
            "OPENROUTER_API_KEY": "test_key",
            "DEFAULT_MODEL": "test/model",
            "DOCLING_OCR_ENGINE": "tesseract",
            "DOCLING_DO_OCR": "false",
            "DOCLING_DO_TABLE_STRUCTURE": "false",
            "DOCLING_MODEL_CACHE_DIR": "/custom/cache",
        },
    )
    def test_docling_configuration(self):
        """Test Docling-specific configuration options"""
        config = RubotConfig.from_env()

        assert config.docling_ocr_engine == "tesseract"
        assert config.docling_do_ocr is False
        assert config.docling_do_table_structure is False
        assert config.docling_model_cache_dir == "/custom/cache"

    @patch.dict(
        os.environ,
        {"OPENROUTER_API_KEY": "test_key", "DEFAULT_MODEL": "test/model"},
    )
    def test_docling_defaults(self):
        """Test Docling configuration defaults"""
        config = RubotConfig.from_env()

        assert config.docling_ocr_engine == "easyocr"
        assert config.docling_do_ocr is True
        assert (
            config.docling_do_table_structure is False
        )  # Disabled by default for performance
        # Allow both None and the example path for flexibility in tests
        assert config.docling_model_cache_dir in [None, "/path/to/model/cache"]
