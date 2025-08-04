"""
Tests for CLI module
"""

import os
import tempfile
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from rubot.cli import main
from rubot.config import RubotConfig


@pytest.fixture
def cli_runner():
    """Fixture to provide a Click CLI test runner"""
    return CliRunner()


class TestCLI:
    
    @patch("rubot.cli.process_with_openrouter_backoff")
    @patch("rubot.cli._convert_to_markdown")
    @patch("rubot.cli.download_pdf_with_backoff")
    def test_cli_basic_usage(
        self, mock_download_backoff, mock_convert_markdown, mock_llm_backoff, cli_runner, temp_config
    ):
        """Test basic CLI usage with Docling"""
        # Setup mocks
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        mock_download_backoff.return_value = tmp_path
        mock_convert_markdown.return_value = "# Test Markdown\n\nDocling test content"
        mock_llm_backoff.return_value = '{"result": "test"}'

        try:
            with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config), \
                 patch.dict("os.environ", {"DEFAULT_SYSTEM_PROMPT": "test prompt"}):
                result = cli_runner.invoke(main, ["--date", "2024-01-15"])
                
                assert result.exit_code == 0
                mock_download_backoff.assert_called_once()
                mock_convert_markdown.assert_called_once()
                mock_llm_backoff.assert_called_once()
                # The important thing is that the CLI runs successfully
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("rubot.cli.process_with_openrouter_backoff")
    @patch("rubot.cli._convert_to_markdown")
    @patch("rubot.cli.download_pdf_with_backoff")
    def test_cli_with_output_file(
        self, mock_download_backoff, mock_convert_markdown, mock_llm_backoff, cli_runner, temp_env
    ):
        """Test CLI with output file using Docling"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        mock_download_backoff.return_value = tmp_path
        mock_convert_markdown.return_value = "# Test Output\n\nDocling output content"
        mock_llm_backoff.return_value = '{"choices":[{"message":{"content":"{\\"result\\":\\"test\\"}"}}]}'

        try:
            with cli_runner.isolated_filesystem():
                with patch.dict("os.environ", temp_env):
                    result = cli_runner.invoke(
                        main, ["--date", "2024-01-15", "--output", "result.json"]
                    )
                    assert result.exit_code == 0
                    # Check that output was created
                    assert os.path.exists("result.json")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_cli_invalid_date(self, cli_runner, temp_env):
        """Test CLI with invalid date"""
        result = cli_runner.invoke(main, ["--date", "invalid-date"])
        assert result.exit_code == 1

    @patch("rubot.cli.download_pdf_with_backoff")
    def test_cli_download_error(self, mock_download_backoff, cli_runner, temp_config):
        """Test CLI with download error"""
        mock_download_backoff.side_effect = FileNotFoundError("PDF not found")
        
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1

    def test_cli_nonexistent_prompt_file(self, cli_runner, temp_config):
        """Test CLI with nonexistent prompt file fails early before PDF download"""
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15", "--prompt", "/nonexistent/prompt.txt"])

        assert result.exit_code == 1
        assert "Prompt file not found" in result.output

    def test_cli_nonexistent_default_prompt_file(self, cli_runner):
        """Test CLI with nonexistent default prompt file from config fails early"""
        # Create config with nonexistent default prompt file
        config_with_bad_prompt = RubotConfig(
            openrouter_api_key="test_key",
            default_model="test/model",
            default_prompt_file="/nonexistent/default_prompt.txt"
        )
        
        with patch("rubot.cli.RubotConfig.from_env", return_value=config_with_bad_prompt):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1
        assert "Prompt file not found" in result.output

    def test_cli_with_system_prompt_env_var(self, cli_runner, temp_config):
        """Test CLI works correctly when using DEFAULT_SYSTEM_PROMPT instead of prompt file"""
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config), \
             patch("rubot.cli.download_pdf_with_backoff") as mock_download_backoff, \
             patch("rubot.cli._convert_to_markdown") as mock_convert, \
             patch("rubot.cli.process_with_openrouter_backoff") as mock_llm_backoff, \
             patch.dict("os.environ", {"DEFAULT_SYSTEM_PROMPT": "Test system prompt"}):
            
            # Setup mocks to avoid actual processing
            mock_download_backoff.return_value = "/tmp/test.pdf"
            mock_convert.return_value = "# Test content"
            mock_llm_backoff.return_value = '{"result": "success"}'
            
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        # Should succeed because we're using DEFAULT_SYSTEM_PROMPT, not a file
        assert result.exit_code == 0