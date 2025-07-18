"""
PDF downloader module for Rathaus-Umschau
"""

import requests
import tempfile
import re
import os
import logging
from pathlib import Path
from .retry import retry_on_failure


def validate_date_format(date: str) -> None:
    """Validate date format and ensure it's a valid date."""
    import datetime

    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date}. Use YYYY-MM-DD")


def validate_pdf_url(url: str) -> None:
    """Validate that the PDF URL is from the expected domain."""
    expected_domain = "ru.muenchen.de"
    if not url.startswith(f"https://{expected_domain}"):
        raise ValueError(f"Invalid PDF domain. Expected https://{expected_domain}")


def generate_pdf_url(date: str) -> str:
    """
    Generate PDF URL based on date.

    Args:
        date: Date string in YYYY-MM-DD format

    Returns:
        PDF URL string
    """
    validate_date_format(date)
    year, month, day = date.split("-")
    url = f"https://ru.muenchen.de/pdf/{year}/ru-{year}-{month}-{day}.pdf"
    validate_pdf_url(url)
    return url


@retry_on_failure(max_retries=3, delay=1.0, exceptions=(requests.RequestException,))
def download_pdf(date: str, timeout: int = 30) -> str:
    """
    Download PDF from Rathaus-Umschau website.

    Args:
        date: Date string in YYYY-MM-DD format

    Returns:
        Path to downloaded PDF file

    Raises:
        requests.RequestException: If download fails
        FileNotFoundError: If PDF not found for given date
    """
    url = generate_pdf_url(date)

    try:
        response = requests.get(url, timeout=timeout, verify=True)
        response.raise_for_status()

        # Validate content type
        content_type = response.headers.get("content-type", "")
        if "application/pdf" not in content_type.lower():
            logger = logging.getLogger(__name__)
            logger.warning(f"Unexpected content type: {content_type}")

        # Validate content size
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > 100:  # Warn for files > 100MB
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Large PDF detected: {size_mb:.1f}MB")
            except ValueError:
                pass

        # Create temporary file in CACHE_ROOT
        import os

        cache_root = os.getenv("CACHE_ROOT", tempfile.gettempdir())
        cache_dir = os.path.join(cache_root, "downloads")
        os.makedirs(cache_dir, exist_ok=True)

        # Write with streaming to handle large files
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, dir=cache_dir, mode="wb"
        ) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            return str(tmp_file.name)

    except requests.exceptions.Timeout:
        raise requests.RequestException(
            f"Download timed out after {timeout}s for {url}"
        )
    except requests.exceptions.ConnectionError:
        raise requests.RequestException(f"Connection failed to {url}")
    except requests.exceptions.HTTPError as e:
        if hasattr(e, "response") and e.response is not None:
            status_code = e.response.status_code
        else:
            # Fallback in case response is not available
            status_code = 500

        if status_code == 404:
            raise FileNotFoundError(f"PDF not found for date {date}. URL: {url}")
        elif status_code == 403:
            raise requests.RequestException(f"Access forbidden to {url}")
        elif status_code >= 500:
            raise requests.RequestException(f"Server error ({status_code}) at {url}")
        else:
            raise requests.RequestException(f"HTTP {status_code} at {url}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Failed to download PDF from {url}: {e}")
    except OSError as e:
        raise OSError(f"Failed to write PDF file: {e}")
