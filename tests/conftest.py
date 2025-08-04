"""
Pytest configuration and fixtures
"""

import os
import sys
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

# Create a clean mock for docling functionality
class MockDocling:
    """Simple mock for docling with minimum functionality needed for tests"""
    class DocumentConverter:
        def __init__(self, *args, **kwargs):
            pass
        
        def convert(self, *args, **kwargs):
            result = MagicMock()
            result.status = "SUCCESS"
            result.document = MagicMock()
            result.document.export_to_markdown.return_value = "# Mock Markdown"
            return result
    
    class ConversionStatus:
        SUCCESS = "SUCCESS"
    
    class DoclingConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class ImageRefMode:
        PLACEHOLDER = "placeholder"
        EMBEDDED = "embedded"
        REFERENCED = "referenced"

# Create a mock for docling_core
class MockDoclingCore:
    class types:
        class doc:
            class base:
                class ImageRefMode:
                    PLACEHOLDER = "placeholder"
                    EMBEDDED = "embedded"
                    REFERENCED = "referenced"

# Set up mock modules
mock_docling = MockDocling()
mock_docling_core = MockDoclingCore()

sys.modules['docling'] = mock_docling
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.document_converter'].DocumentConverter = mock_docling.DocumentConverter
sys.modules['docling.datamodel'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.base_models'].ConversionStatus = mock_docling.ConversionStatus
sys.modules['docling_core'] = mock_docling_core
sys.modules['docling_core.types'] = mock_docling_core.types
sys.modules['docling_core.types.doc'] = mock_docling_core.types.doc
sys.modules['docling_core.types.doc.base'] = mock_docling_core.types.doc.base

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
        # Docling configuration
        docling_ocr_engine="easyocr",
        docling_do_ocr=True,
        docling_do_table_structure=False,
        docling_image_mode="placeholder",
        docling_image_placeholder="<!-- image -->",
        docling_use_cpu_only=True,
        docling_batch_size=1,
        docling_max_image_size=1024,
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
