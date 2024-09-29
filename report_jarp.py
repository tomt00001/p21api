import petl as etl

from report_base import Report_Base


class ReportJarp(Report_Base):
    @property
    def file_name_prefix(self) -> str:
        return "jarp_"

    def run(self) -> None:
        invoice_data = self._client.query(
            "p21_view_invoice_hdr",
            start_date=self._start_date,
            selects=[
                "bill2_name",
                "freight",
                "invoice_date",
                "invoice_no",
                "other_charge_amount",
                "period",
                "po_no",
                "ship2_address1",
                "tax_amount",
                "total_amount",
                "year_for_period",
            ],
            filters=[
                "(ship_to_id eq 12755 or ship_to_id eq 15097)",
                "not substringof('P', po_no)",
            ],
            order_by=["invoice_date asc"],
        )
        invoice = etl.fromdicts(invoice_data)
        etl.tocsv(
            invoice,
            self.file_name("p21_view_invoice_hdr"),
        )

        invoice_line_data = self._client.query(
            "p21_view_invoice_line",
            start_date=self._start_date,
            select=[
                "item_id",
                "item_desc",
                "qty_requested",
                "qty_shipped",
                "unit_price",
                "extended_price",
                "customer_part_number",
                "invoice_no",
                "line_no",
            ],
        )
        invoice_line = etl.fromdicts(invoice_line_data)
        etl.tocsv(
            invoice_line,
            self.file_name("p21_view_invoice_line"),
        )

        supplier_data = self._client.query(
            "p21_view_inventory_supplier",
            start_date=self._start_date,
            select=["inv_mast_uid", "supplier_id"],
        )
        supplier = etl.fromdicts(supplier_data)
        etl.tocsv(supplier, self.file_name("p21_view_inventory_supplier"))

        # p21_sales_history_view
        # item_id
        # item_desc
        # unit_price
        # customer_id
        # inv_mast_uid
        # supplier_id
        # invoice_no
        # line_no
        # ship_to_id

        join1 = etl.join(
            invoice,
            invoice_line,
            "invoice_no",
        )
        join2 = etl.join(join1, supplier, "item_id")
        etl.tocsv(join2, self.file_name("combined"))
