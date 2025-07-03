import petl as etl

from .report_base import ReportBase


class ReportDailySales(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "daily_sales_"

    def _run(self) -> None:
        # Use improved pagination-aware query method
        invoice_data, _ = self._client.query_odataservice(
            endpoint="p21_view_invoice_hdr",
            selects=[
                "bill2_name",
                "freight",
                "invoice_date",
                "invoice_no",
                "other_charge_amount",
                "period",
                "tax_amount",
                "total_amount",
                "year_for_period",
                "salesrep_id",
            ],
            start_date=self._start_date,
            order_by=["year_for_period asc", "invoice_no asc"],
            page_size=1000,  # Explicit page size for large datasets
        )
        if not invoice_data:
            return
        invoice = etl.fromdicts(invoice_data)
        etl.tocsv(
            invoice,
            self.file_name("report"),
        )
