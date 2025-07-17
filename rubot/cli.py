"""
CLI interface for rubot using Click framework
"""

import click
from datetime import datetime
import os
import tempfile
from typing import Optional

from .downloader import download_pdf, generate_pdf_url
from .marker import convert_pdf_to_markdown
from .llm import process_with_openrouter
from .utils import validate_date
from .config import RubotConfig
from .models import RathausUmschauAnalysis
from .cache import PDFCache


@click.command()
@click.option("--date", default=None, help="Date in YYYY-MM-DD format (default: today)")
@click.option(
    "--output", default=None, help="Output file path for JSON result (default: stdout)"
)
@click.option(
    "--prompt", default=None, help="Path to prompt file (default: from config)"
)
@click.option(
    "--model", default=None, help="OpenRouter model ID (default: from config)"
)
@click.option("--config", default=None, help="Path to config file (default: .env)")
@click.option("--no-cache", is_flag=True, help="Disable PDF caching")
@click.option("--cache-dir", default=None, help="Custom cache directory")
@click.option(
    "--temperature",
    default=0.1,
    type=float,
    help="LLM temperature (0.0-1.0, default: 0.1)",
)
@click.option(
    "--max-tokens",
    default=4000,
    type=int,
    help="Maximum tokens for LLM response (default: 4000)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
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
) -> None:
    """
    Download Rathaus-Umschau PDF, convert to markdown, and process with LLM.
    """
    try:
        app_config = _load_and_validate_config(config, verbose)
        date = _prepare_date(date)
        prompt, model = _validate_prompt_and_model(prompt, model, app_config)
        cache = _setup_cache(no_cache, cache_dir, app_config, verbose)

        _log_processing_info(date, model, temperature, max_tokens, verbose)

        pdf_path = _download_pdf_with_cache(date, cache, app_config, verbose)
        markdown_content = _convert_to_markdown(
            pdf_path, app_config, cache_dir, verbose
        )

        _log_prompt_source(prompt, verbose)
        llm_response = _process_with_llm(
            markdown_content,
            prompt,
            model,
            temperature,
            max_tokens,
            verbose,
            app_config,
        )

        _handle_output(llm_response, output, verbose, date, model)
        _cleanup_temp_files(cache, pdf_path)

    except Exception as e:
        _handle_error(e, verbose)


def _load_and_validate_config(config: Optional[str], verbose: bool) -> RubotConfig:
    """Load and validate configuration."""
    try:
        app_config = RubotConfig.from_env(config)
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        raise click.Abort()

    if verbose:
        click.echo("Configuration loaded:", err=True)
        config_dict = app_config.to_dict()
        for key, value in config_dict.items():
            click.echo(f"  {key}: {value}", err=True)
        click.echo(err=True)

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

    if model is None:
        model = app_config.default_model
        if not model:
            raise ValueError(
                "Either --model parameter or DEFAULT_MODEL environment "
                "variable must be configured"
            )

    return (prompt, model)


def _setup_cache(
    no_cache: bool, cache_dir: Optional[str], app_config: RubotConfig, verbose: bool
) -> Optional[PDFCache]:
    """Setup PDF cache if enabled."""
    if no_cache or not app_config.cache_enabled:
        return None

    cache_directory = cache_dir or app_config.cache_dir
    if not cache_directory:
        cache_directory = os.path.join(tempfile.gettempdir(), "rubot_cache")

    cache = PDFCache(cache_directory, app_config.cache_max_age_hours)
    if verbose:
        click.echo(f"Cache enabled: {cache.cache_dir}", err=True)

    return cache


def _log_processing_info(
    date: str, model: str, temperature: float, max_tokens: int, verbose: bool
) -> None:
    """Log processing information."""
    click.echo(f"Processing Rathaus-Umschau for date: {date}", err=True)
    if verbose:
        click.echo(f"Model: {model}", err=True)
        click.echo(f"Temperature: {temperature}", err=True)
        click.echo(f"Max tokens: {max_tokens}", err=True)


def _download_pdf_with_cache(
    date: str, cache: Optional[PDFCache], app_config: RubotConfig, verbose: bool
) -> str:
    """Download PDF with caching support."""
    click.echo("Checking PDF cache...", err=True)
    pdf_url = generate_pdf_url(date)

    pdf_path = None
    if cache:
        pdf_path = cache.get(pdf_url)
        if pdf_path:
            click.echo(f"PDF Cache HIT: {pdf_path}", err=True)

    if not pdf_path:
        click.echo("PDF Cache MISS: Downloading...", err=True)
        pdf_path = download_pdf(date, app_config.request_timeout)
        if cache:
            cached_path = cache.put(pdf_url, pdf_path)
            click.echo(f"PDF cached to: {cached_path}", err=True)
        else:
            click.echo(f"PDF downloaded to: {pdf_path}", err=True)

    return pdf_path


