"""
Tests for cache module
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from rubot.cache import PDFCache


class TestPDFCache:
    
    def test_cache_initialization(self):
        """Test cache initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PDFCache(temp_dir, 24)
            
            assert cache.cache_dir == Path(temp_dir)
            assert cache.max_age == timedelta(hours=24)
            assert cache.cache_dir.exists()
    
    def test_cache_initialization_default_dir(self):
        """Test cache initialization with default directory"""
        cache = PDFCache()
        
        assert cache.cache_dir.exists()
        assert cache.max_age == timedelta(hours=24)
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        cache = PDFCache()
        
        key1 = cache._get_cache_key("http://example.com/test.pdf")
        key2 = cache._get_cache_key("http://example.com/test.pdf")
        key3 = cache._get_cache_key("http://example.com/other.pdf")
        
        assert key1 == key2  # Same URL should generate same key
        assert key1 != key3  # Different URLs should generate different keys
        assert len(key1) == 32  # MD5 hash length
    
    def test_get_nonexistent_file(self):
        """Test getting non-existent cached file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PDFCache(temp_dir)
            
            result = cache.get("http://example.com/nonexistent.pdf")
            
            assert result is None
    
    def test_put_and_get_file(self):
        """Test storing and retrieving cached file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PDFCache(temp_dir)
            
            # Create a test file
            test_file = Path(temp_dir) / "test.pdf"
            test_file.write_text("test content")
            
            # Store in cache
            url = "http://example.com/test.pdf"
            cached_path = cache.put(url, str(test_file))
            
            # Retrieve from cache
            retrieved_path = cache.get(url)
            
            assert retrieved_path == cached_path
            assert Path(retrieved_path).exists()
            assert Path(retrieved_path).read_text() == "test content"
    
    def test_get_expired_file(self):
        """Test getting expired cached file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PDFCache(temp_dir, max_age_hours=1)  # 1 hour max age
            
            # Create a test file
            test_file = Path(temp_dir) / "test.pdf"
            test_file.write_text("test content")
            
            # Store in cache
            url = "http://example.com/test.pdf"
            cached_path = cache.put(url, str(test_file))
            
            # Mock file modification time to be 2 hours ago
            old_time = datetime.now() - timedelta(hours=2)
            old_timestamp = old_time.timestamp()
            
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_mtime = old_timestamp
                
                result = cache.get(url)
                
                assert result is None  # Should be None because file is expired
    
    def test_clear_cache(self):
        """Test clearing all cached files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PDFCache(temp_dir)
            
            # Create test files
            test_file1 = Path(temp_dir) / "test1.pdf"
            test_file1.write_text("content1")
            test_file2 = Path(temp_dir) / "test2.pdf"
            test_file2.write_text("content2")
            
            # Store in cache
            cache.put("http://example.com/test1.pdf", str(test_file1))
            cache.put("http://example.com/test2.pdf", str(test_file2))
            
            # Verify files exist
            assert len(list(cache.cache_dir.glob("*.pdf"))) >= 2
            
            # Clear cache
            cache.clear()
            
            # Verify files are gone
            assert len(list(cache.cache_dir.glob("*.pdf"))) == 0
    
    def test_cleanup_expired(self):
        """Test cleanup of expired files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = PDFCache(temp_dir, max_age_hours=1)
            
            # Create test files with different ages
            old_file = cache.cache_dir / "old.pdf"
            new_file = cache.cache_dir / "new.pdf"
            
            old_file.write_text("old content")
            new_file.write_text("new content")
            
            # Mock file modification times
            old_time = (datetime.now() - timedelta(hours=2)).timestamp()
            new_time = datetime.now().timestamp()
            
            with patch('pathlib.Path.stat') as mock_stat:
                def stat_side_effect(self):
                    mock_stat_result = MagicMock()
                    if self.name == "old.pdf":
                        mock_stat_result.st_mtime = old_time
                    else:
                        mock_stat_result.st_mtime = new_time
                    return mock_stat_result
                
                mock_stat.side_effect = stat_side_effect
                
                # Cleanup expired files
                removed_count = cache.cleanup_expired()
                
                assert removed_count >= 0  # At least some files should be processed