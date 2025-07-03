import petl as etl

from .report_base import ReportBase


class ReportGrindShopOpenOrders(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "grind_shop_open_orders_"

    def _run(self) -> None:
        # Get order header data for grind shop orders (taker = 'RC')
        order_hdr_data, url = self._client.query_odataservice(
            endpoint="p21_view_oe_hdr",
            selects=[
                "customer_id",
                "order_no",
                "order_date",
                "requested_date",
                "promise_date",
                "taker",
                "delete_flag",
                "completed",
                "company_id",
            ],
            filters=[
                "company_id eq 'CMS'",  # CMS Orders Only
                "delete_flag eq 'N'",  # Not Deleted
                "completed ne 'Y'",  # Order is not marked complete
                "taker eq 'RC'",  # Grind Shop
            ],
            order_by=["customer_id asc", "order_no asc"],
        )
        if not order_hdr_data:
            return

        order_hdr = etl.fromdicts(order_hdr_data)
        if self._debug:
            etl.tocsv(order_hdr, self.file_name("order_hdr"))

        # Get order line data for the orders
        order_no_filters = " or ".join(
            [
                f"order_no eq '{order_no}'"
                for order_no in {row["order_no"] for row in order_hdr_data}
            ]
        )

        order_line_data, url = self._client.query_odataservice(
            endpoint="p21_view_oe_line",
            selects=[
                "order_no",
                "inv_mast_uid",
                "qty_ordered",
                "qty_allocated",
                "qty_on_pick_tickets",
                "qty_invoiced",
                "qty_canceled",
                "disposition",
                "delete_flag",
                "complete",
            ],
            filters=[
                f"({order_no_filters})",
                "delete_flag eq 'N'",  # Not Deleted
                "complete ne 'Y'",  # Line is not marked complete
            ],
        )
        if not order_line_data:
            return

        order_line = etl.fromdicts(order_line_data)
        if self._debug:
            etl.tocsv(order_line, self.file_name("order_line"))

        # Get inventory master data for item details
        inv_mast_uid_filters = " or ".join(
            [
                f"inv_mast_uid eq {inv_mast_uid}"
                for inv_mast_uid in {row["inv_mast_uid"] for row in order_line_data}
                if inv_mast_uid is not None
            ]
        )

        if not inv_mast_uid_filters:
            return

        inv_mast_data, _ = self._client.query_odataservice(
            endpoint="p21_view_inv_mast",
            selects=[
                "inv_mast_uid",
                "item_id",
                "item_desc",
            ],
            filters=[f"({inv_mast_uid_filters})"],
        )
        if not inv_mast_data:
            return

        inv_mast = etl.fromdicts(inv_mast_data)
        if self._debug:
            etl.tocsv(inv_mast, self.file_name("inv_mast"))

        # Get customer data
        customer_id_filters = " or ".join(
            [
                f"customer_id eq {customer_id}"
                for customer_id in {row["customer_id"] for row in order_hdr_data}
                if customer_id is not None
            ]
        )

        customer_data, _ = self._client.query_odataservice(
            endpoint="p21_view_customer",
            selects=[
                "customer_id",
                "customer_name",
            ],
            filters=[f"({customer_id_filters})"],
        )
        if not customer_data:
            return

        customer = etl.fromdicts(customer_data)
        if self._debug:
            etl.tocsv(customer, self.file_name("customer"))

        # Join order header with customer
        order_customer_joined = etl.join(
            order_hdr,
            customer,
            lkey="customer_id",
            rkey="customer_id",
        )

        # Join with order lines
        order_line_joined = etl.join(
            order_customer_joined,
            order_line,
            lkey="order_no",
            rkey="order_no",
        )

        # Join with inventory master for item details
        final_joined = etl.join(
            order_line_joined,
            inv_mast,
            lkey="inv_mast_uid",
            rkey="inv_mast_uid",
        )

        # Select the desired columns matching the SQL query output
        selected_columns = etl.cut(
            final_joined,
            "customer_id",
            "customer_name",
            "order_no",
            "order_date",
            "requested_date",
            "promise_date",
            "item_id",
            "item_desc",
            "qty_ordered",
            "qty_allocated",
            "qty_on_pick_tickets",
            "qty_invoiced",
            "qty_canceled",
            "disposition",
        )

        # Sort the data
        sorted_table = etl.sort(
            selected_columns, key=["customer_id", "order_no", "item_id"]
        )

        # Filter items that start with KDB or PRE (assumptions from SQL comments)
        filtered_table = etl.select(
            sorted_table, lambda rec: rec.get("item_id", "").startswith(("KDB", "PRE"))
        )

        # Output the result to a CSV file
        etl.tocsv(filtered_table, self.file_name("report"))
