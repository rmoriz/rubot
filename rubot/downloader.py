"""
PDF downloader module for Rathaus-Umschau
"""

import requests
import tempfile
from .retry import retry_on_failure


def generate_pdf_url(date: str) -> str:
    """
    Generate PDF URL based on date.

    Args:
        date: Date string in YYYY-MM-DD format

    Returns:
        PDF URL string
    """
    year, month, day = date.split("-")
    return f"https://ru.muenchen.de/pdf/{year}/ru-{year}-{month}-{day}.pdf"


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
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Create temporary file in CACHE_ROOT
        import os
        cache_root = os.getenv("CACHE_ROOT", tempfile.gettempdir())
        cache_dir = os.path.join(cache_root, "downloads")
        os.makedirs(cache_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, dir=cache_dir
        ) as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise FileNotFoundError(f"PDF not found for date {date}. URL: {url}")
        raise
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"Failed to download PDF from {url}: {e}")
