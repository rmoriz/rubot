"""
OpenRouter API integration for LLM processing
"""

import requests
import json
import os
import logging
from pathlib import Path
from typing import Optional
from .retry import retry_on_failure


def load_prompt(prompt_path: Optional[str]) -> str:
    """
    Load system prompt from file or environment.

    Args:
        prompt_path: Path to prompt file (optional)

    Returns:
        System prompt string
    """
    if prompt_path and Path(prompt_path).exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    # Fallback to environment variable
    env_prompt = os.getenv("DEFAULT_SYSTEM_PROMPT")
    if env_prompt:
        return env_prompt

    # No default prompt - require explicit configuration
    raise ValueError(
        "System prompt must be specified either via prompt file or DEFAULT_SYSTEM_PROMPT environment variable"
    )


@retry_on_failure(max_retries=2, delay=10.0, exceptions=(requests.RequestException,))
def process_with_openrouter(
    markdown_content: str,
    prompt_path: Optional[str],
    model: Optional[str],
    temperature: float = 0.1,
    max_tokens: int = 4000,
    verbose: bool = False,
    timeout: int = 120,
) -> str:
    """
    Process markdown content with OpenRouter API.

    Args:
        markdown_content: Markdown content to process
        prompt_path: Path to system prompt file (optional)
        model: OpenRouter model ID (optional)
        temperature: LLM temperature setting
        max_tokens: Maximum tokens for response
        verbose: Enable debug output for API requests

    Returns:
        JSON response from OpenRouter API

    Raises:
        requests.RequestException: If API request fails
        ValueError: If API key is missing
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")

    # Model is required
    if not model:
        model = os.getenv("DEFAULT_MODEL")
        if not model:
            raise ValueError(
                "Model must be specified either as parameter or DEFAULT_MODEL environment variable"
            )

    # Load system prompt
    system_prompt = load_prompt(prompt_path)

    # Prepare API request
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/rmoriz/rubot",
        "X-Title": "rubot CLI Tool",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": markdown_content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if verbose:
        logger = logging.getLogger(__name__)
        logger.debug("OpenRouter API Request")
        logger.debug(f"URL: {url}")
        logger.debug(f"Model: {model}")
        logger.debug(f"Temperature: {temperature}")
        logger.debug(f"Max Tokens: {max_tokens}")
        logger.debug(f"Content Length: {len(markdown_content)} characters")
        logger.debug(
            f"System Prompt: {system_prompt[:100]}..."
            if len(system_prompt) > 100
            else f"System Prompt: {system_prompt}"
        )
        logger.debug(f"Headers: {dict(headers)}")
        logger.debug(
            f"Full JSON Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}"
        )

    try:
        response = requests.post(
            url, headers=headers, json=payload, timeout=timeout, verify=True
        )

        if verbose:
            logger = logging.getLogger(__name__)
            logger.debug(f"Response Status: {response.status_code}")
            logger.debug(f"Response Headers: {dict(response.headers)}")
            if response.status_code != 200:
                logger.debug(f"Response Text: {response.text}")
            logger.debug("-" * 50)

        response.raise_for_status()

        response_json = response.json()

        if verbose:
            logger = logging.getLogger(__name__)
            logger.debug("API Response received")
            logger.debug("\nFull JSON Response:")
            logger.debug(json.dumps(response_json, indent=2, ensure_ascii=False))
            logger.debug("-" * 50)

        # Return formatted JSON response
        return json.dumps(response_json, indent=2, ensure_ascii=False)

    except requests.exceptions.Timeout:
        raise requests.RequestException(
            f"OpenRouter API request timed out after {timeout}s"
        )
    except requests.exceptions.ConnectionError:
        raise requests.RequestException("Failed to connect to OpenRouter API")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise requests.RequestException("Invalid OpenRouter API key")
        elif e.response.status_code == 429:
            raise requests.RequestException("OpenRouter API rate limit exceeded")
        elif e.response.status_code >= 500:
            raise requests.RequestException(
                f"OpenRouter API server error ({e.response.status_code})"
            )
        else:
            raise requests.RequestException(
                f"OpenRouter API HTTP error ({e.response.status_code})"
            )
    except requests.exceptions.RequestException as e:
        raise requests.RequestException(f"OpenRouter API request failed: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from OpenRouter API: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error processing OpenRouter API response: {e}")
