from typing import TYPE_CHECKING, Type

from .odata_client import ODataClient
from .report_base import ReportBase
from .report_daily_sales import ReportDailySales
from .report_inventory import ReportInventory
from .report_jarp import ReportJarp
from .report_kennametal_pos import ReportKennametalPos
from .report_monthly_consolidation import ReportMonthlyConsolidation
from .report_monthly_invoices import ReportMonthlyInvoices
from .report_open_orders import ReportOpenOrders
from .report_open_po import ReportOpenPO

if TYPE_CHECKING:
    from .config import Config

REPORT_GROUPS: dict[str, list[Type[ReportBase]]] = {
    "monthly": [
        ReportKennametalPos,
        ReportDailySales,
        ReportOpenOrders,
        ReportMonthlyInvoices,
        ReportMonthlyConsolidation,
        ReportJarp,
    ],
    "inventory": [
        ReportInventory,
    ],
    "po": [
        ReportOpenPO,
    ],
}


def do_reports(
    client: "ODataClient",
    config: "Config",
) -> None:
    # Get the classes of each report in each report group
    report_classes = [
        report
        for report_group in [REPORT_GROUPS.get(x) for x in config.report_groups]
        for report in report_group or []
    ]

    # Run each report from the list of classes
    for report_class in report_classes:
        report = report_class(client=client, config=config)
        report.run()


def get_reports_list() -> list[str]:
    return list(REPORT_GROUPS.keys())
