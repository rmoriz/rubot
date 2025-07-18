"""
Tests for CLI module
"""

import os
import tempfile
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
    @patch("rubot.cli._convert_to_markdown")
    @patch("rubot.cli.download_pdf")
    def test_cli_basic_usage(
        self, mock_download, mock_convert, mock_llm, cli_runner, temp_config
    ):
        """Test basic CLI usage"""
        # Setup mocks
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        mock_download.return_value = tmp_path
        mock_convert.return_value = "test markdown content"
        mock_llm.return_value = '{"result": "test"}'

        try:
            with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config), \
                 patch.dict("os.environ", {"DEFAULT_SYSTEM_PROMPT": "test prompt"}):
                result = cli_runner.invoke(main, ["--date", "2024-01-15"])

            assert result.exit_code == 0
            mock_download.assert_called_once()
            mock_convert.assert_called_once()
            mock_llm.assert_called_once()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch("rubot.cli.process_with_openrouter")
    @patch("rubot.cli._convert_to_markdown")
    @patch("rubot.cli.download_pdf")
    def test_cli_with_output_file(
        self, mock_download, mock_convert, mock_llm, cli_runner, temp_env
    ):
        """Test CLI with output file"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        mock_download.return_value = tmp_path
        mock_convert.return_value = "test markdown content"
        mock_llm.return_value = '{"result": "test"}'

        try:
            with cli_runner.isolated_filesystem():
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

    @patch("rubot.cli.download_pdf")
    def test_cli_download_error(self, mock_download, cli_runner, temp_config):
        """Test CLI with download error"""
        mock_download.side_effect = FileNotFoundError("PDF not found")
        
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1