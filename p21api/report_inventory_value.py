from datetime import timedelta

import petl as etl

from .report_base import ReportBase


class ReportInventoryValue(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "inventory_value_"

    def _run(self) -> None:
        year_ago_date = self._start_date - timedelta(days=365)

        # Sales
        sales_filters = self._client.get_datetime_filter(
            "invoice_date",
            year_ago_date,
            self._start_date,
        )
        sales_data, _ = self._client.query_odataservice(
            "p21_sales_history_view",
            selects=["item_id", "invoice_date"],
            filters=sales_filters,
            order_by=["item_id asc", "invoice_date desc"],
            # use_pagination removed; rely on page_size
            page_size=1000,
        )
        sales = etl.fromdicts(sales_data)

        # Deduplicate the rows based on 'item_id'
        # (keeps the first occurrence of each item_id)
        deduplicated_sales = etl.distinct(sales, key="item_id")
        reordered_sales = etl.cut(deduplicated_sales, "item_id", "invoice_date")

        # Output the deduplicated sales data to CSV
        etl.tocsv(reordered_sales, self.file_name("sales"))

        # POs
        po_line_filters = self._client.get_datetime_filter(
            "date_created",
            year_ago_date,
            self._start_date,
        )
        po_line_data, _ = self._client.query_odataservice(
            "p21_view_po_line",
            selects=[
                "item_id",
                "date_created",
                "received_date",
            ],
            filters=po_line_filters,
            order_by=["item_id asc", "date_created desc"],
            # use_pagination removed; rely on page_size
            page_size=1000,
        )
        po_line = etl.fromdicts(po_line_data)

        # Deduplicate the rows based on 'item_id'
        # (keeps the first occurrence of each item_id)
        deduplicated_po_line = etl.distinct(po_line, key="item_id")
        reordered_po_line = etl.cut(
            deduplicated_po_line, "item_id", "date_created", "received_date"
        )

        # Output the deduplicated PO line data to CSV
        etl.tocsv(reordered_po_line, self.file_name("po_line"))

        # Inventory Value
        inventory_value_filters = ["fifo_layer_qty gt 0"]
        inventory_value_data, _ = self._client.query_odataservice(
            "p21_view_inventory_value_report",
            selects=[
                "item_id",
                "cost",
                "qty_on_hand",
                "fifo_layer_qty",
                "fifo_layer_value",
            ],
            filters=inventory_value_filters,
            # use_pagination removed; rely on page_size
            page_size=1000,
        )
        inventory_value = etl.fromdicts(inventory_value_data)
        reordered_inventory_value = etl.cut(
            inventory_value,
            "item_id",
            "cost",
            "qty_on_hand",
            "fifo_layer_qty",
            "fifo_layer_value",
        )

        etl.tocsv(reordered_inventory_value, self.file_name("inventory_value"))

        # Join inventory_value with sales
        merged_data = etl.outerjoin(inventory_value, deduplicated_sales, key="item_id")

        # Join with po_line
        merged_data = etl.outerjoin(merged_data, deduplicated_po_line, key="item_id")

        # Reorder columns
        merged_data = etl.cut(
            merged_data,
            "item_id",
            "invoice_date",
            "date_created",
            "received_date",
            "cost",
            "qty_on_hand",
            "fifo_layer_qty",
            "fifo_layer_value",
        )

        # Output to CSV
        etl.tocsv(merged_data, self.file_name("merged_output"))
