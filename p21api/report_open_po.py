from datetime import datetime

import petl as etl

from .report_base import ReportBase


class ReportOpenPO(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "open_po_"

    def _run(self):
        start_date = datetime.now()
        start_date_str = self._client._datetime_to_str(start_date)
        po_filters = ["complete eq 'N'"]

        po_data, url = self._client.query_odataservice(
            "p21_view_po_hdr",
            selects=[
                "supplier_id",
                "po_no",
                "order_date",
                "expected_date",
            ],
            filters=[f"order_date lt {start_date_str}"] + po_filters,
            order_by=["supplier_id asc", "order_date asc"],
        )
        po = etl.fromdicts(po_data)

        po_nos = [row["po_no"] for row in po_data] if po_data else []
        supplier_ids = [row["supplier_id"] for row in po_data] if po_data else []

        po_line_data, url = self._client.query_odataservice(
            "p21_view_po_line",
            selects=[
                "po_no",
                "line_no",
                "item_id",
                "item_description",
                "qty_ordered",
                "qty_received",
            ],
            filters=[f"date_created lt {start_date_str}"] + po_filters,
            order_by=["po_no asc", "line_no asc"],
        )

        # Filter data for only line items on a matching open PO
        po_line_data = (
            [row for row in po_line_data if row["po_no"] in po_nos]
            if po_line_data
            else []
        )
        po_line = etl.fromdicts(po_line_data)

        supplier_data, url = self._client.query_odataservice(
            "p21_view_supplier",
            selects=[
                "supplier_id",
                "supplier_name",
            ],
            filters=[f"date_created lt {start_date_str}"],
            order_by=["supplier_id asc"],
        )

        # Filter data for only suppliers on a matching open PO
        supplier_data = (
            [row for row in supplier_data if row["supplier_id"] in supplier_ids]  # noqa: E501
            if supplier_data
            else []
        )
        supplier = etl.fromdicts(supplier_data)

        # 4. Join Tables: supplier -> po_hdr -> po_line
        joined_table = (
            po.join(supplier, key="supplier_id")
            .join(po_line, key="po_no")
            .addfield(
                "qty_remaining",
                lambda row: row["qty_ordered"] - row["qty_received"],
            )
        ).cut(
            "supplier_id",
            "supplier_name",
            "po_no",
            "order_date",
            "expected_date",
            "item_id",
            "item_description",
            "qty_ordered",
            "qty_received",
            "qty_remaining",
        )

        # 6. Export to CSV
        etl.tocsv(joined_table, self.file_name("report"))
