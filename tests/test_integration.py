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

    def test_full_workflow_success(self, cli_runner, temp_config):
        """Test complete workflow from PDF download to LLM processing"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        try:
            with patch("rubot.cli.download_pdf", return_value=tmp_path), \
                 patch("fitz.open") as mock_fitz, \
                 patch("rubot.cli.process_with_openrouter", return_value='{"result": "success"}') as mock_llm:
                
                mock_doc = MagicMock()
                mock_doc.__len__.return_value = 1
                mock_page = MagicMock()
                mock_page.get_text.return_value = "Test PDF content"
                mock_doc.load_page.return_value = mock_page
                mock_fitz.return_value = mock_doc

                with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
                    result = cli_runner.invoke(main, ["--date", "2024-01-15"])

                assert result.exit_code == 0
                mock_llm.assert_called_once()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_workflow_with_custom_prompt_and_model(self, cli_runner, temp_config):
        """Test workflow with custom prompt and model"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"mock pdf content")
            tmp_path = tmp_file.name

        try:
            with patch("rubot.cli.download_pdf", return_value=tmp_path), \
                 patch("fitz.open") as mock_fitz, \
                 patch("rubot.cli.process_with_openrouter", return_value='{"result": "custom"}') as mock_llm:
                
                mock_doc = MagicMock()
                mock_doc.__len__.return_value = 1
                mock_page = MagicMock()
                mock_page.get_text.return_value = "Test PDF content"
                mock_doc.load_page.return_value = mock_page
                mock_fitz.return_value = mock_doc

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
                mock_llm.assert_called_once()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_workflow_date_validation_error(self, cli_runner, temp_env):
        """Test workflow with invalid date"""
        result = cli_runner.invoke(main, ["--date", "invalid-date"])
        assert result.exit_code == 1

    def test_workflow_download_error_handling(self, cli_runner, temp_config):
        """Test workflow error handling for download failures"""
        with patch("rubot.cli.download_pdf", side_effect=FileNotFoundError("PDF not found for date 2024-01-15")):
            with patch("rubot.cli.RubotConfig.from_env", return_value=temp_config):
                result = cli_runner.invoke(main, ["--date", "2024-01-15"])

        assert result.exit_code == 1