from p21api.config import Config
from p21api.odata_client import ODataClient

from gui import show_gui_dialog


def main():
    config = Config()

    if config.should_show_gui:
        data, save_clicked = show_gui_dialog(config=config)
        if not save_clicked or not data:
            return
        merged_data = {**config.model_dump(), **data}
        config = Config.from_gui_input(merged_data)

    assert config.base_url, "Base URL is required"
    assert config.start_date, "Start date is required"

    if not config.has_login:
        raise ValueError("Username and password are required")

    client = ODataClient(config=config)

    # Get the classes of each report in each report group
    report_groups = config.get_report_groups()
    report_classes = [
        report
        for report_group in [report_groups.get(x) for x in config.report_groups]
        for report in report_group or []
    ]

    # Run each report from the list of classes
    for report_class in report_classes:
        report = report_class(
            client=client,
            start_date=config.start_date,
            end_date=config.end_date,
            output_folder=config.output_folder,
            debug=config.debug,
            config=config,
        )
        report.run()


if __name__ == "__main__":
    main()
