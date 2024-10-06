from typing import Type

from .config import Config
from .odata_client import ODataClient
from .report_base import ReportBase
from .report_daily_sales import ReportDailySales
from .report_jarp import ReportJarp
from .report_kennametal_pos import ReportKennametalPos
from .report_monthly_consolidation import ReportMonthlyConsolidation
from .report_monthly_invoices import ReportMonthlyInvoices
from .report_open_orders import ReportOpenOrders


def do_reports(client: "ODataClient", config: Config) -> None:
    report_classes: list[Type[ReportBase]] = [
        ReportKennametalPos,
        ReportDailySales,
        ReportOpenOrders,
        ReportMonthlyInvoices,
        ReportMonthlyConsolidation,
        ReportJarp,
    ]
    for report_class in report_classes:
        report = report_class(client=client, config=config)
        report.run()
