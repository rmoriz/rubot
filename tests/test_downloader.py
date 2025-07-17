"""
Tests for downloader module
"""

import pytest
import requests
from unittest.mock import patch, mock_open, MagicMock
import tempfile

from rubot.downloader import generate_pdf_url, download_pdf


class TestDownloader:

    def test_generate_pdf_url(self):
        """Test PDF URL generation"""
        url = generate_pdf_url("2024-01-15")
        expected = "https://ru.muenchen.de/pdf/2024/ru-2024-01-15.pdf"
        assert url == expected

    def test_generate_pdf_url_different_date(self):
        """Test PDF URL generation with different date"""
        url = generate_pdf_url("2023-12-31")
        expected = "https://ru.muenchen.de/pdf/2023/ru-2023-12-31.pdf"
        assert url == expected

    @patch("rubot.downloader.requests.get")
    @patch("rubot.downloader.tempfile.NamedTemporaryFile")
    def test_download_pdf_success(self, mock_tempfile, mock_get):
        """Test successful PDF download"""
        # Mock response
        mock_response = MagicMock()
        mock_response.content = b"fake pdf content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock temporary file
        mock_file = MagicMock()
        mock_file.name = "/tmp/test.pdf"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        result = download_pdf("2024-01-15")

        assert result == "/tmp/test.pdf"
        mock_get.assert_called_once()
        mock_file.write.assert_called_once_with(b"fake pdf content")

    @patch("rubot.downloader.requests.get")
    def test_download_pdf_not_found(self, mock_get):
        """Test PDF download when file not found"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        with pytest.raises(
            FileNotFoundError, match="PDF not found for date 2024-01-15"
        ):
            download_pdf("2024-01-15")

    @patch("rubot.downloader.requests.get")
    def test_download_pdf_network_error(self, mock_get):
        """Test PDF download with network error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(requests.RequestException, match="Failed to download PDF"):
            download_pdf("2024-01-15")
