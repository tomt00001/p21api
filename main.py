import os
from datetime import datetime

from dotenv import load_dotenv

from p21_odata_client import P21ODataClient
from report_daily_sales import ReportDailySales
from report_open_orders import ReportOpenOrders

if __name__ == "__main__":
    load_dotenv()

    base_url = os.getenv("BASE_URL")
    username = os.getenv("APIUSERNAME")
    password = os.getenv("APIPASSWORD")
    date_input = os.getenv("DATE_INPUT")
    if isinstance(date_input, str):
        date_input = datetime.strptime(date_input, "%Y-%m-%d")

    if base_url is None or username is None or password is None:
        raise ValueError("Missing environment variables")

    if date_input is None:
        raise ValueError("Missing date input")

    client = P21ODataClient(base_url, username, password, debug=True)

    report_classes = [ReportDailySales, ReportOpenOrders]
    for report_class in report_classes:
        report = report_class(client=client, start_date=date_input)
        report.run()
