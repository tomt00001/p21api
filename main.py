from datetime import datetime

from p21_odata_client import P21ODataClient
from report_daily_sales import ReportDailySales
from report_jarp import ReportJarp
from report_kennametal_pos import ReportKennametalPos
from report_monthly_consolidation import ReportMonthlyConsolidation
from report_monthly_invoices import ReportMonthlyInvoices
from report_open_orders import ReportOpenOrders

if __name__ == "__main__":
    base_url = "https://christensenmachinery-play.epicordistribution.com"
    username = "bmulhern"
    password = "P21@nrehlum567232"

    client = P21ODataClient(base_url, username, password)

    date_input = datetime(2019, 5, 1)

    report_classes = [
        ReportDailySales,
        ReportJarp,
        ReportKennametalPos,
        ReportMonthlyConsolidation,
        ReportMonthlyInvoices,
        ReportOpenOrders,
    ]
    for report_class in report_classes:
        report = report_class(client=client, start_date=date_input)
        report.run()
