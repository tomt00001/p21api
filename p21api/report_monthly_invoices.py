from .report_invoice_base import InvoiceHeaderReportBase


class ReportMonthlyInvoices(InvoiceHeaderReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "monthly_invoices_"
