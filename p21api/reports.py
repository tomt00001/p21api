from typing import TYPE_CHECKING

from .odata_client import ODataClient

if TYPE_CHECKING:
    from .config import Config


def do_reports(
    client: "ODataClient",
    config: "Config",
) -> None:
    # Get the classes of each report in each report group
    report_groups = config.get_report_groups()
    report_classes = [
        report
        for report_group in [report_groups.get(x) for x in config.report_groups]
        for report in report_group or []
    ]

    if config.start_date is None:
        raise ValueError("Start date is required")

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
