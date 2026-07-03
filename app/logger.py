"""Central logging setup for the calculator.

This module owns the one place where Python's `logging` system gets
configured. Everything else in the app simply calls `logging.info(...)`
or `logging.error(...)` and trusts that the messages end up in the log
file named by the configuration.
"""

import logging

from app.calculator_config import CalculatorConfig


def configure_logging(config: CalculatorConfig) -> logging.Logger:
    """Point the logging system at the configured log file.

    Creates the log directory if it does not exist yet, then sets up the
    root logger so every log record is written to the file with a
    timestamp and severity level. Returns the root logger so callers can
    use it directly if they want to.
    """
    config.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=config.log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )
    logger = logging.getLogger()
    logger.info("Logging configured, writing to %s", config.log_file)
    return logger
