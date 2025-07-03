# Standard library imports
from datetime import datetime

# Third-party imports
import petl as etl

# Local imports
from .report_base import ReportBase


class ReportOpenPO(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "open_po_"

    def _run(self) -> None:
        start_date = datetime.now()
        start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        po_filters = ["complete eq 'N'"]

        po_data, _ = self._client.query_odataservice(
            "p21_view_po_hdr",
            selects=[
                "supplier_id",
                "po_no",
                "order_date",
                "expected_date",
            ],
            filters=[f"order_date lt {start_date_str}"] + po_filters,
            order_by=["supplier_id asc", "order_date asc"],
            use_pagination=True,
            page_size=1000,
        )
        po = etl.fromdicts(po_data)

        po_nos: list[str] = [row["po_no"] for row in po_data] if po_data else []
        supplier_ids: list[str] = (
            [row["supplier_id"] for row in po_data] if po_data else []
        )

        po_line_data, _ = self._client.query_odataservice(
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
            use_pagination=True,
            page_size=1000,
        )

        po_line_data_filtered: list[dict[str, object]] = (
            [row for row in po_line_data if row["po_no"] in po_nos]
            if po_line_data
            else []
        )
        po_line = etl.fromdicts(po_line_data_filtered)

        supplier_data, _ = self._client.query_odataservice(
            "p21_view_supplier",
            selects=[
                "supplier_id",
                "supplier_name",
            ],
            filters=[f"date_created lt {start_date_str}"],
            order_by=["supplier_id asc"],
            use_pagination=True,
            page_size=1000,
        )

        supplier_data_filtered: list[dict[str, object]] = (
            [row for row in supplier_data if row["supplier_id"] in supplier_ids]  # noqa: E501
            if supplier_data
            else []
        )
        supplier = etl.fromdicts(supplier_data_filtered)

        # 4. Join Tables: supplier -> po_hdr -> po_line
        # First join po with supplier
        po_supplier_joined = etl.join(po, supplier, key="supplier_id")

        # Then join with po_line
        joined_table = etl.join(po_supplier_joined, po_line, key="po_no")

        # Add calculated field
        joined_with_calc = etl.addfield(
            joined_table,
            "qty_remaining",
            lambda row: row["qty_ordered"] - row["qty_received"],
        )

        # Cut to select desired fields
        final_table = etl.cut(
            joined_with_calc,
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
        etl.tocsv(final_table, self.file_name("report"))
