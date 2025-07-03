import petl as etl

from .report_base import ReportBase


class ReportJarp(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "jarp_"

    def _run(self) -> None:
        # Use improved pagination-aware query method with explicit parameters
        invoice_data, _ = self._client.query_odataservice(
            endpoint="p21_view_invoice_hdr",
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
                "ship_to_id",
                "salesrep_id",
            ],
            start_date=self._start_date,
            filters=[
                "(ship_to_id eq 12755 or ship_to_id eq 15097)",
            ],
            order_by=["invoice_date asc"],
            page_size=500,  # Smaller page size for complex joins
        )
        if not invoice_data:
            return
        invoice_pre = etl.fromdicts(invoice_data)
        invoice = etl.select(
            invoice_pre,
            lambda rec: not (rec.get("po_no") or "").startswith("P"),
        )
        if self._debug:
            etl.tocsv(invoice, self.file_name("invoice"))

        invoice_ids_filter = " or ".join(
            [
                f"invoice_no eq '{invoice_id}'"
                for invoice_id in {row["invoice_no"] for row in invoice_data}
            ]
        )
        invoice_line_data, _ = self._client.query_odataservice(
            endpoint="p21_view_invoice_line",
            selects=[
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
            filters=[f"({invoice_ids_filter})"],
            page_size=500,  # Smaller page size for detailed line data
        )
        if not invoice_line_data:
            return
        invoice_line = etl.fromdicts(invoice_line_data)
        if self._debug:
            etl.tocsv(invoice_line, self.file_name("invoice_line"))

        sales_history_data, _ = self._client.query_odataservice(
            endpoint="p21_sales_history_view",
            selects=[
                "item_id",
                "item_desc",
                "unit_price",
                "customer_id",
                "inv_mast_uid",
                "supplier_id",
                "invoice_no",
                "line_no",
                "ship_to_id",
            ],
            filters=[f"({invoice_ids_filter})"],
            page_size=500,  # Smaller page size for history data
        )
        if not sales_history_data:
            return
        sales_history = etl.fromdicts(sales_history_data)
        if self._debug:
            etl.tocsv(sales_history, self.file_name("sales_history"))

        supplier_id_filter = " or ".join(
            [
                f"supplier_id eq {supplier_id}"
                for supplier_id in {row["supplier_id"] for row in sales_history_data}
                if supplier_id is not None
            ]
        )
        supplier_data, _ = self._client.query_odataservice(
            endpoint="p21_view_inventory_supplier",
            selects=["inv_mast_uid", "supplier_id", "item_id"],
            filters=[f"({supplier_id_filter})"],
            page_size=500,  # Smaller page size for supplier data
        )
        supplier = etl.fromdicts(supplier_data)
        if self._debug:
            etl.tocsv(supplier, self.file_name("supplier"))

        # Step 1: Join sales_history with supplier on inv_mast_uid,
        # supplier_id, and item_id
        sales_supplier_joined = etl.join(
            sales_history,
            supplier,
            lkey=("inv_mast_uid", "supplier_id", "item_id"),
            rkey=("inv_mast_uid", "supplier_id", "item_id"),
        )

        # Step 2: Join the result with invoice_hdr on invoice_no
        invoice_sales_joined = etl.join(
            invoice,
            sales_supplier_joined,
            lkey="invoice_no",  # Key in invoice_hdr
            rkey="invoice_no",
        )  # Key in sales_supplier_joined

        # Step 3: Join the result with invoice_line on invoice_no
        final_join = etl.join(
            invoice_sales_joined,
            invoice_line,
            lkey=("invoice_no", "line_no"),
            rkey=("invoice_no", "line_no"),
        )

        # Step 4: Select the desired columns
        selected_columns = etl.cut(
            final_join,
            "bill2_name",
            "ship2_address1",
            "invoice_date",
            "invoice_no",
            "item_id",
            "item_desc",
            "qty_requested",
            "qty_shipped",
            "unit_price",
            "extended_price",
            "customer_part_number",
            "po_no",
        )

        sorted_table = etl.sort(selected_columns, "invoice_date")

        # Step 6: Output the result to a CSV file
        etl.tocsv(sorted_table, self.file_name("report"))
