"""
Centralized logging configuration for P21 API application.

This module provides structured logging setup with different handlers,
formatters, and configuration options for various environments.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from .environment_config import Environment, LoggingConfig


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    # ANSI color codes
    COLORS: dict[str, str] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """Structured formatter for JSON-like log output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as structured data."""
        import json

        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(
    config: LoggingConfig,
    environment: Environment = Environment.DEVELOPMENT,
    app_name: str = "p21api",
) -> None:
    """
    Setup application logging based on configuration.

    Args:
        config: Logging configuration
        environment: Current environment
        app_name: Application name for log files
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if environment == Environment.DEVELOPMENT:
        # Colored formatter for development
        console_formatter: logging.Formatter = ColoredFormatter(config.format)
    else:
        # Standard formatter for production
        console_formatter = logging.Formatter(config.format)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if config.file_path:
        # Ensure log directory exists
        log_file = Path(config.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
        )

        if environment == Environment.PRODUCTION:
            # Structured logging for production
            file_formatter: logging.Formatter = StructuredFormatter()
        else:
            # Standard formatting for development/testing
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Set specific logger levels
    _configure_logger_levels(environment)

    # Log the logging setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized for {environment.value} environment")
    logger.debug(f"Log level: {config.level}")
    if config.file_path:
        logger.debug(f"Log file: {config.file_path}")


def _configure_logger_levels(environment: Environment) -> None:
    """Configure specific logger levels based on environment."""

    if environment == Environment.PRODUCTION:
        # Reduce noise in production
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("PyQt6").setLevel(logging.ERROR)
    elif environment == Environment.TESTING:
        # Minimal logging during tests
        logging.getLogger("requests").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.getLogger("PyQt6").setLevel(logging.CRITICAL)
    else:  # Development
        # Verbose logging for development
        logging.getLogger("p21api").setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent naming.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggingContext:
    """Context manager for temporary logging configuration."""

    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.original_level = logger.level

    def __enter__(self) -> logging.Logger:
        self.logger.setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.logger.setLevel(self.original_level)


def with_logging_level(logger: logging.Logger, level: int) -> LoggingContext:
    """
    Context manager to temporarily change logging level.

    Usage:
        with with_logging_level(logger, logging.DEBUG):
            # Debug logging enabled
            logger.debug("This will be logged")
    """
    return LoggingContext(logger, level)
