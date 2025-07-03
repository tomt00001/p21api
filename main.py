import logging
import traceback
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
    config = Config()

    if config.should_show_gui:
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
    # Configure logging for when running as script
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
