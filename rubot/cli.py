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
        # Load configuration
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

        # Use today's date if not specified
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Validate date format
        validate_date(date)

        # Use config defaults if not specified - but require them to be set
        if prompt is None:
            prompt = app_config.default_prompt_file
            if not prompt:
                if not os.getenv("DEFAULT_SYSTEM_PROMPT"):
                    raise ValueError(
                        "Either --prompt parameter, DEFAULT_PROMPT_FILE, or DEFAULT_SYSTEM_PROMPT must be configured"
                    )

        if model is None:
            model = app_config.default_model
            if not model:
                raise ValueError(
                    "Either --model parameter or DEFAULT_MODEL environment variable must be configured"
                )

        # Setup cache
        cache = None
        if not no_cache and app_config.cache_enabled:
            cache_directory = cache_dir or app_config.cache_dir
            if not cache_directory:
                cache_directory = os.path.join(tempfile.gettempdir(), "rubot_cache")
            cache = PDFCache(cache_directory, app_config.cache_max_age_hours)
            if verbose:
                click.echo(f"Cache enabled: {cache.cache_dir}", err=True)

        click.echo(f"Processing Rathaus-Umschau for date: {date}", err=True)
        if verbose:
            click.echo(f"Model: {model}", err=True)
            click.echo(f"Temperature: {temperature}", err=True)
            click.echo(f"Max tokens: {max_tokens}", err=True)

        # Step 1: Download PDF (with caching)
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

        # Step 2: Convert to Markdown
        click.echo("Checking Markdown cache...", err=True)
        markdown_content = convert_pdf_to_markdown(
            pdf_path,
            use_cache=app_config.cache_enabled,
            cache_dir=cache_directory,
            verbose=verbose,
            timeout=app_config.marker_timeout,
        )

        if verbose:
            click.echo(f"Markdown length: {len(markdown_content)} characters", err=True)

        # Step 3: Process with OpenRouter
        click.echo("Processing with LLM...", err=True)

        # Show prompt source on STDERR
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

        llm_response = process_with_openrouter(
            markdown_content,
            prompt,
            model,
            temperature,
            max_tokens,
            verbose,
            app_config.openrouter_timeout,
        )

        # Step 4: Process and output LLM response
        try:
            # Parse OpenRouter response
            import json

            openrouter_response = json.loads(llm_response)

            # Extract the actual content from OpenRouter response
            if "choices" in openrouter_response and openrouter_response["choices"]:
                actual_content = openrouter_response["choices"][0]["message"]["content"]

                # Try to parse the content as JSON and replace it in the response
                try:
                    # Robust JSON extraction using multiple strategies
                    import re

                    cleaned_content = actual_content.strip()

                    # Strategy 1: Extract from markdown code blocks (most robust)
                    code_block_patterns = [
                        r"```json\s*\n(.*?)\n```",  # ```json ... ```
                        r"```\s*\n(.*?)\n```",  # ``` ... ```
                        r"`([^`]*)`",  # `...` (single backticks)
                    ]

                    json_content = None
                    for pattern in code_block_patterns:
                        matches = re.findall(pattern, cleaned_content, re.DOTALL)
                        for match in matches:
                            candidate = match.strip()
                            # Check if this looks like JSON (starts with { or [)
                            if candidate.startswith(("{", "[")):
                                try:
                                    # Test if it's valid JSON
                                    json.loads(candidate)
                                    json_content = candidate
                                    break
                                except json.JSONDecodeError:
                                    continue
                        if json_content:
                            break

                    # Strategy 2: Look for JSON object boundaries in the entire text
                    if not json_content:
                        # Find all potential JSON objects/arrays
                        json_candidates = []

                        # Look for objects {...}
                        brace_count = 0
                        start_idx = -1
                        for i, char in enumerate(cleaned_content):
                            if char == "{":
                                if brace_count == 0:
                                    start_idx = i
                                brace_count += 1
                            elif char == "}":
                                brace_count -= 1
                                if brace_count == 0 and start_idx != -1:
                                    json_candidates.append(
                                        cleaned_content[start_idx : i + 1]
                                    )

                        # Look for arrays [...]
                        bracket_count = 0
                        start_idx = -1
                        for i, char in enumerate(cleaned_content):
                            if char == "[":
                                if bracket_count == 0:
                                    start_idx = i
                                bracket_count += 1
                            elif char == "]":
                                bracket_count -= 1
                                if bracket_count == 0 and start_idx != -1:
                                    json_candidates.append(
                                        cleaned_content[start_idx : i + 1]
                                    )

                        # Test candidates for valid JSON
                        for candidate in json_candidates:
                            try:
                                json.loads(candidate.strip())
                                json_content = candidate.strip()
                                break
                            except json.JSONDecodeError:
                                continue

                    # Use the found JSON content or fall back to original
                    if json_content:
                        cleaned_content = json_content
                    else:
                        # Last resort: try the entire content as-is
                        cleaned_content = cleaned_content

                    content_json = json.loads(cleaned_content)

                    # Replace the string content with parsed JSON in the response
                    openrouter_response["choices"][0]["message"][
                        "content"
                    ] = content_json

                    # Output the complete response with parsed JSON content
                    formatted_response = json.dumps(
                        openrouter_response, indent=2, ensure_ascii=False
                    )

                    if output:
                        with open(output, "w", encoding="utf-8") as f:
                            f.write(formatted_response)
                        click.echo(
                            f"Complete response with parsed JSON saved to: {output}",
                            err=True,
                        )
                    else:
                        # Output complete response with parsed JSON to STDOUT
                        print(formatted_response)

                except json.JSONDecodeError:
                    # Content is not valid JSON, keep original response
                    click.echo(
                        "Note: LLM content is not valid JSON, keeping as text in response",
                        err=True,
                    )
                    if output:
                        with open(output, "w", encoding="utf-8") as f:
                            f.write(llm_response)
                        click.echo(f"Original response saved to: {output}", err=True)
                    else:
                        print(llm_response)
            else:
                # No choices in response, output raw response
                if output:
                    with open(output, "w", encoding="utf-8") as f:
                        f.write(llm_response)
                    click.echo(f"Raw response saved to: {output}", err=True)
                else:
                    print(llm_response)

        except json.JSONDecodeError:
            # Fallback: output raw response if parsing fails
            click.echo(
                "Warning: Could not parse OpenRouter response, outputting raw response",
                err=True,
            )
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(llm_response)
                click.echo(f"Raw response saved to: {output}", err=True)
            else:
                print(llm_response)

        # Optional: Parse and show analysis summary on STDERR if verbose
        if verbose:
            try:
                analysis = RathausUmschauAnalysis.from_llm_response(
                    llm_response, date, model
                )
                click.echo("Analysis summary:", err=True)
                click.echo(
                    f"  - Summary length: {len(analysis.summary)} characters", err=True
                )
                click.echo(f"  - {len(analysis.announcements)} announcements", err=True)
                click.echo(f"  - {len(analysis.events)} events", err=True)
                click.echo(
                    f"  - {len(analysis.important_dates)} important dates", err=True
                )
            except Exception as e:
                click.echo(
                    f"Note: Could not parse LLM response as structured data: {e}",
                    err=True,
                )

        # Cleanup temporary files (but not cached ones)
        if not cache and pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
