"""
Pytest configuration and fixtures
"""

import os
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch

from rubot.config import RubotConfig


@pytest.fixture
def temp_env():
    """
    Fixture that provides a clean environment for tests.

    This fixture:
    1. Saves the original environment
    2. Creates a temporary environment with minimal settings
    3. Restores the original environment after the test

    Usage:
        def test_something(temp_env):
            temp_env.update({"MY_VAR": "value"})
            # Test code here
    """
    original_env = os.environ.copy()

    # Create a minimal test environment
    test_env = {
        "OPENROUTER_API_KEY": "test_api_key",
        "DEFAULT_MODEL": "test/model",
        "DEFAULT_SYSTEM_PROMPT": "Test system prompt",
    }

    with patch.dict(os.environ, test_env, clear=True):
        yield os.environ

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_config(temp_env):
    """
    Fixture that provides a RubotConfig instance with test settings.

    Usage:
        def test_something(temp_config):
            # temp_config is a RubotConfig instance with test settings
            assert temp_config.default_model == "test/model"
    """
    return RubotConfig(
        openrouter_api_key="test_api_key",
        default_model="test/model",
        default_prompt_file=None,
        cache_enabled=False,
        cache_dir=None,
        cache_max_age_hours=24,
        request_timeout=30,
        openrouter_timeout=30,
        pdf_timeout=60,
        max_retries=1,
        retry_delay=0.1,
        max_pdf_pages=10,
        output_format="json",
        json_indent=2,
    )


@pytest.fixture
def temp_cache_dir():
    """
    Fixture that provides a temporary directory for cache testing.

    Usage:
        def test_something(temp_cache_dir):
            # temp_cache_dir is a path to a temporary directory
            cache = PDFCache(temp_cache_dir)
            # Test code here
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
