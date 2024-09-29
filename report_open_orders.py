from report_base import Report_Base


class ReportOpenOrders(Report_Base):
    @property
    def file_name_prefix(self) -> str:
        return "open_orders_"

    def run(self) -> None:
        # p21_order_view
        # ship2_name
        # order_date
        # customer_id
        # order_no
        # item_id
        # qty_ordered
        # completed
        # quote_flag
        # qty_allocated
        # qty_invoiced
        # po_no
        # disposition
        # qty_on_pick_tickets
        # qty_canceled
        # line_no
        # item_desc
        # order_no
        # item_id
        # line_no

        # filters = ["completed eq 'N'", "quote_flag eq 'N'"]
        #    AND ( "p21_order_view"."customer_id" = 12087
        #           OR "p21_order_view"."customer_id" = 12139
        #           OR "p21_order_view"."customer_id" = 12149
        #           OR "p21_order_view"."customer_id" = 12344
        #           OR "p21_order_view"."customer_id" = 12620
        #           OR "p21_order_view"."customer_id" = 12976
        #           OR "p21_order_view"."customer_id" = 13191
        #           OR "p21_order_view"."customer_id" = 13321
        #           OR "p21_order_view"."customer_id" = 13627
        #           OR "p21_order_view"."customer_id" = 14048
        #           OR "p21_order_view"."customer_id" = 14211 )
        # order_by = ["customer_id asc", "order_no", "line_no"]

        # TODO need a list of order_nos to filter this one from a previous step
        # created_date does not exist
        # p21_view_ord_ack_line_data = self._client.query(
        #     "p21_view_ord_ack_line",
        #     start_date=self._start_date,
        #     select=["item_desc", "item_id" "line_number", "order_no"],
        # )
        # p21_view_ord_ack_line = etl.fromdicts(p21_view_ord_ack_line_data)
        # etl.tocsv(
        #     p21_view_ord_ack_line,
        #     self.file_name("p21_view_ord_ack_line"),
        # )
        pass