def _convert_to_markdown(
    pdf_path: str, app_config: RubotConfig, cache_dir: Optional[str], verbose: bool
) -> str:
    """Convert PDF to markdown."""
    click.echo("Checking Markdown cache...", err=True)
    markdown_content = convert_pdf_to_markdown(
        pdf_path,
        use_cache=app_config.cache_enabled,
        cache_dir=cache_dir,
        verbose=verbose,
        timeout=app_config.marker_timeout,
    )

    if verbose:
        click.echo(f"Markdown length: {len(markdown_content)} characters", err=True)

    return markdown_content


def _log_prompt_source(prompt: Optional[str], verbose: bool) -> None:
    """Log prompt source information."""
    if prompt:
        click.echo(f"Prompt source: File '{prompt}'", err=True)
    else:
        env_prompt = os.getenv("DEFAULT_SYSTEM_PROMPT")
        if env_prompt:
            click.echo(
                "Prompt source: Environment variable 'DEFAULT_SYSTEM_PROMPT'",
                err=True,
            )
        else:
            click.echo("Prompt source: Unknown", err=True)


def _process_with_llm(
    markdown_content: str,
    prompt: Optional[str],
    model: str,
    temperature: float,
    max_tokens: int,
    verbose: bool,
    app_config: RubotConfig,
) -> str:
    """Process content with LLM."""
    click.echo("Processing with LLM...", err=True)
    result = process_with_openrouter(
        markdown_content,
        prompt,
        model,
        temperature,
        max_tokens,
        verbose,
        app_config.openrouter_timeout,
    )
    return str(result)


def _handle_output(
    llm_response: str, output: Optional[str], verbose: bool, date: str, model: str
) -> None:
    """Handle LLM response output and parsing."""
    try:
        import json

        openrouter_response = json.loads(llm_response)

        if "choices" in openrouter_response and openrouter_response["choices"]:
            actual_content = openrouter_response["choices"][0]["message"]["content"]

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
                    formatted_response, output, "Complete response with parsed JSON"
                )

            except json.JSONDecodeError:
                click.echo(
                    "Note: LLM content is not valid JSON, keeping as text in response",
                    err=True,
                )
                _write_output(llm_response, output, "Original response")
        else:
            _write_output(llm_response, output, "Raw response")

    except json.JSONDecodeError:
        click.echo(
            "Warning: Could not parse OpenRouter response, outputting raw response",
            err=True,
        )
        _write_output(llm_response, output, "Raw response")

    if verbose:
        _log_analysis_summary(llm_response, date, model)


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
                    import json

                    json.loads(candidate)
                    return str(candidate)
                except json.JSONDecodeError:
                    continue

    # Strategy 2: Look for JSON object boundaries
    json_candidates = _find_json_candidates(cleaned_content)

    for candidate in json_candidates:
        try:
            import json

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


def _write_output(content: str, output: Optional[str], description: str) -> None:
    """Write content to output file or stdout."""
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"{description} saved to: {output}", err=True)
    else:
        print(content)


def _log_analysis_summary(llm_response: str, date: str, model: str) -> None:
    """Log analysis summary if possible."""
    try:
        analysis = RathausUmschauAnalysis.from_llm_response(llm_response, date, model)
        click.echo("Analysis summary:", err=True)
        click.echo(f"  - Summary length: {len(analysis.summary)} characters", err=True)
        click.echo(f"  - {len(analysis.announcements)} announcements", err=True)
        click.echo(f"  - {len(analysis.events)} events", err=True)
        click.echo(f"  - {len(analysis.important_dates)} important dates", err=True)
    except Exception as e:
        click.echo(
            f"Note: Could not parse LLM response as structured data: {e}",
            err=True,
        )


def _cleanup_temp_files(cache: Optional[PDFCache], pdf_path: Optional[str]) -> None:
    """Cleanup temporary files if not cached."""
    if not cache and pdf_path and os.path.exists(pdf_path):
        os.remove(pdf_path)


def _handle_error(e: Exception, verbose: bool) -> None:
    """Handle and log errors."""
    click.echo(f"Error: {e}", err=True)
    if verbose:
        import traceback

        click.echo(traceback.format_exc(), err=True)
    raise click.Abort()


if __name__ == "__main__":
    main()
