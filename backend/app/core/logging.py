"""
Centralized logging configuration for the application.

Usage:
    from app.core.logging import logger

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message", exc_info=True)
"""
import json
import logging
import sys
from typing import Optional

from app.core.request_context import get_request_id


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_format: str = "text",
) -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_format: text or json

    Returns:
        Configured logger instance
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )

    if log_format == "json":
        formatter: logging.Formatter = _JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    handler.addFilter(_RequestIdFilter())

    app_logger = logging.getLogger("yt-archiver")
    app_logger.setLevel(log_level)

    app_logger.handlers.clear()
    app_logger.addHandler(handler)

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


logger = setup_logging()


def get_module_logger(module: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        module: Module name (e.g., 'downloads', 'drive', 'library')

    Returns:
        Logger instance for the module
    """
    return get_logger(module)
