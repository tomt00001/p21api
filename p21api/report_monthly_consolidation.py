from .report_invoice_base import InvoiceHeaderReportBase


class ReportMonthlyConsolidation(InvoiceHeaderReportBase):
    selects = [
        "bill2_name",
        "consolidated",
        "freight",
        "invoice_date",
        "invoice_no",
        "other_charge_amount",
        "period",
        "tax_amount",
        "total_amount",
        "year_for_period",
        "salesrep_id",
    ]
    filters = ["consolidated eq 'Y'"]

    @property
    def file_name_prefix(self) -> str:
        return "monthly_consolidation_"
