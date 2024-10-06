import petl as etl

from .report_base import ReportBase


class ReportOpenOrders(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "open_orders_"

    def run(self):
        order_data, url = self._client.query_odataservice(
            "p21_order_view",
            selects=[
                "completed",
                "customer_id",
                "disposition",
                "item_id",
                "line_no",
                "order_date",
                "order_no",
                "po_no",
                "qty_allocated",
                "qty_canceled",
                "qty_invoiced",
                "qty_on_pick_tickets",
                "qty_ordered",
                "quote_flag",
                "ship2_name",
            ],
            filters=[
                "completed eq 'N'",
                "quote_flag eq 'N'",
                "(customer_id eq 12087 or customer_id eq 12139 or "
                "customer_id eq 12149 or customer_id eq 12344 or "
                "customer_id eq 12620 or customer_id eq 12976 or "
                "customer_id eq 13191 or customer_id eq 13321 or "
                "customer_id eq 13627 or customer_id eq 14048 or "
                "customer_id eq 14211)",
            ],
            order_by=["customer_id asc", "order_no asc", "line_no asc"],
        )
        order = etl.fromdicts(order_data)
        if self._debug:
            etl.tocsv(order, self.file_name("order"))
        order_no_filters = " or ".join(
            [
                f"order_no eq '{order_no}'"
                for order_no in {row["order_no"] for row in order_data}
            ]
        )

        order_ack_line_data, url = self._client.query_odataservice(
            "p21_view_ord_ack_line",
            selects=[
                "item_desc",
                "item_id",
                "line_number",
                "order_no",
            ],
            filters=[f"({order_no_filters})"],
        )
        order_ack_line = etl.fromdicts(order_ack_line_data)
        if self._debug:
            etl.tocsv(order_ack_line, self.file_name("order_ack_line"))

        joined = etl.join(
            order,
            order_ack_line,
            lkey=("order_no", "item_id", "line_no"),
            rkey=("order_no", "item_id", "line_number"),
        )
        if self._debug:
            etl.tocsv(joined, self.file_name("joined"))

        selected = etl.cut(
            joined,
            "completed",
            "customer_id",
            "disposition",
            "item_id",
            "line_no",
            "order_date",
            "order_no",
            "po_no",
            "qty_allocated",
            "qty_canceled",
            "qty_invoiced",
            "qty_on_pick_tickets",
            "qty_ordered",
            "quote_flag",
            "ship2_name",
            "item_desc",
        )

        sorted_table = etl.sort(
            selected,
            key=[
                "customer_id",
                "order_no",
                "line_no",
            ],
        )

        etl.tocsv(sorted_table, self.file_name("report"))
