"""
Tests for downloader module
"""

import pytest
import tempfile
import os
import requests
import time
from unittest.mock import patch, MagicMock, call
from rubot.downloader import (
    download_pdf,
    download_pdf_with_backoff,
    generate_pdf_url,
    validate_date_format,
    validate_pdf_url,
)


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
        validate_pdf_url(
            "https://ru.muenchen.de/pdf/2024/ru-2024-01-15.pdf"
        )  # Should not raise

    def test_validate_pdf_url_invalid(self):
        """Test PDF URL validation with invalid domain"""
        with pytest.raises(ValueError):
            validate_pdf_url("https://invalid-domain.com/test.pdf")

    @patch("requests.get")
    def test_download_pdf_success(self, mock_get):
        """Test successful PDF download"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/pdf"}
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

    @patch("rubot.downloader.download_pdf")
    @patch("time.sleep")
    def test_download_pdf_with_backoff_success_first_try(
        self, mock_sleep, mock_download
    ):
        """Test backoff when file is found on first try"""
        mock_download.return_value = "/tmp/test.pdf"

        result = download_pdf_with_backoff("2024-01-15")

        assert result == "/tmp/test.pdf"
        mock_download.assert_called_once_with("2024-01-15", 30)
        mock_sleep.assert_not_called()

    @patch("rubot.downloader.download_pdf")
    @patch("time.sleep")
    def test_download_pdf_with_backoff_success_second_try(
        self, mock_sleep, mock_download
    ):
        """Test backoff when file is found on second try"""
        mock_download.side_effect = [
            FileNotFoundError("PDF not found"),
            "/tmp/test.pdf",
        ]

        result = download_pdf_with_backoff("2024-01-15")

        assert result == "/tmp/test.pdf"
        assert mock_download.call_count == 2
        mock_sleep.assert_called_once_with(5 * 60)  # 5 minutes

    @patch("rubot.downloader.download_pdf")
    @patch("time.sleep")
    def test_download_pdf_with_backoff_all_attempts_fail(
        self, mock_sleep, mock_download
    ):
        """Test backoff when all attempts fail"""
        mock_download.side_effect = FileNotFoundError("PDF not found")

        result = download_pdf_with_backoff("2024-01-15")

        assert result is None
        assert mock_download.call_count == 6  # Initial + 5 retries
        assert mock_sleep.call_count == 5
        # Verify exponential backoff sleep times
        mock_sleep.assert_has_calls(
            [
                call(5 * 60),   # 5 minutes
                call(10 * 60),  # 10 minutes
                call(20 * 60),  # 20 minutes
                call(40 * 60),  # 40 minutes
                call(80 * 60),  # 80 minutes
            ]
        )

    @patch("rubot.downloader.download_pdf")
    @patch("time.sleep")
    def test_download_pdf_with_backoff_request_exception(
        self, mock_sleep, mock_download
    ):
        """Test backoff when request exception occurs"""
        mock_download.side_effect = requests.RequestException(
            "Connection error"
        )

        result = download_pdf_with_backoff("2024-01-15")

        assert result is None
        mock_download.assert_called_once_with("2024-01-15", 30)
        mock_sleep.assert_not_called()
