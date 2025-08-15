import tempfile, os
from rubot import cli
import logging
import io, sys
from rubot.cache import PDFCache


def test_cleanup_temp_files(tmp_path):
    f = tmp_path / "todelete.txt"
    f.write_text("x")
    logger = logging.getLogger("t")
    cli._cleanup_temp_files(None, str(f), logger)
    assert not f.exists()


def test_log_cache_cleanup_info():
    logger = logging.getLogger("t-logcache")
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    cli._log_cache_cleanup_info(3, False, logger)
    handler.flush()
    log_contents = log_stream.getvalue()
    assert ("3" in log_contents) or ("ENABLED" in log_contents)
    logger.removeHandler(handler)
