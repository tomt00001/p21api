import petl as etl

from report_base import Report_Base


class ReportJarp(Report_Base):
    @property
    def file_name_prefix(self) -> str:
        return "jarp_"

    def run(self) -> None:
        invoice_data, url = self._client.query_odataservice(
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
                "ship_to_id",
            ],
            filters=[
                "(ship_to_id eq 12755 or ship_to_id eq 15097)",
                # "not startswith(po_no, 'P')",
            ],
            order_by=["invoice_date asc"],
        )
        invoice_pre = etl.fromdicts(invoice_data)
        invoice = etl.select(
            invoice_pre,
            lambda rec: not rec["po_no"].startswith("P"),
        )
        if self._debug:
            etl.tocsv(invoice, self.file_name("invoice"))

        invoice_ids_filter = " or ".join(
            [
                f"invoice_no eq '{invoice_id}'"
                for invoice_id in {row["invoice_no"] for row in invoice_data}
            ]
        )
        invoice_line_data, url = self._client.query_odataservice(
            "p21_view_invoice_line",
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
        )
        invoice_line = etl.fromdicts(invoice_line_data)
        if self._debug:
            etl.tocsv(invoice_line, self.file_name("invoice_line"))

        sales_history_data, url = self._client.query_odataservice(
            "p21_sales_history_view",
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
        )
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
        supplier_data, url = self._client.query_odataservice(
            "p21_view_inventory_supplier",
            selects=["inv_mast_uid", "supplier_id", "item_id"],
            filters=[f"({supplier_id_filter})"],
        )
        supplier = etl.fromdicts(supplier_data)
        if self._debug:
            etl.tocsv(supplier, self.file_name("supplier"))

        # Step 1: Join sales_history with supplier on inv_mast_uid, supplier_id, and item_id
        sales_supplier_joined = etl.join(
            sales_history,
            supplier,
            lkey=("inv_mast_uid", "supplier_id", "item_id"),  # Keys in sales_history
            rkey=("inv_mast_uid", "supplier_id", "item_id"),
        )  # Keys in supplier

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
            lkey="invoice_no",  # Key in invoice_sales_joined
            rkey="invoice_no",
        )  # Key in invoice_line

        # Step 4: Filter based on line_no
        final_join = etl.select(
            final_join, "{line_no} == {line_no}"
        )  # Adjust according to your needs

        # Step 5: Select the desired columns
        selected_columns = etl.cut(
            final_join,
            "bill2_name",
            "invoice_date",
            "invoice_no",
            "po_no",
            "ship2_address1",
            "customer_part_number",
            "extended_price",
            "qty_requested",
            "qty_shipped",
            "item_desc",
            "item_id",
            "unit_price",
        )

        # Step 6: Output the result to a CSV file
        etl.tocsv(selected_columns, self.file_name("report"))
