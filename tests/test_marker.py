"""
Tests for marker module
"""

import pytest
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from rubot.marker import convert_pdf_to_markdown


class TestMarker:

    @patch("rubot.marker._find_markdown_file")
    @patch("rubot.marker.subprocess.run")
    @patch("rubot.marker.tempfile.TemporaryDirectory")
    def test_convert_pdf_to_markdown_success(
        self, mock_tempdir, mock_subprocess, mock_find_file
    ):
        """Test successful PDF to markdown conversion"""
        # Mock temporary directory
        mock_temp_path = MagicMock()
        mock_tempdir.return_value.__enter__.return_value = mock_temp_path

        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Create a mock markdown file path
        mock_md_file = Path("/tmp/mock_dir/test/output.md")
        mock_find_file.return_value = mock_md_file

        # Mock file reading
        with patch(
            "builtins.open",
            mock_open(read_data="# Test Markdown\n\nThis is test content."),
        ):
            # Disable caching to avoid file existence check
            result = convert_pdf_to_markdown("/path/to/test.pdf", use_cache=False)

        assert result == "# Test Markdown\n\nThis is test content."
        mock_subprocess.assert_called_once()
        mock_find_file.assert_called_once()

        # Check that marker_single was called with correct arguments
        call_args = mock_subprocess.call_args[0][0]
        assert call_args[0] == "marker_single"
        assert "/path/to/test.pdf" in call_args

    @patch("rubot.marker.subprocess.run")
    @patch("rubot.marker.tempfile.TemporaryDirectory")
    def test_convert_pdf_to_markdown_subprocess_error(
        self, mock_tempdir, mock_subprocess
    ):
        """Test PDF conversion with subprocess error"""
        mock_temp_path = MagicMock()
        mock_tempdir.return_value.__enter__.return_value = mock_temp_path

        # Mock subprocess error
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "marker_single", stderr="Conversion failed"
        )

        with pytest.raises(RuntimeError, match="marker-pdf conversion failed"):
            convert_pdf_to_markdown("/path/to/test.pdf")

    @patch("rubot.marker.subprocess.run")
    @patch("rubot.marker.tempfile.TemporaryDirectory")
    def test_convert_pdf_to_markdown_no_output_file(
        self, mock_tempdir, mock_subprocess
    ):
        """Test PDF conversion when no markdown file is generated"""
        mock_temp_path = MagicMock()
        mock_temp_path.__truediv__ = lambda self, other: Path(f"/tmp/{other}")
        mock_temp_path.glob.return_value = []  # No .md files found
        mock_tempdir.return_value.__enter__.return_value = mock_temp_path

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Mock file not existing
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="No markdown file generated"):
                convert_pdf_to_markdown("/path/to/test.pdf")

    @patch("rubot.marker.subprocess.run")
    def test_convert_pdf_to_markdown_marker_not_installed(self, mock_subprocess):
        """Test PDF conversion when marker-pdf is not installed"""
        mock_subprocess.side_effect = FileNotFoundError("marker_single not found")

        with pytest.raises(FileNotFoundError, match="marker-pdf not found"):
            convert_pdf_to_markdown("/path/to/test.pdf")
