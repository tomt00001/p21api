"""Tests for the logging configuration module."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from p21api.environment_config import Environment, LoggingConfig
from p21api.logging_config import (
    ColoredFormatter,
    LoggingContext,
    StructuredFormatter,
    get_logger,
    setup_logging,
    with_logging_level,
)


class TestColoredFormatter:
    """Test the colored console formatter."""

    def test_format_with_colors(self):
        """Test formatting with color codes."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Should contain color codes for INFO level
        assert "\033[32m" in formatted  # Green color
        assert "\033[0m" in formatted  # Reset color
        assert "Test message" in formatted

    def test_format_all_levels(self):
        """Test formatting for all log levels."""
        formatter = ColoredFormatter("%(levelname)s")

        levels = [
            (logging.DEBUG, "\033[36m"),  # Cyan
            (logging.INFO, "\033[32m"),  # Green
            (logging.WARNING, "\033[33m"),  # Yellow
            (logging.ERROR, "\033[31m"),  # Red
            (logging.CRITICAL, "\033[35m"),  # Magenta
        ]

        for level, expected_color in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="",
                lineno=0,
                msg="Test",
                args=(),
                exc_info=None,
            )

            formatted = formatter.format(record)
            assert expected_color in formatted
            assert "\033[0m" in formatted  # Reset color


class TestStructuredFormatter:
    """Test the structured JSON formatter."""

    def test_basic_formatting(self):
        """Test basic JSON formatting."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"

        formatted = formatter.format(record)

        # Should be valid JSON
        import json

        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["function"] == "test_func"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_formatting_with_exception(self):
        """Test formatting with exception information."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except Exception:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.module = "test"
        record.funcName = "test_func"

        formatted = formatter.format(record)

        import json

        data = json.loads(formatted)

        assert "exception" in data
        assert "ValueError: Test exception" in data["exception"]

    def test_formatting_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test_func"
        record.user_id = "12345"
        record.request_id = "abc-def"

        formatted = formatter.format(record)

        import json

        data = json.loads(formatted)

        # Extra fields should be included
        assert data["user_id"] == "12345"
        assert data["request_id"] == "abc-def"


class TestSetupLogging:
    """Test the logging setup function."""

    def test_setup_logging_development(self):
        """Test logging setup for development environment."""
        config = LoggingConfig(level="DEBUG")

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            setup_logging(config, Environment.DEVELOPMENT)

            # Should set debug level
            mock_logger.setLevel.assert_called_with(logging.DEBUG)
            # Should clear existing handlers
            mock_logger.handlers.clear.assert_called_once()
            # Should add handlers
            assert mock_logger.addHandler.call_count >= 1

    def test_setup_logging_production(self):
        """Test logging setup for production environment."""
        config = LoggingConfig(level="INFO")

        with patch("p21api.logging_config.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            setup_logging(config, Environment.PRODUCTION)

            # Verify logger was configured (may be called multiple times)
            assert mock_logger.setLevel.call_count >= 1
            mock_logger.addHandler.assert_called()

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            config = LoggingConfig(level="INFO", file_path=str(log_file))

            with (
                patch("logging.getLogger") as mock_get_logger,
                patch("logging.handlers.RotatingFileHandler") as mock_file_handler,
            ):
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                # Mock file handler to avoid actual file creation
                mock_handler_instance = Mock()
                mock_file_handler.return_value = mock_handler_instance

                setup_logging(config, Environment.DEVELOPMENT)

                # Should add both console and file handlers
                assert mock_logger.addHandler.call_count == 2

    def test_setup_logging_creates_log_directory(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "logs" / "test.log"

            config = LoggingConfig(file_path=str(log_file))

            with (
                patch("logging.getLogger") as mock_get_logger,
                patch("logging.handlers.RotatingFileHandler") as mock_file_handler,
            ):
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                # Mock file handler to avoid actual file creation
                mock_handler_instance = Mock()
                mock_file_handler.return_value = mock_handler_instance

                setup_logging(config, Environment.DEVELOPMENT)

                # Directory should be created
                assert log_file.parent.exists()


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"


class TestLoggingContext:
    """Test the logging context manager."""

    def test_logging_context_temporary_level(self):
        """Test temporary logging level change."""
        logger = logging.getLogger("test_context")
        original_level = logger.level

        context = LoggingContext(logger, logging.DEBUG)

        # Level should not change until entering context
        assert logger.level == original_level

        with context:
            # Level should be changed
            assert logger.level == logging.DEBUG

        # Level should be restored
        assert logger.level == original_level

    def test_logging_context_exception_handling(self):
        """Test that logging level is restored even with exceptions."""
        logger = logging.getLogger("test_context_exception")
        original_level = logger.level

        try:
            with LoggingContext(logger, logging.DEBUG):
                assert logger.level == logging.DEBUG
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Level should still be restored
        assert logger.level == original_level


class TestWithLoggingLevel:
    """Test the with_logging_level function."""

    def test_with_logging_level(self):
        """Test the with_logging_level context manager."""
        logger = logging.getLogger("test_with_level")
        original_level = logger.level

        with with_logging_level(logger, logging.DEBUG):
            assert logger.level == logging.DEBUG

        assert logger.level == original_level

    def test_with_logging_level_returns_logger(self):
        """Test that the context manager returns the logger."""
        logger = logging.getLogger("test_return")

        with with_logging_level(logger, logging.DEBUG) as ctx_logger:
            assert ctx_logger is logger
