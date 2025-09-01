"""
OpenRouter API integration for LLM processing
"""

import requests
import json
import os
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, cast


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
            logger.debug(
                json.dumps(response_json, indent=2, ensure_ascii=False)
            )
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
            raise requests.RequestException(
                "OpenRouter API rate limit exceeded"
            )
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
        raise RuntimeError(
            f"Unexpected error processing OpenRouter API response: {e}"
        )


def is_valid_openrouter_response(response_json: Dict[str, Any]) -> bool:
    """
    Check if OpenRouter response is valid and contains content.

    Args:
        response_json: The OpenRouter response JSON

    Returns:
        True if response is valid, False otherwise
    """
    # Check if the response has the expected structure
    if "choices" not in response_json or not response_json["choices"]:
        return False

    # Check if content exists and is not empty
    content = response_json["choices"][0].get("message", {}).get("content")
    if content is None or content.strip() == "":
        return False

    return True


def process_with_openrouter_backoff(
    markdown_content: str,
    prompt_path: Optional[str],
    model: Optional[str],
    temperature: float = 0.1,
    max_tokens: int = 4000,
    verbose: bool = False,
    timeout: int = 120,
    fallback_model: Optional[str] = None,
) -> str:
    """
    Process markdown content with OpenRouter API using retry mechanism with fallback model.

    Will retry 3 times with the primary model with progressive delays optimized for rate limits:
    1. Immediate retry (0s delay)
    2. Wait 30 seconds and retry
    3. Wait 60 seconds and retry  
    4. Wait 120 seconds and retry
    
    If all retries with the primary model fail and a fallback model is provided,
    it will attempt to use the fallback model as a last resort.

    Args:
        markdown_content: Markdown content to process
        prompt_path: Path to system prompt file (optional)
        model: OpenRouter model ID (optional)
        temperature: LLM temperature setting
        max_tokens: Maximum tokens for response
        verbose: Enable debug output for API requests
        timeout: API request timeout in seconds
        fallback_model: Fallback model to use if primary model fails (optional)

    Returns:
        JSON response from OpenRouter API

    Raises:
        requests.RequestException: If all API requests fail
        ValueError: If API key is missing or responses are invalid
    """
    logger = logging.getLogger(__name__)
    max_retries = 3
    # Progressive retry delays: 0s, 30s, 60s, 120s (better for rate limits)
    retry_delays = [0, 30, 60, 120]  # seconds
    
    # Determine the primary model to use
    primary_model = model or os.getenv("DEFAULT_MODEL")
    if not primary_model:
        raise ValueError(
            "Model must be specified either as parameter or DEFAULT_MODEL environment variable"
        )

    # First attempt with primary model
    try:
        logger.info(f"OpenRouter request - first attempt with model: {primary_model}")
        response = process_with_openrouter(
            markdown_content,
            prompt_path,
            primary_model,
            temperature,
            max_tokens,
            verbose,
            timeout,
        )

        # Parse response to check if it's valid
        response_json = json.loads(response)
        if is_valid_openrouter_response(response_json):
            logger.info("OpenRouter request successful on first attempt")
            return cast(str, response)
        else:
            error_msg = "Empty or invalid content in OpenRouter response"
            logger.warning(f"{error_msg} on first attempt")

    except (
        requests.RequestException,
        ValueError,
        json.JSONDecodeError,
    ) as e:
        logger.warning(f"OpenRouter request failed on first attempt: {e}")

    # Retry attempts with primary model and progressive delays
    last_exception = None
    for attempt in range(max_retries):
        delay = retry_delays[attempt + 1]  # Skip first delay (0s) since we already tried
        if delay > 0:
            logger.info(f"Waiting {delay} seconds before retry #{attempt+1}...")
            time.sleep(delay)
        else:
            logger.info(f"Immediate retry #{attempt+1} (no delay)")

        try:
            logger.info(f"OpenRouter retry attempt #{attempt+1} with model: {primary_model}")
            response = process_with_openrouter(
                markdown_content,
                prompt_path,
                primary_model,
                temperature,
                max_tokens,
                verbose,
                timeout,
            )

            # Parse response to check if it's valid
            response_json = json.loads(response)
            if is_valid_openrouter_response(response_json):
                logger.info(f"OpenRouter request successful on retry #{attempt+1}")
                return cast(str, response)
            else:
                error_msg = "Empty or invalid content in OpenRouter response"
                logger.warning(f"{error_msg} on retry #{attempt+1}")
                last_exception = ValueError(error_msg)

        except (
            requests.RequestException,
            ValueError,
            json.JSONDecodeError,
        ) as e:
            logger.warning(f"OpenRouter request failed on retry #{attempt+1}: {e}")
            last_exception = e

    # All retries with primary model failed, try fallback model if available
    if fallback_model and fallback_model != primary_model:
        logger.warning(f"All attempts with primary model '{primary_model}' failed")
        logger.info(f"Attempting fallback to model: {fallback_model}")
        
        try:
            response = process_with_openrouter(
                markdown_content,
                prompt_path,
                fallback_model,
                temperature,
                max_tokens,
                verbose,
                timeout,
            )

            # Parse response to check if it's valid
            response_json = json.loads(response)
            if is_valid_openrouter_response(response_json):
                logger.info(f"OpenRouter request successful with fallback model: {fallback_model}")
                return cast(str, response)
            else:
                error_msg = "Empty or invalid content in OpenRouter response from fallback model"
                logger.error(error_msg)
                raise ValueError(error_msg)

        except (
            requests.RequestException,
            ValueError,
            json.JSONDecodeError,
        ) as e:
            logger.error(f"Fallback model '{fallback_model}' also failed: {e}")
            # Raise the last exception from the primary model attempts
            if last_exception:
                raise last_exception
            raise e
    else:
        if fallback_model == primary_model:
            logger.warning("Fallback model is the same as primary model, skipping fallback attempt")
        elif not fallback_model:
            logger.warning("No fallback model configured")
        
        logger.error(f"All {max_retries + 1} OpenRouter attempts failed with model '{primary_model}'")
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected end of OpenRouter retry loop")
