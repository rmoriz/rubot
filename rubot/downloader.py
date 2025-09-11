"""
PDF downloader module for Rathaus-Umschau
"""

import requests
import tempfile
import os
import logging
import time
from typing import Optional, cast


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
        raise ValueError(
            f"Invalid PDF domain. Expected https://{expected_domain}"
        )


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
            raise FileNotFoundError(
                f"PDF not found for date {date}. URL: {url}"
            )
        elif status_code == 403:
            raise requests.RequestException(f"Access forbidden to {url}")
        elif status_code >= 500:
            raise requests.RequestException(
                f"Server error ({status_code}) at {url}"
            )
        else:
            raise requests.RequestException(f"HTTP {status_code} at {url}")
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(
            f"Failed to download PDF from {url}: {e}"
        )
    except OSError as e:
        raise OSError(f"Failed to write PDF file: {e}")


def download_pdf_with_backoff(
    date: str, timeout: int = 30, max_retries: int = 4, base_delay: int = 30
) -> Optional[str]:
    """
    Download PDF with exponential backoff retry mechanism.

    Args:
        date: Date string in YYYY-MM-DD format
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts (default: 4)
        base_delay: Base delay in seconds for first retry (default: 30 seconds)

    Returns:
        Path to downloaded PDF file or None if all attempts failed
    """
    logger = logging.getLogger(__name__)

    # Retry attempts with exponential backoff (including first attempt)
    for attempt in range(max_retries + 1):
        try:
            result = download_pdf(date, timeout)
            if attempt > 0:
                logger.info(f"PDF successfully downloaded on attempt #{attempt+1}")
            return cast(str, result)
        except FileNotFoundError as e:
            if attempt == 0:
                logger.info(f"PDF not available on first attempt: {e}")
            else:
                logger.info(f"PDF still not available on attempt #{attempt+1}: {e}")
            
            if attempt == max_retries:
                logger.error("Maximum retries reached, PDF not available")
                return None
            
            # Wait before next retry
            wait_time = base_delay * (2 ** attempt)
            logger.info(
                f"Waiting {wait_time/60:.1f} minutes before retry #{attempt+2}..."
            )
            time.sleep(wait_time)
            
        except (requests.RequestException, OSError) as e:
            logger.error(f"Error downloading PDF on attempt #{attempt+1}: {e}")
            return None

    return None


def download_pdf_with_short_retries(date: str, timeout: int = 30) -> Optional[str]:
    """
    Download PDF with shorter retry intervals suitable for automated/scheduled runs.
    
    Retries with shorter delays: 30s, 1min, 2min, 4min
    Total retry time: ~7.5 minutes
    
    Args:
        date: Date string in YYYY-MM-DD format
        timeout: Request timeout in seconds

    Returns:
        Path to downloaded PDF file or None if all attempts failed
    """
    return download_pdf_with_backoff(
        date=date, 
        timeout=timeout, 
        max_retries=4, 
        base_delay=30  # 30 seconds base delay: 30s, 1min, 2min, 4min
    )
