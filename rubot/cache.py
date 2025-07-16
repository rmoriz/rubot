"""
Simple file-based caching for downloaded PDFs
"""

import os
import hashlib
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


class PDFCache:
    """Simple file-based cache for downloaded PDFs"""

    def __init__(self, cache_dir: Optional[str] = None, max_age_hours: int = 24):
        """
        Initialize PDF cache.

        Args:
            cache_dir: Directory for cache files (default: system temp)
            max_age_hours: Maximum age of cached files in hours
        """
        if cache_dir is None:
            cache_dir = os.path.join(tempfile.gettempdir(), "rubot_cache")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get full path for cache file"""
        return self.cache_dir / f"{cache_key}.pdf"

    def get(self, url: str) -> Optional[str]:
        """
        Get cached PDF file path if exists and not expired.

        Args:
            url: PDF URL

        Returns:
            Path to cached file or None if not found/expired
        """
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        # Check if file is too old
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - file_time > self.max_age:
            cache_path.unlink()  # Remove expired file
            return None

        return str(cache_path)

    def put(self, url: str, file_path: str) -> str:
        """
        Store file in cache.

        Args:
            url: PDF URL
            file_path: Path to file to cache

        Returns:
            Path to cached file
        """
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        # Copy file to cache
        import shutil

        shutil.copy2(file_path, cache_path)

        return str(cache_path)

    def clear(self) -> None:
        """Clear all cached files"""
        for cache_file in self.cache_dir.glob("*.pdf"):
            cache_file.unlink()

    def cleanup_expired(self) -> int:
        """
        Remove expired cache files.

        Returns:
            Number of files removed
        """
        removed = 0
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*.pdf"):
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if now - file_time > self.max_age:
                cache_file.unlink()
                removed += 1

        return removed
