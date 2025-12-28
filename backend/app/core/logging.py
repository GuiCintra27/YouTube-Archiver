"""
Centralized logging configuration for the application.

Usage:
    from app.core.logging import logger

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message", exc_info=True)
"""
import logging
import sys
from typing import Optional

from app.core.request_context import get_request_id


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance
    """
    # Get log level from string
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Default format with timestamp, level, module, and message
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )

    # Create formatter
    formatter = logging.Formatter(
        format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create stream handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    handler.addFilter(_RequestIdFilter())

    # Get root logger for the app
    app_logger = logging.getLogger("yt-archiver")
    app_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    app_logger.handlers.clear()
    app_logger.addHandler(handler)

    # Prevent propagation to root logger
    app_logger.propagate = False

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the given name.

    Args:
        name: Name for the child logger (usually module name)

    Returns:
        Child logger instance
    """
    return logging.getLogger(f"yt-archiver.{name}")


# Initialize the main logger
# Log level will be reconfigured when settings are loaded
logger = setup_logging()


# Module-specific loggers for better categorization
def get_module_logger(module: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        module: Module name (e.g., 'downloads', 'drive', 'library')

    Returns:
        Logger instance for the module
    """
    return get_logger(module)
