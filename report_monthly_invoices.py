from datetime import timedelta

import petl as etl

from report_base import Report_Base


class ReportMonthlyInvoices(Report_Base):
    @property
    def file_name_prefix(self) -> str:
        return "monthly_invoices_"

    def run(self) -> None:
        end_date = self._start_date + timedelta(days=90)
        p21_view_invoice_hdr_data = self._client.query(
            "p21_view_invoice_hdr",
            start_date=self._start_date,
            end_date=end_date,
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
            ],
            order_by=["year_for_period asc", "invoice_no asc"],
        )
        p21_view_invoice_hdr = etl.fromdicts(p21_view_invoice_hdr_data)
        etl.tocsv(
            p21_view_invoice_hdr,
            self.file_name("p21_view_invoice_hdr"),
        )
