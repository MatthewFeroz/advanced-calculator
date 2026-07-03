"""Tests for the logging setup module."""

import logging

from app.calculator_config import CalculatorConfig
from app.logger import configure_logging


def test_configure_logging_creates_log_file(tmp_path):
    """Configuring logging should create the directory and log file."""
    config = CalculatorConfig(base_dir=tmp_path, auto_save=False)
    configure_logging(config)
    logging.shutdown()
    assert config.log_file.exists()
    contents = config.log_file.read_text(encoding=config.default_encoding)
    assert "Logging configured" in contents


def test_messages_are_written_with_level(tmp_path):
    """Log records should include their severity level in the file."""
    config = CalculatorConfig(base_dir=tmp_path, auto_save=False)
    logger = configure_logging(config)
    logger.warning("watch out")
    logging.shutdown()
    contents = config.log_file.read_text(encoding=config.default_encoding)
    assert "WARNING" in contents
    assert "watch out" in contents
