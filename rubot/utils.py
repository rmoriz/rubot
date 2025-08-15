"""
Utility functions for rubot
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv


def validate_date(date_str: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        True if valid

    Raises:
        ValueError: If date format is invalid
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        raise ValueError(
            f"Invalid date format: {date_str}. Expected YYYY-MM-DD"
        )

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        raise ValueError(f"Invalid date: {date_str}")


def load_env_config() -> Dict[str, str]:
    """
    Load configuration from .env file.

    Returns:
        Dictionary with configuration values
    """
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    return {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY") or "",
        "DEFAULT_MODEL": os.getenv("DEFAULT_MODEL") or "",
        "DEFAULT_PROMPT_FILE": os.getenv("DEFAULT_PROMPT_FILE") or "",
        "DEFAULT_SYSTEM_PROMPT": os.getenv("DEFAULT_SYSTEM_PROMPT") or "",
    }


def ensure_directory(path: str) -> None:
    """
    Ensure directory exists, create if necessary.

    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)
