from .report_invoice_base import InvoiceHeaderReportBase


class ReportDailySales(InvoiceHeaderReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "daily_sales_"
