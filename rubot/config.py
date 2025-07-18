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
    cache_root: Optional[str] = None

    # Network settings
    request_timeout: int = 120
    openrouter_timeout: int = 120
    pdf_timeout: int = 600
    max_retries: int = 3
    retry_delay: float = 1.0

    # Cache settings
    cache_enabled: bool = True
    cache_max_age_hours: int = 24

    # Processing settings
    max_pdf_pages: int = 100

    # Output settings
    output_format: str = "json"
    json_indent: int = 2

    # Docling configuration
    docling_ocr_engine: str = "easyocr"
    docling_do_ocr: bool = True
    docling_do_table_structure: bool = False  # Disabled for faster processing
    docling_model_cache_dir: Optional[str] = None
    docling_image_mode: str = "placeholder"
    docling_image_placeholder: str = "<!-- image -->"

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
            cache_root=os.getenv("CACHE_ROOT"),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "120")),
            openrouter_timeout=int(os.getenv("OPENROUTER_TIMEOUT", "120")),
            pdf_timeout=int(os.getenv("PDF_TIMEOUT", "600")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_max_age_hours=int(os.getenv("CACHE_MAX_AGE_HOURS", "24")),
            max_pdf_pages=int(os.getenv("MAX_PDF_PAGES", "100")),
            output_format=os.getenv("OUTPUT_FORMAT", "json"),
            json_indent=int(os.getenv("JSON_INDENT", "2")),
            # Docling configuration
            docling_ocr_engine=os.getenv("DOCLING_OCR_ENGINE", "easyocr"),
            docling_do_ocr=os.getenv("DOCLING_DO_OCR", "true").lower() == "true",
            docling_do_table_structure=os.getenv("DOCLING_DO_TABLE_STRUCTURE", "false").lower() == "true",
            docling_model_cache_dir=os.getenv("DOCLING_MODEL_CACHE_DIR"),
            docling_image_mode=os.getenv("DOCLING_IMAGE_MODE", "placeholder"),
            docling_image_placeholder=os.getenv("DOCLING_IMAGE_PLACEHOLDER", "<!-- image -->"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "openrouter_api_key": "***" if self.openrouter_api_key else None,
            "default_model": self.default_model,
            "default_prompt_file": self.default_prompt_file,
            "cache_dir": self.cache_dir,
            "cache_root": self.cache_root,
            "request_timeout": self.request_timeout,
            "openrouter_timeout": self.openrouter_timeout,
            "pdf_timeout": self.pdf_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "cache_enabled": self.cache_enabled,
            "cache_max_age_hours": self.cache_max_age_hours,
            "max_pdf_pages": self.max_pdf_pages,
            "output_format": self.output_format,
            "json_indent": self.json_indent,
            "docling_ocr_engine": self.docling_ocr_engine,
            "docling_do_ocr": self.docling_do_ocr,
            "docling_do_table_structure": self.docling_do_table_structure,
            "docling_model_cache_dir": self.docling_model_cache_dir,
            "docling_image_mode": self.docling_image_mode,
            "docling_image_placeholder": self.docling_image_placeholder,
        }


def get_default_config() -> RubotConfig:
    """Get default configuration from environment"""
    return RubotConfig.from_env()
