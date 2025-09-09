import logging
import traceback
from pathlib import Path
from typing import NoReturn

from p21api.config import Config
from p21api.odata_client import ODataClient

from gui import show_gui_dialog

logger = logging.getLogger(__name__)


class P21APIError(Exception):
    """Base exception for P21 API related errors."""

    pass


class ConfigurationError(P21APIError):
    """Raised when configuration is invalid or incomplete."""

    pass


class ReportExecutionError(P21APIError):
    """Raised when report execution fails."""

    def __init__(self, message: str, exceptions: list[str] | None = None):
        super().__init__(message)
        self.exceptions = exceptions or []


def main() -> NoReturn | None:
    """
    Main entry point for the P21 API data exporter.

    This function:
    1. Loads configuration from environment or shows GUI if needed
    2. Validates required credentials and parameters
    3. Creates an OData client and runs specified reports
    4. Handles exceptions and provides error reporting

    Returns:
        None if GUI is cancelled, otherwise raises exceptions on errors

    Raises:
        ConfigurationError: If required login credentials are missing
        ReportExecutionError: If any reports fail and debug mode is enabled, or
                             if multiple reports fail (collected exceptions)
    """

    import os

    config = Config()

    # Only show GUI if not running under pytest, unless override is set
    suppress_gui = (
        os.environ.get("PYTEST_CURRENT_TEST")
        and os.environ.get("P21API_SUPPRESS_GUI", "1") != "0"
    )
    if config.should_show_gui and not suppress_gui:
        data, save_clicked = show_gui_dialog(config=config)
        if not save_clicked or not data:
            return
        merged_data = {**config.model_dump(), **data}
        config = Config(**merged_data)

    if not config.has_login:
        raise ConfigurationError("Username and password are required")

    # Validate required configuration
    required_fields = {
        "base_url": config.base_url,
        "username": config.username,
        "password": config.password,
        "start_date": config.start_date,
    }

    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        raise ConfigurationError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )

    # At this point we know these are not None due to validation above
    with ODataClient(
        username=config.username,  # type: ignore[arg-type]
        password=config.password,  # type: ignore[arg-type]
        base_url=config.base_url,
        default_page_size=1000,  # Use improved pagination
        logger=logger,  # Pass logger for better debugging
    ) as client:
        # Get the classes of each report in each report group
        report_classes = config.get_reports()

        exceptions: list[str] = []
        raise_exception = config.debug

        # Run each report from the list of classes
        for report_class in report_classes:
            try:
                report = report_class(
                    client=client,
                    start_date=config.start_date,  # type: ignore[arg-type]
                    end_date=config.end_date,
                    output_folder=config.output_folder,
                    debug=config.debug,
                    config=config,
                )
                report.run()
            except Exception as e:
                error_msg = f"Failed to execute {report_class.__name__}: {str(e)}"
                logger.error(error_msg)

                if raise_exception:
                    raise ReportExecutionError(error_msg) from e
                exceptions.append(traceback.format_exc())

        if exceptions:
            logger.error("Configuration: %s", config.model_dump(exclude={"password"}))
            raise ReportExecutionError(
                f"Failed to execute {len(exceptions)} report(s)", exceptions
            )


if __name__ == "__main__":
    import datetime
    import sys
    from pathlib import Path

    # Compose error log filename with timestamp for uniqueness
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"p21api_error_{timestamp}.log"
    log_path = Path.cwd() / log_filename

    # Set up file handler BEFORE any logging occurs, so all logs are captured
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    # Now configure console logging (basicConfig only affects root logger if no
    # handlers exist)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        main()
    except Exception as exc:
        # Gather error details
        error_type = type(exc).__name__
        error_message = str(exc)
        tb = traceback.format_exc()
        log_content = (
            f"\n\nP21 API Exporter Crash Log\n"
            f"Timestamp: {timestamp}\n"
            f"Error Type: {error_type}\n"
            f"Error Message: {error_message}\n"
            f"\nTraceback:\n{tb}\n"
        )
        try:
            # Write crash summary at the end of the log file
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_content)
            logger.error(
                f"A fatal error occurred. Details have been saved to: {log_path}"
            )
            logger.error("Please send this file to support for troubleshooting.")
        except Exception as file_exc:
            logger.error(
                "A fatal error occurred, and the error log could not be written:"
            )
            logger.error(str(file_exc))
            logger.error("Original error:")
            logger.error(log_content)
        finally:
            # Ensure file handler is flushed and closed
            file_handler.flush()
            file_handler.close()
            root_logger.removeHandler(file_handler)
        # Exit with error code
        sys.exit(1)
