import petl as etl

from report_base import Report_Base


class ReportMonthlyConsolidation(Report_Base):
    @property
    def file_name_prefix(self) -> str:
        return "monthly_consolidation_"

    def run(self) -> None:
        invoice_data, url = self._client.query_odataservice(
            "p21_view_invoice_hdr",
            start_date=self._start_date,
            selects=[
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
            ],
            filters=["consolidated eq 'Y'"],
            order_by=["year_for_period asc", "invoice_no asc"],
        )
        invoice = etl.fromdicts(invoice_data)
        etl.tocsv(
            invoice,
            self.file_name("report"),
        )
