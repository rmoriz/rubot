"""
Tests for utils module
"""

import pytest
from unittest.mock import patch, mock_open
import os

from rubot.utils import validate_date


class TestUtils:

    def test_validate_date_valid(self):
        """Test valid date validation"""
        assert validate_date("2024-01-15") is True
        assert validate_date("2023-12-31") is True
        assert validate_date("2024-02-29") is True  # Leap year

    def test_validate_date_invalid_format(self):
        """Test invalid date format"""
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("2024-1-15")

        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("24-01-15")

        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date("2024/01/15")

    def test_validate_date_invalid_date(self):
        """Test invalid date values"""
        with pytest.raises(ValueError, match="Invalid date"):
            validate_date("2024-02-30")

        with pytest.raises(ValueError, match="Invalid date"):
            validate_date("2024-13-01")

        with pytest.raises(ValueError, match="Invalid date"):
            validate_date("2023-02-29")  # Not a leap year

    # load_env_config function was removed - tests moved to test_config.py
