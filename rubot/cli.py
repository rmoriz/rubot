"""
CLI interface for rubot using Click framework
"""

import click
from datetime import datetime
import os
import tempfile
import time
import json
import logging
import importlib.metadata
from typing import Optional

from .downloader import download_pdf_with_backoff, generate_pdf_url
from .llm import process_with_openrouter_backoff
from .utils import validate_date
from .config import RubotConfig
from .models import RathausUmschauAnalysis
from .cache import PDFCache
from .logger import setup_logger


_metadata = importlib.metadata.metadata("rubot")
_homepage = _metadata.get("Home-page", "https://github.com/rmoriz/rubot")
_issues = "https://github.com/rmoriz/rubot/issues"

# Try to extract issues URL from project URLs
project_urls = _metadata.get_all("Project-url", [])
for url_line in project_urls:
    if "Issues" in url_line and "=" in url_line:
        _issues = url_line.split("=", 1)[1].strip()
        break


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    help=f"""{_metadata["Summary"]}

Website: {_homepage}
Issues: {_issues}""",
)
@click.version_option(version=importlib.metadata.version("rubot"))
@click.option(
    "--date", default=None, help="Date in YYYY-MM-DD format (default: today)"
)
@click.option(
    "--output",
    default=None,
    help="Output file path for JSON result (default: stdout)",
)
@click.option(
    "--prompt", default=None, help="Path to prompt file (default: from config)"
)
@click.option(
    "--model", default=None, help="OpenRouter model ID (default: from config)"
)
@click.option(
    "--config", default=None, help="Path to config file (default: .env)"
)
@click.option("--no-cache", is_flag=True, help="Disable PDF caching")
@click.option("--cache-dir", default=None, help="Custom cache directory")
@click.option(
    "--temperature",
    default=0.8,
    type=float,
    help="LLM temperature (0.0-1.0, default: 0.8)",
)
@click.option(
    "--max-tokens",
    default=4000,
    type=int,
    help="Maximum tokens for LLM response (default: 4000)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--cache-cleanup-days",
    default=None,
    type=int,
    help="Delete cache files older than N days "
    "(default: 14, env: CACHE_CLEANUP_DAYS)",
)
@click.option(
    "--skip-cleanup",
    is_flag=True,
    help="Skip automatic cache cleanup (env: SKIP_CLEANUP=1)",
)
def main(
    date: Optional[str],
    output: Optional[str],
    prompt: Optional[str],
    model: Optional[str],
    config: Optional[str],
    no_cache: bool,
    cache_dir: Optional[str],
    temperature: float,
    max_tokens: int,
    verbose: bool,
    cache_cleanup_days: Optional[int],
    skip_cleanup: bool,
) -> None:
    """Command implementation - see help text for details."""
    logger = setup_logger(level="DEBUG" if verbose else None)
    if verbose:
        logger.debug("Verbose logging enabled")

    try:
        app_config = _load_and_validate_config(config, logger)
        cache_root = (
            cache_dir
            or app_config.cache_dir
            or os.getenv("CACHE_ROOT", tempfile.gettempdir())
            or "/tmp"
        )
        logger.info(f"Using cache root: {cache_root}")
        date = _prepare_date(date)
        prompt, model = _validate_prompt_and_model(prompt, model, app_config)
        cache = _setup_cache(no_cache, cache_dir, app_config, logger)

        _log_processing_info(date, model, temperature, max_tokens, logger)
        _log_cache_cleanup_info(cache_cleanup_days, skip_cleanup, logger)

        pdf_path = _download_pdf_with_cache(date, cache, app_config, logger)
        markdown_content = _convert_to_markdown(
            pdf_path, app_config, cache_dir, logger
        )

        _log_prompt_source(prompt, logger)
        llm_response = _process_with_llm(
            markdown_content,
            prompt,
            model,
            temperature,
            max_tokens,
            logger,
            app_config,
        )

        _handle_output(llm_response, output, logger, date, model)
        _cleanup_temp_files(cache, pdf_path, logger)
        _cleanup_old_cache_files(
            cache_root, cache_cleanup_days, skip_cleanup, logger
        )

    except Exception as e:
        _handle_error(e, logger)


