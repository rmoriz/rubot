"""
Tests for CLI module
"""

import os
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from rubot.cli import main


@pytest.fixture
def cli_runner():
    """Fixture to provide a Click CLI test runner"""
    return CliRunner()


class TestCLI:

    @patch("rubot.cli.process_with_openrouter")
    @patch("rubot.cli.convert_pdf_to_markdown")
    @patch("rubot.cli.download_pdf")
    def test_cli_basic_usage(
        self, mock_download, mock_convert, mock_llm, cli_runner, temp_config
    ):
        """Test basic CLI usage"""
        # Setup mocks
        mock_download.return_value = "/tmp/test.pdf"
        mock_convert.return_value = "test markdown content"
        mock_llm.return_value = '{"result": "test"}'

        # Use the temp_config fixture to provide configuration
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 0
        mock_download.assert_called_once()
        mock_convert.assert_called_once()
        mock_llm.assert_called_once()

    @patch("rubot.cli.process_with_openrouter")
    @patch("rubot.cli.convert_pdf_to_markdown")
    @patch("rubot.cli.download_pdf")
    def test_cli_with_output_file(
        self, mock_download, mock_convert, mock_llm, cli_runner, temp_config
    ):
        """Test CLI with output file"""
        # Setup mocks
        mock_download.return_value = "/tmp/test.pdf"
        mock_convert.return_value = "test markdown content"
        mock_llm.return_value = '{"result": "test"}'

        with cli_runner.isolated_filesystem():
            # Use the temp_config fixture to provide configuration
            with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
                result = cli_runner.invoke(
                    main, ["--date", "2024-01-15", "--output", "result.json"]
                )

            assert result.exit_code == 0
            assert "saved to: result.json" in result.output

            # Check file was created
            with open("result.json", "r") as f:
                content = f.read()
                assert '"result": "test"' in content

    def test_cli_invalid_date(self, cli_runner, temp_env):
        """Test CLI with invalid date"""
        result = cli_runner.invoke(main, ["--date", "invalid-date"])

        assert result.exit_code == 1
        assert "Invalid date format" in result.output

    @patch("rubot.cli.download_pdf")
    def test_cli_download_error(self, mock_download, cli_runner, temp_config):
        """Test CLI with download error"""
        # Setup mock to raise an error
        mock_download.side_effect = FileNotFoundError("PDF not found")

        # Use the temp_config fixture to provide configuration
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1
        assert "Error: PDF not found" in result.output
