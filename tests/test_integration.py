"""
Integration tests for rubot
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from rubot.cli import main


@pytest.fixture
def cli_runner():
    """Fixture to provide a Click CLI test runner"""
    return CliRunner()


class TestIntegration:

    def test_full_workflow_success(self, cli_runner, temp_config, mock_openrouter_requests):
        """Test complete workflow from PDF download to LLM processing with Docling"""
        from tests.conftest import OpenRouterMockResponses
        
        # Set up structured JSON response
        mock_openrouter_requests.set_single_response(
            OpenRouterMockResponses.structured_json_response()
        )
        
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        try:
            with (
                patch(
                    "rubot.cli.download_pdf_with_backoff",
                    return_value=tmp_path,
                ),
                patch(
                    "rubot.cli._convert_to_markdown",
                    return_value="# Test PDF Content\n\nDocling converted content",
                ),
            ):

                with (
                    patch(
                        "rubot.cli.RubotConfig.from_env",
                        return_value=temp_config,
                    ),
                    patch.dict(
                        "os.environ", {"DEFAULT_SYSTEM_PROMPT": "test prompt"}
                    ),
                ):
                    result = cli_runner.invoke(
                        main, ["--date", "2024-01-15", "--no-cache"]
                    )

                if result.exit_code != 0:
                    print(f"CLI output: {result.output}")
                    print(f"Exception: {result.exception}")
                assert result.exit_code == 0
                # Verify the OpenRouter API was called
                assert mock_openrouter_requests.get_call_count() == 1

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_workflow_with_custom_prompt_and_model(
        self, cli_runner, temp_config, mock_openrouter_requests
    ):
        """Test workflow with custom prompt and model using Docling"""
        from tests.conftest import OpenRouterMockResponses
        
        # Set up structured JSON response
        mock_openrouter_requests.set_single_response(
            OpenRouterMockResponses.structured_json_response()
        )
        
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        # Create temporary prompt file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as prompt_file:
            prompt_file.write("Custom test prompt for integration test")
            prompt_path = prompt_file.name

        try:
            with (
                patch(
                    "rubot.cli.download_pdf_with_backoff",
                    return_value=tmp_path,
                ),
                patch(
                    "rubot.cli._convert_to_markdown",
                    return_value="# Custom PDF Content\n\nCustom docling output",
                ),
            ):

                with (
                    patch(
                        "rubot.cli.RubotConfig.from_env",
                        return_value=temp_config,
                    ),
                    patch.dict(
                        "os.environ", {"DEFAULT_SYSTEM_PROMPT": "test prompt"}
                    ),
                ):
                    result = cli_runner.invoke(
                        main,
                        [
                            "--date",
                            "2024-01-15",
                            "--prompt",
                            prompt_path,
                            "--model",
                            "custom-model",
                        ],
                    )

                assert result.exit_code == 0
                # Verify the OpenRouter API was called with custom model
                assert mock_openrouter_requests.get_call_count() == 1
                last_request = mock_openrouter_requests.get_last_request()
                assert last_request["json"]["model"] == "custom-model"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(prompt_path):
                os.unlink(prompt_path)

    def test_workflow_date_validation_error(self, cli_runner, temp_env):
        """Test workflow with invalid date"""
        result = cli_runner.invoke(main, ["--date", "invalid-date"])
        assert result.exit_code == 1

    def test_workflow_download_error_handling(self, cli_runner, temp_config):
        """Test workflow error handling for download failures"""
        with patch(
            "rubot.cli.download_pdf_with_backoff",
            side_effect=FileNotFoundError("PDF not found for date 2024-01-15"),
        ):
            with patch(
                "rubot.cli.RubotConfig.from_env", return_value=temp_config
            ):
                result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1


@pytest.mark.integration_real_api
class TestRealAPIIntegration:
    """Integration tests that actually call the OpenRouter API - requires API key"""
    
    def test_real_api_call(self, temp_env):
        """Test that we can actually call OpenRouter API - requires real API key"""
        # Skip if no real API key is available
        real_api_key = os.getenv("OPENROUTER_API_KEY_REAL")
        if not real_api_key:
            pytest.skip("OPENROUTER_API_KEY_REAL not set - skipping real API test")
            
        # Temporarily set the real API key
        temp_env["OPENROUTER_API_KEY"] = real_api_key
        
        from rubot.llm import process_with_openrouter
        
        result = process_with_openrouter(
            "This is a test markdown content for API testing.",
            None,
            "moonshotai/kimi-k2:free",
            temperature=0.1,
            max_tokens=100
        )
        
        # Verify we got a valid response
        import json
        parsed = json.loads(result)
        assert "choices" in parsed
        assert len(parsed["choices"]) > 0
        assert "content" in parsed["choices"][0]["message"]
        assert len(parsed["choices"][0]["message"]["content"].strip()) > 0
