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


# Set up mock modules - using MagicMock for flexibility
mock_docling_module = MagicMock()
mock_docling_module.DocumentConverter = MockDocling.DocumentConverter
mock_docling_module.ConversionStatus = MockDocling.ConversionStatus
mock_docling_module.DoclingConfig = MockDocling.DoclingConfig
mock_docling_module.ImageRefMode = MockDocling.ImageRefMode

mock_docling_core_module = MagicMock()
mock_docling_core_module.types = MockDoclingCore.types

sys.modules["docling"] = mock_docling_module  # type: ignore
sys.modules["docling.document_converter"] = MagicMock()
sys.modules["docling.document_converter"].DocumentConverter = MockDocling.DocumentConverter
sys.modules["docling.datamodel"] = MagicMock()
sys.modules["docling.datamodel.base_models"] = MagicMock()
sys.modules["docling.datamodel.base_models"].ConversionStatus = MockDocling.ConversionStatus
sys.modules["docling_core"] = mock_docling_core_module  # type: ignore
sys.modules["docling_core.types"] = MockDoclingCore.types  # type: ignore
sys.modules["docling_core.types.doc"] = MockDoclingCore.types.doc  # type: ignore
sys.modules["docling_core.types.doc.base"] = MockDoclingCore.types.doc.base  # type: ignore

from rubot.config import RubotConfig
import json
from typing import Dict, Any, List


class OpenRouterMockResponses:
    """Collection of mock responses for OpenRouter API tests"""

    @staticmethod
    def successful_response(content: str = "Mock LLM response") -> Dict[str, Any]:
        """Standard successful OpenRouter response"""
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test/model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

    @staticmethod
    def empty_response() -> Dict[str, Any]:
        """Response with empty content"""
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test/model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": ""
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 0,
                "total_tokens": 100
            }
        }

    @staticmethod
    def structured_json_response() -> Dict[str, Any]:
        """Response with structured JSON content (typical for rubot)"""
        json_content = {
            "issue": "123",
            "year": "2024",
            "id": "2024-01-15",
            "summary": "Test Rathaus-Umschau analysis",
            "social_media_post": "Test social media post",
            "announcements": [
                {
                    "title": "Test announcement",
                    "description": "Test description",
                    "category": "test",
                    "date": "2024-01-15",
                    "location": "Test location"
                }
            ],
            "events": [],
            "important_dates": []
        }
        
        return {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test/model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(json_content, indent=2, ensure_ascii=False)
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 500,
                "completion_tokens": 300,
                "total_tokens": 800
            }
        }


class OpenRouterMockClient:
    """Mock client for OpenRouter API that can simulate various scenarios"""
    
    def __init__(self):
        self.responses: List[Dict[str, Any]] = []
        self.call_count = 0
        self.last_request: Dict[str, Any] = {}
        
    def set_responses(self, responses: List[Dict[str, Any]]):
        """Set a sequence of responses to return"""
        self.responses = responses
        self.call_count = 0
        
    def set_single_response(self, response: Dict[str, Any]):
        """Set a single response to return repeatedly"""
        self.responses = [response]
        self.call_count = 0
        
    def mock_post(self, url: str, headers: Dict, json: Dict, timeout: int, verify: bool):
        """Mock the requests.post method"""
        import requests
        
        # Store the request for inspection
        self.last_request = {
            'url': url,
            'headers': headers,
            'json': json,
            'timeout': timeout,
            'verify': verify
        }
        
        # Get the response to return
        if not self.responses:
            # Default successful response if none set
            response_data = OpenRouterMockResponses.successful_response()
        elif len(self.responses) == 1:
            # Single response, return it every time
            response_data = self.responses[0]
        else:
            # Multiple responses, cycle through them
            response_data = self.responses[self.call_count % len(self.responses)]
            
        self.call_count += 1
        
        # Create mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = response_data
        mock_response.headers = {'content-type': 'application/json'}
        
        return mock_response
        
    def get_call_count(self) -> int:
        """Get the number of times the API was called"""
        return self.call_count
        
    def get_last_request(self) -> Dict[str, Any]:
        """Get the last request made to the API"""
        return self.last_request


@pytest.fixture
def mock_openrouter():
    """
    Fixture that provides a configured OpenRouter mock client.
    
    Usage:
        def test_something(mock_openrouter):
            # Set up the response you want
            mock_openrouter.set_single_response(
                OpenRouterMockResponses.successful_response("Test content")
            )
            
            # Your test code that calls OpenRouter
            with patch("rubot.llm.requests.post", mock_openrouter.mock_post):
                result = process_with_openrouter(...)
    """
    client = OpenRouterMockClient()
    # Set default successful response
    client.set_single_response(OpenRouterMockResponses.successful_response())
    return client


@pytest.fixture
def mock_openrouter_requests(mock_openrouter):
    """
    Fixture that automatically patches requests.post with OpenRouter mock.
    
    Usage:
        def test_something(mock_openrouter_requests):
            # requests.post is already patched
            result = process_with_openrouter(...)
            
            # Access the mock if needed
            assert mock_openrouter_requests.get_call_count() == 1
    """
    with patch("rubot.llm.requests.post", mock_openrouter.mock_post):
        yield mock_openrouter


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
