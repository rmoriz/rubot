"""
Integration tests for rubot workflow
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from rubot.cli import main


class TestIntegration:

    @patch("rubot.cli.os.remove")
    @patch("rubot.cli.process_with_openrouter")
    @patch("rubot.cli.convert_pdf_to_markdown")
    @patch("rubot.cli.download_pdf")
    def test_full_workflow_success(
        self,
        mock_download,
        mock_convert,
        mock_llm,
        mock_remove,
        cli_runner,
        temp_config,
    ):
        """Test complete workflow from download to output"""
        # Setup mocks
        mock_download.return_value = "/tmp/test.pdf"
        mock_convert.return_value = "# Test Document\n\nThis is test content."
        mock_llm.return_value = json.dumps(
            {
                "summary": "Test document analysis",
                "announcements": [
                    {
                        "title": "Test Announcement",
                        "description": "Test description",
                        "category": "test",
                        "date": "2024-01-15",
                    }
                ],
            },
            indent=2,
        )

        # Use the temp_config fixture to provide configuration
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 0
        assert "Processing Rathaus-Umschau for date: 2024-01-15" in result.output
        assert "PDF Cache MISS: Downloading..." in result.output
        assert "PDF downloaded to: /tmp/test.pdf" in result.output
        assert "Processing with LLM..." in result.output
        assert '"summary": "Test document analysis"' in result.output

        # Verify all steps were called
        mock_download.assert_called_once_with(
            "2024-01-15", 30
        )  # timeout parameter is passed
        mock_convert.assert_called_once_with(
            "/tmp/test.pdf", use_cache=False, cache_dir=None, cache_root=None, verbose=False, timeout=60
        )
        mock_llm.assert_called_once()

    @patch("rubot.cli.process_with_openrouter")
    @patch("rubot.cli.convert_pdf_to_markdown")
    @patch("rubot.cli.download_pdf")
    def test_workflow_with_custom_prompt_and_model(
        self, mock_download, mock_convert, mock_llm, cli_runner, temp_config
    ):
        """Test workflow with custom prompt file and model"""
        mock_download.return_value = "/tmp/test.pdf"
        mock_convert.return_value = "Test markdown"
        mock_llm.return_value = '{"result": "custom test"}'

        with cli_runner.isolated_filesystem():
            # Create custom prompt file
            with open("custom_prompt.txt", "w") as f:
                f.write("Custom prompt for testing")

            # Use the temp_config fixture to provide configuration
            with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
                result = cli_runner.invoke(
                    main,
                    [
                        "--date",
                        "2024-01-15",
                        "--prompt",
                        "custom_prompt.txt",
                        "--model",
                        "custom-model",
                    ],
                )

            assert result.exit_code == 0

            # Verify LLM was called with custom parameters
            mock_llm.assert_called_once()
            # Check that the model parameter was passed correctly
            call_args = mock_llm.call_args
            assert (
                call_args[0][2] == "custom-model"
            )  # Third argument should be the model

    def test_workflow_date_validation_error(self, cli_runner, temp_env):
        """Test workflow with invalid date"""
        result = cli_runner.invoke(main, ["--date", "invalid-date"])

        assert result.exit_code == 1
        assert "Invalid date format" in result.output

    @patch("rubot.cli.download_pdf")
    def test_workflow_download_error_handling(
        self, mock_download, cli_runner, temp_config
    ):
        """Test workflow error handling for download failures"""
        mock_download.side_effect = FileNotFoundError(
            "PDF not found for date 2024-01-15"
        )

        # Use the temp_config fixture to provide configuration
        with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
            result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1
        assert "Error: PDF not found for date 2024-01-15" in result.output
