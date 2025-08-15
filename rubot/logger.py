"""
Logging utilities for rubot
"""

import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: str = "rubot",
    level: Optional[str] = None,
    force_stderr: bool = False,
) -> logging.Logger:
    """
    Setup logger with appropriate formatting and level.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set log level from environment or parameter
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    logger.setLevel(numeric_level)

    # Create console handler (always use stderr)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str = "rubot") -> logging.Logger:
    """
    Get configured logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
