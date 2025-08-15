from rubot.logger import setup_logger, get_logger
import logging


def test_setup_logger_sets_level_and_format(monkeypatch):
    logger = setup_logger("test", level="DEBUG")
    assert logger.level == logging.DEBUG
    logger.debug("debug msg")
    assert any(
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    )


def test_get_logger_returns_same_instance():
    l1 = setup_logger("foobar", level="INFO")
    l2 = get_logger("foobar")
    assert l1 is l2
