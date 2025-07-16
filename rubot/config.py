"""
Configuration management for rubot
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class RubotConfig:
    """Configuration class for rubot"""

    # API Configuration
    openrouter_api_key: str
    default_model: str

    # File paths
    default_prompt_file: Optional[str] = None
    cache_dir: Optional[str] = None

    # Network settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    # Cache settings
    cache_enabled: bool = True
    cache_max_age_hours: int = 24

    # Processing settings
    max_pdf_pages: int = 100
    batch_multiplier: int = 2

    # Output settings
    output_format: str = "json"
    json_indent: int = 2

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "RubotConfig":
        """
        Load configuration from environment variables.

        Args:
            env_file: Path to .env file (optional)

        Returns:
            RubotConfig instance

        Raises:
            ValueError: If required configuration is missing
        """
        if env_file and Path(env_file).exists():
            load_dotenv(env_file)
        elif Path(".env").exists():
            load_dotenv(".env")

        # Required configuration
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        model = os.getenv("DEFAULT_MODEL")
        if not model:
            raise ValueError("DEFAULT_MODEL environment variable is required")

        return cls(
            openrouter_api_key=api_key,
            default_model=model,
            default_prompt_file=os.getenv("DEFAULT_PROMPT_FILE"),
            cache_dir=os.getenv("CACHE_DIR"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_max_age_hours=int(os.getenv("CACHE_MAX_AGE_HOURS", "24")),
            max_pdf_pages=int(os.getenv("MAX_PDF_PAGES", "100")),
            batch_multiplier=int(os.getenv("BATCH_MULTIPLIER", "2")),
            output_format=os.getenv("OUTPUT_FORMAT", "json"),
            json_indent=int(os.getenv("JSON_INDENT", "2")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "openrouter_api_key": "***" if self.openrouter_api_key else None,
            "default_model": self.default_model,
            "default_prompt_file": self.default_prompt_file,
            "cache_dir": self.cache_dir,
            "request_timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "cache_enabled": self.cache_enabled,
            "cache_max_age_hours": self.cache_max_age_hours,
            "max_pdf_pages": self.max_pdf_pages,
            "batch_multiplier": self.batch_multiplier,
            "output_format": self.output_format,
            "json_indent": self.json_indent,
        }


def get_default_config() -> RubotConfig:
    """Get default configuration from environment"""
    return RubotConfig.from_env()