def _load_and_validate_config(
    config: Optional[str], logger: logging.Logger
) -> RubotConfig:
    """Load and validate configuration."""
    try:
        app_config = RubotConfig.from_env(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise click.Abort()

    logger.debug("Configuration loaded:")
    config_dict = app_config.to_dict()
    for key, value in config_dict.items():
        logger.debug(f"  {key}: {value}")

    return app_config


def _prepare_date(date: Optional[str]) -> str:
    """Prepare and validate date."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    validate_date(date)
    return date


def _validate_prompt_and_model(
    prompt: Optional[str], model: Optional[str], app_config: RubotConfig
) -> tuple[Optional[str], str]:
    """Validate prompt and model configuration."""
    if prompt is None:
        prompt = app_config.default_prompt_file
        if not prompt:
            if not os.getenv("DEFAULT_SYSTEM_PROMPT"):
                raise ValueError(
                    "Either --prompt parameter, DEFAULT_PROMPT_FILE, or "
                    "DEFAULT_SYSTEM_PROMPT must be configured"
                )

    # Early validation: Check if prompt file exists before proceeding
    # This prevents wasting time downloading PDFs if the prompt file is missing
    # Especially important for Docker environments with volume mount issues
    if prompt and not os.path.isfile(prompt):
        raise ValueError(f"Prompt file not found: {prompt}")

    if model is None:
        model = app_config.default_model
        if not model:
            raise ValueError(
                "Either --model parameter or DEFAULT_MODEL environment "
                "variable must be configured"
            )

    return (prompt, model)


def _setup_cache(
    no_cache: bool,
    cache_dir: Optional[str],
    app_config: RubotConfig,
    logger: logging.Logger,
) -> Optional[PDFCache]:
    """Setup PDF cache if enabled."""
    if no_cache or not app_config.cache_enabled:
        logger.debug("Cache disabled")
        return None

    cache_root = (
        cache_dir
        or app_config.cache_dir
        or os.getenv("CACHE_ROOT", tempfile.gettempdir())
        or "/tmp"
    )
    cache = PDFCache(
        cache_root, app_config.cache_max_age_hours, cache_root=cache_root
    )
    logger.info(f"PDF cache enabled: {cache.cache_dir}")

    return cache


def _log_processing_info(
    date: str,
    model: str,
    temperature: float,
    max_tokens: int,
    logger: logging.Logger,
) -> None:
    """Log processing information."""
    logger.info(f"Processing Rathaus-Umschau for date: {date}")
    logger.debug(f"Model: {model}")
    logger.debug(f"Temperature: {temperature}")
    logger.debug(f"Max tokens: {max_tokens}")


def _download_pdf_with_cache(
    date: str,
    cache: Optional[PDFCache],
    app_config: RubotConfig,
    logger: logging.Logger,
) -> str:
    """Download PDF with caching support, keeping original filename."""
    pdf_url = generate_pdf_url(date)
    logger.info(f"PDF URL: {pdf_url}")

    # Generate filename from date
    year, month, day = date.split("-")
    filename = f"ru-{year}-{month}-{day}.pdf"

    pdf_path: str
    if cache:
        # Check if PDF exists with original filename in cache
        pdf_path = os.path.join(cache.cache_dir, filename)
        if os.path.exists(pdf_path):
            from datetime import datetime

            creation_time = os.path.getctime(pdf_path)
            creation_date = datetime.fromtimestamp(creation_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            logger.info(
                f"PDF Cache HIT: {pdf_path} (created: {creation_date})"
            )
            return pdf_path

    logger.info("PDF Cache MISS: Downloading...")
    try:
        downloaded_path: Optional[str] = download_pdf_with_backoff(
            date, app_config.request_timeout
        )
        if downloaded_path is None:
            raise FileNotFoundError(
                f"PDF for date {date} not available after multiple retries"
            )
    except FileNotFoundError as e:
        logger.error(f"PDF not found: {e}")
        raise

    if cache:
        # Move to cache with original filename
        cache_path = os.path.join(cache.cache_dir, filename)
        import shutil

        shutil.move(downloaded_path, cache_path)
        logger.info(f"PDF cached to: {cache_path}")
        return cache_path
    else:
        return downloaded_path


def _convert_to_markdown(
    pdf_path: str,
    app_config: RubotConfig,
    cache_dir: Optional[str],
    logger: logging.Logger,
) -> str:
    """Convert PDF to markdown using Docling with caching."""
    from .docling_converter import DoclingPDFConverter, DoclingConfig
    import hashlib
    import os

    # Create cache directory for markdown
    cache_root = (
        cache_dir
        or app_config.cache_dir
        or os.getenv("CACHE_ROOT", tempfile.gettempdir())
        or "/tmp"
    )
    markdown_cache_dir = os.path.join(cache_root, "markdown")
    os.makedirs(markdown_cache_dir, exist_ok=True)

    # Generate cache key from PDF file (streaming hash)
    hasher = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    content_hash = hasher.hexdigest()

    cache_key = f"{content_hash}_docling.md"
    cache_file = os.path.join(markdown_cache_dir, cache_key)

    # Check if markdown is cached
    if os.path.exists(cache_file):
        cache_age = time.time() - os.path.getmtime(cache_file)
        cache_max_age = app_config.cache_max_age_hours * 3600

        if cache_age < cache_max_age:
            cache_file_size = os.path.getsize(cache_file)
            logger.info(
                f"Markdown Cache HIT: {cache_file} ({cache_file_size:,} bytes)"
            )
            with open(cache_file, "r", encoding="utf-8") as f:
                content = f.read()
                logger.info(
                    f"Markdown loaded from cache: {len(content):,} characters"
                )
                return content
        else:
            logger.info(
                f"Markdown Cache EXPIRED: {cache_file} (age: {cache_age/3600:.1f}h)"
            )
    else:
        logger.info("Markdown Cache MISS: Converting PDF with Docling...")

    # Configure Docling
    logger.info(
        f"Configuring Docling with OCR engine: {app_config.docling_ocr_engine}"
    )
    docling_config = DoclingConfig(
        ocr_engine=app_config.docling_ocr_engine,
        do_ocr=app_config.docling_do_ocr,
        do_table_structure=app_config.docling_do_table_structure,
        image_mode=app_config.docling_image_mode,
        image_placeholder=app_config.docling_image_placeholder,
        use_cpu_only=app_config.docling_use_cpu_only,
        max_image_size=app_config.docling_max_image_size,
    )

    # Convert with Docling
    converter = DoclingPDFConverter(docling_config)
    markdown_content = converter.convert_to_markdown(pdf_path)

    # Cache the markdown
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(
        f"Docling conversion complete: {len(markdown_content):,} characters"
    )
    logger.debug(f"Markdown cached to: {cache_file}")

    return markdown_content


def _log_prompt_source(prompt: Optional[str], logger: logging.Logger) -> None:
    """Log prompt source information."""
    if prompt:
        logger.info(f"Prompt source: File '{prompt}'")
    else:
        env_prompt = os.getenv("DEFAULT_SYSTEM_PROMPT")
        if env_prompt:
            logger.info(
                "Prompt source: Environment variable 'DEFAULT_SYSTEM_PROMPT'"
            )
        else:
            logger.warning("Prompt source: Unknown")


def _process_with_llm(
    markdown_content: str,
    prompt: Optional[str],
    model: str,
    temperature: float,
    max_tokens: int,
    logger: logging.Logger,
    app_config: RubotConfig,
) -> str:
    """Process content with LLM."""
    logger.info(f"Processing with LLM ({model})...")
    result = process_with_openrouter_backoff(
        markdown_content,
        prompt,
        model,
        temperature,
        max_tokens,
        logger.level <= logging.DEBUG,  # Use debug flag from logger
        app_config.openrouter_timeout,
        app_config.fallback_model,  # Pass fallback model from config
    )
    return str(result)


def _handle_output(
    llm_response: str,
    output: Optional[str],
    logger: logging.Logger,
    date: str,
    model: str,
) -> None:
    """Handle LLM response output and parsing."""
    try:
        openrouter_response = json.loads(llm_response)

        if "choices" in openrouter_response and openrouter_response["choices"]:
            actual_content = openrouter_response["choices"][0]["message"][
                "content"
            ]

            try:
                json_content = _extract_json_from_content(actual_content)
                if json_content:
                    content_json = json.loads(json_content)
                    openrouter_response["choices"][0]["message"][
                        "content"
                    ] = content_json

                formatted_response = json.dumps(
                    openrouter_response, indent=2, ensure_ascii=False
                )
                _write_output(
                    formatted_response,
                    output,
                    "Complete response with parsed JSON",
                    logger,
                )

            except json.JSONDecodeError:
                logger.info(
                    "LLM content is not valid JSON, keeping as text in response"
                )
                _write_output(
                    llm_response, output, "Original response", logger
                )
        else:
            _write_output(llm_response, output, "Raw response", logger)

    except json.JSONDecodeError:
        logger.warning(
            "Could not parse OpenRouter response, outputting raw response"
        )
        _write_output(llm_response, output, "Raw response", logger)

    if logger.level <= logging.DEBUG:
        _log_analysis_summary(llm_response, date, model, logger)


def _extract_json_from_content(content: str) -> Optional[str]:
    """Extract JSON content from LLM response using multiple strategies."""
    import re

    cleaned_content = content.strip()

    # Strategy 1: Extract from markdown code blocks
    code_block_patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
        r"`([^`]*)`",
    ]

    for pattern in code_block_patterns:
        matches = re.findall(pattern, cleaned_content, re.DOTALL)
        for match in matches:
            candidate = match.strip()
            if candidate.startswith(("{", "[")):
                try:
                    json.loads(candidate)
                    return str(candidate)
                except json.JSONDecodeError:
                    continue

    # Strategy 2: Look for JSON object boundaries
    json_candidates = _find_json_candidates(cleaned_content)

    for candidate in json_candidates:
        try:
            json.loads(candidate.strip())
            return str(candidate.strip())
        except json.JSONDecodeError:
            continue

    return None


def _find_json_candidates(content: str) -> list[str]:
    """Find potential JSON objects/arrays in content."""
    candidates = []
    candidates.extend(_find_json_objects(content))
    candidates.extend(_find_json_arrays(content))
    return candidates


def _find_json_objects(content: str) -> list[str]:
    """Find JSON objects {...} in content."""
    candidates = []
    brace_count = 0
    start_idx = -1

    for i, char in enumerate(content):
        if char == "{":
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                candidates.append(content[start_idx : i + 1])

    return candidates


def _find_json_arrays(content: str) -> list[str]:
    """Find JSON arrays [...] in content."""
    candidates = []
    bracket_count = 0
    start_idx = -1

    for i, char in enumerate(content):
        if char == "[":
            if bracket_count == 0:
                start_idx = i
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0 and start_idx != -1:
                candidates.append(content[start_idx : i + 1])

    return candidates


def _write_output(
    content: str,
    output: Optional[str],
    description: str,
    logger: logging.Logger,
) -> None:
    """Write content to output file or stdout."""
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"{description} saved to: {output}")
    else:
        print(content)


def _log_cache_cleanup_info(
    cache_cleanup_days: Optional[int],
    skip_cleanup: bool,
    logger: logging.Logger,
) -> None:
    """Log cache cleanup information."""
    if skip_cleanup or os.getenv("SKIP_CLEANUP") == "1":
        logger.info("Cache cleanup: DISABLED (skipped by user request)")
    else:
        days = cache_cleanup_days or int(os.getenv("CACHE_CLEANUP_DAYS", "14"))
        if days <= 0:
            logger.info("Cache cleanup: DISABLED (days <= 0)")
        else:
            logger.info(
                f"Cache cleanup: ENABLED (files older than {days} days will be removed)"
            )


def _log_analysis_summary(
    llm_response: str, date: str, model: str, logger: logging.Logger
) -> None:
    """Log analysis summary if possible."""
    try:
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response, date, model
        )
        logger.debug("Analysis summary:")
        logger.debug(f"  - Summary length: {len(analysis.summary)} characters")
        logger.debug(f"  - {len(analysis.announcements)} announcements")
        logger.debug(f"  - {len(analysis.events)} events")
        logger.debug(f"  - {len(analysis.important_dates)} important dates")
    except Exception as e:
        logger.debug(f"Could not parse LLM response as structured data: {e}")


def _cleanup_temp_files(
    cache: Optional[PDFCache], pdf_path: Optional[str], logger: logging.Logger
) -> None:
    """Cleanup temporary files if not cached."""
    if not cache and pdf_path and os.path.exists(pdf_path):
        os.remove(pdf_path)
        logger.debug(f"Cleaned up temporary file: {pdf_path}")


def _handle_error(e: Exception, logger: logging.Logger) -> None:
    """Handle and log errors."""
    error_msg = f"Error: {e}"
    logger.error(error_msg)
    logger.debug("Full traceback:", exc_info=True)
    # Also output to stderr for CLI visibility
    click.echo(error_msg, err=True)
    raise click.Abort()


def _cleanup_old_cache_files(
    cache_root: str,
    cache_cleanup_days: Optional[int],
    skip_cleanup: bool,
    logger: logging.Logger,
) -> None:
    """Clean up old cache files based on age."""
    if skip_cleanup or os.getenv("SKIP_CLEANUP") == "1":
        logger.debug("Cache cleanup skipped by user request")
        return

    days = cache_cleanup_days or int(os.getenv("CACHE_CLEANUP_DAYS", "14"))
    if days <= 0:
        logger.debug("Cache cleanup disabled (days <= 0)")
        return

    cutoff_time = time.time() - (days * 24 * 3600)

    # Clean up PDF cache
    pdf_cache_dir = os.path.join(cache_root, "pdf_cache")
    _cleanup_directory_by_age(pdf_cache_dir, cutoff_time, logger, "PDF")

    # Clean up markdown cache
    markdown_cache_dir = os.path.join(cache_root, "markdown")
    _cleanup_directory_by_age(
        markdown_cache_dir, cutoff_time, logger, "Markdown"
    )

    # Clean up downloads cache
    downloads_cache_dir = os.path.join(cache_root, "downloads")
    _cleanup_directory_by_age(
        downloads_cache_dir, cutoff_time, logger, "Downloads"
    )


def _cleanup_directory_by_age(
    directory: str, cutoff_time: float, logger: logging.Logger, name: str
) -> None:
    """Clean up files in a directory older than cutoff time."""
    if not os.path.exists(directory):
        return

    removed_count = 0
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if (
            os.path.isfile(filepath)
            and os.path.getmtime(filepath) < cutoff_time
        ):
            try:
                os.remove(filepath)
                removed_count += 1
            except (OSError, IOError) as e:
                logger.warning(
                    f"Could not remove {name} cache file {filepath}: {e}"
                )

    if removed_count > 0:
        logger.info(
            f"Cleaned up {removed_count} old {name} cache files (older than {int((time.time() - cutoff_time) / (24 * 3600))} days)"
        )
    else:
        logger.debug(f"No old {name} cache files to clean up")


if __name__ == "__main__":
    main()
