import logging
import traceback

from p21api.config import Config
from p21api.odata_client import ODataClient

from gui import show_gui_dialog

logger = logging.getLogger(__name__)


def main():
    config = Config()

    if config.should_show_gui:
        data, save_clicked = show_gui_dialog(config=config)
        if not save_clicked or not data:
            return
        merged_data = {**config.model_dump(), **data}
        config = Config(**merged_data)

    if not config.has_login:
        raise ValueError("Username and password are required")

    assert config.base_url, "Base URL is required"
    assert config.username, "Username is required"
    assert config.password, "Password is required"
    assert config.start_date, "Start date is required"

    client = ODataClient(
        username=config.username, password=config.password, base_url=config.base_url
    )

    # Get the classes of each report in each report group
    report_classes = config.get_reports()

    exceptions = []
    raise_exception = config.debug

    # Run each report from the list of classes
    for report_class in report_classes:
        try:
            report = report_class(
                client=client,
                start_date=config.start_date,
                end_date=config.end_date,
                output_folder=config.output_folder,
                debug=config.debug,
                config=config,
            )
            report.run()
        except Exception as e:
            if raise_exception:
                raise e
            exceptions.append(traceback.format_exc())

    if exceptions:
        logger.error("Configuration: %s", config.model_dump(exclude={"password"}))
        raise Exception(exceptions)


if __name__ == "__main__":
    # Configure logging for when running as script
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    main()
