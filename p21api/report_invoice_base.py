from typing import Any

import petl as etl

from .report_base import ReportBase


class InvoiceHeaderReportBase(ReportBase):
    """Shared implementation for reports that export p21_view_invoice_hdr rows.

    Subclasses only need to set file_name_prefix, and optionally override
    `selects`/`filters` to add fields or narrow the result set.
    """

    selects: list[str] = [
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
    ]
    filters: list[str] | None = None

    def _run(self) -> None:
        query_kwargs: dict[str, Any] = {}
        if self.filters:
            query_kwargs["filters"] = self.filters

        invoice_data, _ = self._client.query(
            endpoint="p21_view_invoice_hdr",
            selects=self.selects,
            start_date=self._start_date,
            order_by=["year_for_period asc", "invoice_no asc"],
            page_size=1000,
            **query_kwargs,
        )
        if not invoice_data:
            return
        invoice = etl.fromdicts(invoice_data)
        etl.tocsv(
            invoice,
            self.file_name("report"),
        )
