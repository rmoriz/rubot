"""
CLI interface for rubot using Click framework
"""

import click
from datetime import datetime
import os
import tempfile
from pathlib import Path

from .downloader import download_pdf, generate_pdf_url
from .marker import convert_pdf_to_markdown
from .llm import process_with_openrouter
from .utils import validate_date
from .config import RubotConfig
from .models import RathausUmschauAnalysis
from .cache import PDFCache


@click.command()
@click.option("--date", default=None, help="Date in YYYY-MM-DD format (default: today)")
@click.option("--output", default=None, help="Output file path for JSON result (default: stdout)")
@click.option("--prompt", default=None, help="Path to prompt file (default: from config)")
@click.option("--model", default=None, help="OpenRouter model ID (default: from config)")
@click.option("--config", default=None, help="Path to config file (default: .env)")
@click.option("--no-cache", is_flag=True, help="Disable PDF caching")
@click.option("--cache-dir", default=None, help="Custom cache directory")
@click.option("--temperature", default=0.1, type=float, help="LLM temperature (0.0-1.0, default: 0.1)")
@click.option("--max-tokens", default=4000, type=int, help="Maximum tokens for LLM response (default: 4000)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(date, output, prompt, model, config, no_cache, cache_dir, temperature, max_tokens, verbose):
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
                if not os.getenv('DEFAULT_SYSTEM_PROMPT'):
                    raise ValueError("Either --prompt parameter, DEFAULT_PROMPT_FILE, or DEFAULT_SYSTEM_PROMPT must be configured")
        
        if model is None:
            model = app_config.default_model
            if not model:
                raise ValueError("Either --model parameter or DEFAULT_MODEL environment variable must be configured")

        # Setup cache
        cache = None
        if not no_cache and app_config.cache_enabled:
            cache_directory = cache_dir or app_config.cache_dir
            if not cache_directory:
                cache_directory = os.path.join(tempfile.gettempdir(), 'rubot_cache')
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
            verbose=verbose
        )

        if verbose:
            click.echo(f"Markdown length: {len(markdown_content)} characters", err=True)

        # Step 3: Process with OpenRouter
        click.echo("Processing with LLM...", err=True)
        
        # Show prompt source and complete content on STDERR
        if prompt:
            click.echo(f"Prompt source: File '{prompt}'", err=True)
            try:
                with open(prompt, 'r', encoding='utf-8') as f:
                    prompt_content = f.read().strip()
                click.echo(f"Prompt content (complete):", err=True)
                click.echo(f"{prompt_content}", err=True)
            except Exception as e:
                click.echo(f"Warning: Could not read prompt file: {e}", err=True)
        else:
            env_prompt = os.getenv('DEFAULT_SYSTEM_PROMPT')
            if env_prompt:
                click.echo(f"Prompt source: Environment variable 'DEFAULT_SYSTEM_PROMPT'", err=True)
                click.echo(f"Prompt content (complete):", err=True)
                click.echo(f"{env_prompt}", err=True)
            else:
                click.echo(f"Prompt source: Unknown", err=True)
        
        llm_response = process_with_openrouter(
            markdown_content, prompt, model, temperature, max_tokens, verbose
        )

        # Step 4: Extract and output JSON content from LLM response
        try:
            # Parse OpenRouter response
            import json
            openrouter_response = json.loads(llm_response)
            
            # Extract the actual content from OpenRouter response
            if 'choices' in openrouter_response and openrouter_response['choices']:
                actual_content = openrouter_response['choices'][0]['message']['content']
                
                # Try to parse the content as JSON
                try:
                    content_json = json.loads(actual_content)
                    # Output the parsed JSON content
                    formatted_json = json.dumps(content_json, indent=2, ensure_ascii=False)
                    
                    if output:
                        with open(output, 'w', encoding='utf-8') as f:
                            f.write(formatted_json)
                        click.echo(f"Extracted JSON content saved to: {output}", err=True)
                    else:
                        # Output extracted JSON to STDOUT
                        print(formatted_json)
                        
                except json.JSONDecodeError:
                    # Content is not valid JSON, output as-is
                    click.echo("Warning: LLM content is not valid JSON, outputting as text", err=True)
                    if output:
                        with open(output, 'w', encoding='utf-8') as f:
                            f.write(actual_content)
                        click.echo(f"LLM text content saved to: {output}", err=True)
                    else:
                        print(actual_content)
            else:
                # No choices in response, output raw response
                if output:
                    with open(output, 'w', encoding='utf-8') as f:
                        f.write(llm_response)
                    click.echo(f"Raw LLM response saved to: {output}", err=True)
                else:
                    print(llm_response)
                    
        except json.JSONDecodeError:
            # Fallback: output raw response if parsing fails
            click.echo("Warning: Could not parse OpenRouter response, outputting raw response", err=True)
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(llm_response)
                click.echo(f"Raw LLM response saved to: {output}", err=True)
            else:
                print(llm_response)
        
        # Optional: Parse and show analysis summary on STDERR if verbose
        if verbose:
            try:
                analysis = RathausUmschauAnalysis.from_llm_response(llm_response, date, model)
                click.echo(f"Analysis summary:", err=True)
                click.echo(f"  - Summary length: {len(analysis.summary)} characters", err=True)
                click.echo(f"  - {len(analysis.announcements)} announcements", err=True)
                click.echo(f"  - {len(analysis.events)} events", err=True)
                click.echo(f"  - {len(analysis.important_dates)} important dates", err=True)
            except Exception as e:
                click.echo(f"Note: Could not parse LLM response as structured data: {e}", err=True)

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