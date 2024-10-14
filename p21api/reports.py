from typing import Type

from .config import Config
from .odata_client import ODataClient
from .report_base import ReportBase
from .report_daily_sales import ReportDailySales
from .report_inventory import ReportInventory
from .report_jarp import ReportJarp
from .report_kennametal_pos import ReportKennametalPos
from .report_monthly_consolidation import ReportMonthlyConsolidation
from .report_monthly_invoices import ReportMonthlyInvoices
from .report_open_orders import ReportOpenOrders


def do_reports(client: "ODataClient", config: Config) -> None:
    report_groups: dict[str, list[Type[ReportBase]]] = {
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
    }
    for report_class in report_groups.get(config.report_group, []):
        report = report_class(client=client, config=config)
        report.run()
