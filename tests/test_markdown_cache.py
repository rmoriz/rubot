from rubot.markdown_cache import MarkdownCache
import tempfile, os
import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
import time


def test_markdown_cache_put_get_clear(tmp_path):
    dummy_pdf = tmp_path / "a.pdf"
    dummy_pdf.write_bytes(b"hello world")
    cache = MarkdownCache(cache_dir=str(tmp_path))
    cache.clear()  # make sure clean

    key = cache.put(str(dummy_pdf), "text-md")
    md = cache.get(str(dummy_pdf))
    assert md == "text-md"
    info = cache.get_cache_info()
    assert 'content_files' in info and info['content_files'] > 0
    cache.clear()
    assert cache.get(str(dummy_pdf)) is None


def test_markdown_cache_cleanup_expired(tmp_path):
    import time, json
    dummy_pdf = tmp_path / "b.pdf"
    dummy_pdf.write_bytes(b"data")
    cache = MarkdownCache(cache_dir=str(tmp_path), max_age_hours=0)
    cache.put(str(dummy_pdf), "foo")
    # Simulate expired by modifying meta file
    key = cache._get_cache_key(str(dummy_pdf))
    _, meta_path = cache._get_cache_paths(key)
    with open(meta_path, "r+") as f:
        meta = json.load(f)
        meta['cached_at'] = '2000-01-01T00:00:00'
        f.seek(0); f.truncate(); json.dump(meta, f)
    assert cache.cleanup_expired() > 0


def test_markdown_cache_init_with_cache_root(tmp_path):
    """Test initializing MarkdownCache with a cache_root parameter"""
    cache_root = str(tmp_path)
    cache = MarkdownCache(cache_root=cache_root)
    
    # Verify cache_dir is inside cache_root
    expected_cache_dir = os.path.join(cache_root, "markdown_cache")
    assert str(cache.cache_dir) == expected_cache_dir
    assert os.path.isdir(expected_cache_dir)


def test_markdown_cache_init_default_paths():
    """Test initializing MarkdownCache with default parameters"""
    cache = MarkdownCache()
    
    # Verify default cache_dir is created
    assert os.path.exists(cache.cache_dir)
    assert "rubot_markdown_cache" in str(cache.cache_dir)


def test_markdown_cache_file_not_found():
    """Test handling of non-existent PDF files"""
    cache = MarkdownCache()
    
    with pytest.raises(FileNotFoundError):
        cache._get_cache_key("/nonexistent/file.pdf")
    
    # get() should return None for non-existent files
    assert cache.get("/nonexistent/file.pdf") is None


def test_markdown_cache_get_expired(tmp_path):
    """Test get() with expired cache entry"""
    dummy_pdf = tmp_path / "test_expired.pdf"
    dummy_pdf.write_bytes(b"test content")
    
    # Create cache with very short expiration
    cache = MarkdownCache(cache_dir=str(tmp_path), max_age_hours=0)
    cache.put(str(dummy_pdf), "markdown content")
    
    # Force expiration by modifying metadata
    key = cache._get_cache_key(str(dummy_pdf))
    _, meta_path = cache._get_cache_paths(key)
    with open(meta_path, "r+") as f:
        meta = json.load(f)
        meta['cached_at'] = '2000-01-01T00:00:00'
        f.seek(0)
        f.truncate()
        json.dump(meta, f)
    
    # get() should return None and remove expired files
    assert cache.get(str(dummy_pdf)) is None
    
    # Verify files were removed
    content_path, meta_path = cache._get_cache_paths(key)
    assert not content_path.exists()
    assert not meta_path.exists()


def test_markdown_cache_corrupt_metadata(tmp_path):
    """Test behavior with corrupt metadata files"""
    dummy_pdf = tmp_path / "corrupt_meta.pdf"
    dummy_pdf.write_bytes(b"test data")
    
    cache = MarkdownCache(cache_dir=str(tmp_path))
    cache.put(str(dummy_pdf), "markdown")
    
    # Corrupt metadata file
    key = cache._get_cache_key(str(dummy_pdf))
    _, meta_path = cache._get_cache_paths(key)
    with open(meta_path, "w") as f:
        f.write("{ invalid json }")
    
    # get() should return None for corrupt metadata
    assert cache.get(str(dummy_pdf)) is None
    
    # cleanup_expired should remove corrupt metadata files
    removed = cache.cleanup_expired()
    assert removed > 0
    assert not meta_path.exists()


def test_markdown_cache_get_cache_info(tmp_path):
    """Test get_cache_info() with multiple entries"""
    cache = MarkdownCache(cache_dir=str(tmp_path))
    
    # Create multiple dummy PDFs and larger content to ensure total_size_mb > 0
    for i in range(3):
        pdf_path = tmp_path / f"test{i}.pdf"
        pdf_path.write_bytes(f"content {i}".encode())
        # Write a larger amount of markdown content to ensure size is > 0 MB
        large_content = f"markdown content {i}\n" * 1000
        cache.put(str(pdf_path), large_content)
    
    info = cache.get_cache_info()
    
    assert info["content_files"] == 3
    assert info["meta_files"] == 3
    assert info["total_size_bytes"] > 0
    assert info["total_size_mb"] > 0
    assert info["cache_dir"] == str(tmp_path)


def test_markdown_cache_missing_metadata(tmp_path):
    """Test behavior when metadata file is missing"""
    dummy_pdf = tmp_path / "missing_meta.pdf"
    dummy_pdf.write_bytes(b"test data")
    
    cache = MarkdownCache(cache_dir=str(tmp_path))
    cache.put(str(dummy_pdf), "markdown")
    
    # Delete metadata file but keep content
    key = cache._get_cache_key(str(dummy_pdf))
    content_path, meta_path = cache._get_cache_paths(key)
    meta_path.unlink()
    
    # get() should return None when metadata is missing
    assert cache.get(str(dummy_pdf)) is None
