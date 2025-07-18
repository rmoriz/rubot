"""
Tests for downloader module
"""

import pytest
import tempfile
import os
import requests
from unittest.mock import patch, MagicMock
from rubot.downloader import download_pdf, generate_pdf_url, validate_date_format, validate_pdf_url


class TestDownloader:

    def test_generate_pdf_url(self):
        """Test PDF URL generation"""
        url = generate_pdf_url("2024-01-15")
        assert url == "https://ru.muenchen.de/pdf/2024/ru-2024-01-15.pdf"

    def test_generate_pdf_url_different_date(self):
        """Test PDF URL generation with different date"""
        url = generate_pdf_url("2023-12-25")
        assert url == "https://ru.muenchen.de/pdf/2023/ru-2023-12-25.pdf"

    def test_validate_date_format(self):
        """Test date format validation"""
        validate_date_format("2024-01-15")  # Should not raise

    def test_validate_date_format_invalid(self):
        """Test date format validation with invalid date"""
        with pytest.raises(ValueError):
            validate_date_format("invalid-date")

    def test_validate_pdf_url(self):
        """Test PDF URL validation"""
        validate_pdf_url("https://ru.muenchen.de/pdf/2024/ru-2024-01-15.pdf")  # Should not raise

    def test_validate_pdf_url_invalid(self):
        """Test PDF URL validation with invalid domain"""
        with pytest.raises(ValueError):
            validate_pdf_url("https://invalid-domain.com/test.pdf")

    @patch("requests.get")
    def test_download_pdf_success(self, mock_get):
        """Test successful PDF download"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_response.iter_content.return_value = [b"pdf content"]
        mock_get.return_value = mock_response

        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            mock_file = MagicMock()
            mock_file.name = "/tmp/test.pdf"
            mock_tmp.return_value.__enter__.return_value = mock_file

            result = download_pdf("2024-01-15")
            assert result == "/tmp/test.pdf"

    @patch("requests.get")
    def test_download_pdf_not_found(self, mock_get):
        """Test PDF download when file not found"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        with pytest.raises(FileNotFoundError):
            download_pdf("2024-01-15")

    @patch("requests.get")
    def test_download_pdf_network_error(self, mock_get):
        """Test PDF download with network error"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            download_pdf("2024-01-15")