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
    use_color: Optional[bool] = None,
) -> logging.Logger:
    """
    Configure and return the application logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        log_format: pretty, text, or json
        use_color: Force enable/disable ANSI colors (pretty/text)

    Returns:
        Configured logger instance
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )

    color_enabled = sys.stdout.isatty() if use_color is None else bool(use_color)

    if log_format == "json":
        formatter: logging.Formatter = _JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    elif log_format == "pretty":
        formatter = _PrettyFormatter(datefmt="%Y-%m-%d %H:%M:%S", use_color=color_enabled)
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


class _PrettyFormatter(logging.Formatter):
    _LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[41m",
    }
    _DIM = "\033[2m"
    _RESET = "\033[0m"

    def __init__(self, datefmt: Optional[str] = None, use_color: bool = True):
        super().__init__(datefmt=datefmt)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt)
        level_name = record.levelname
        location = f"{record.name}:{record.funcName}:{record.lineno}"
        request_id = getattr(record, "request_id", "-")
        message = record.getMessage()

        if self.use_color:
            level_color = self._LEVEL_COLORS.get(record.levelno, "")
            level_text = f"{level_color}{level_name:<8}{self._RESET}"
            time_text = f"{self._DIM}{timestamp}{self._RESET}"
            location_text = f"{self._DIM}{location}{self._RESET}"
            request_text = f"{self._DIM}req:{request_id}{self._RESET}"
        else:
            level_text = f"{level_name:<8}"
            time_text = timestamp
            location_text = location
            request_text = f"req:{request_id}"

        output = f"{time_text} | {level_text} | {request_text:<12} | {location_text} | {message}"

        if record.exc_info:
            output = f"{output}\n{self.formatException(record.exc_info)}"

        return output
