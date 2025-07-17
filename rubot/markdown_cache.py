"""
Markdown cache for PDF conversion results
"""

import os
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
import json


class MarkdownCache:
    """Cache for PDF to Markdown conversion results"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_age_hours: int = 168):  # 1 week default
        """
        Initialize Markdown cache.
        
        Args:
            cache_dir: Directory for cache files (default: system temp)
            max_age_hours: Maximum age of cached files in hours (default: 1 week)
        """
        if cache_dir is None:
            cache_dir = os.path.join(tempfile.gettempdir(), 'rubot_markdown_cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)
    
    def _get_cache_key(self, pdf_path: str) -> str:
        """Generate cache key from PDF file path and modification time"""
        # Get file stats for cache invalidation
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Include file size and modification time in cache key
        stat = pdf_file.stat()
        cache_input = f"{pdf_path}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_cache_paths(self, cache_key: str) -> Tuple[Path, Path]:
        """Get paths for markdown content and metadata files"""
        content_path = self.cache_dir / f"{cache_key}.md"
        meta_path = self.cache_dir / f"{cache_key}_meta.json"
        return content_path, meta_path
    
    def get(self, pdf_path: str) -> Optional[str]:
        """
        Get cached markdown content if exists and not expired.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Cached markdown content or None if not found/expired
        """
        try:
            cache_key = self._get_cache_key(pdf_path)
            content_path, meta_path = self._get_cache_paths(cache_key)
            
            if not content_path.exists() or not meta_path.exists():
                return None
            
            # Check metadata for expiration
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata['cached_at'])
            if datetime.now() - cached_time > self.max_age:
                # Remove expired files
                content_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
                return None
            
            # Return cached content
            with open(content_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    
    def put(self, pdf_path: str, markdown_content: str) -> str:
        """
        Store markdown content in cache.
        
        Args:
            pdf_path: Path to source PDF file
            markdown_content: Markdown content to cache
            
        Returns:
            Cache key used for storage
        """
        cache_key = self._get_cache_key(pdf_path)
        content_path, meta_path = self._get_cache_paths(cache_key)
        
        # Store content
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Store metadata
        metadata = {
            'cached_at': datetime.now().isoformat(),
            'pdf_path': str(pdf_path),
            'content_length': len(markdown_content),
            'cache_key': cache_key
        }
        
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return cache_key
    
    def clear(self) -> None:
        """Clear all cached markdown files"""
        for cache_file in self.cache_dir.glob("*.md"):
            cache_file.unlink()
        for meta_file in self.cache_dir.glob("*_meta.json"):
            meta_file.unlink()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache files.
        
        Returns:
            Number of files removed
        """
        removed = 0
        now = datetime.now()
        
        for meta_file in self.cache_dir.glob("*_meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                cached_time = datetime.fromisoformat(metadata['cached_at'])
                if now - cached_time > self.max_age:
                    # Remove both content and metadata files
                    cache_key = metadata['cache_key']
                    content_path, _ = self._get_cache_paths(cache_key)
                    
                    content_path.unlink(missing_ok=True)
                    meta_file.unlink(missing_ok=True)
                    removed += 2
                    
            except (json.JSONDecodeError, KeyError, FileNotFoundError):
                # Remove corrupted metadata files
                meta_file.unlink(missing_ok=True)
                removed += 1
        
        return removed
    
    def get_cache_info(self) -> dict:
        """Get information about cache contents"""
        content_files = list(self.cache_dir.glob("*.md"))
        meta_files = list(self.cache_dir.glob("*_meta.json"))
        
        total_size = sum(f.stat().st_size for f in content_files)
        
        return {
            'cache_dir': str(self.cache_dir),
            'content_files': len(content_files),
            'meta_files': len(meta_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }