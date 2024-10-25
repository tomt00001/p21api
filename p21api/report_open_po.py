import petl as etl

from .report_base import ReportBase


class ReportOpenPO(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "open_po_"

    def run(self):
        start_date = self._start_date
        end_date = self._client.get_current_month_end_date(start_date)
        _now = self._client._datetime_to_str(start_date)
        po_data, url = self._client.query_odataservice(
            "p21_view_po_hdr",
            selects=[
                "supplier_id",
                "po_no",
                "order_date",
                "expected_date",
            ],
            filters=["complete eq 'N'"]
            + self._client.get_datetime_filter("order_date", start_date, end_date),
            order_by=["supplier_id asc", "order_date asc"],
        )
        if not po_data:
            return
        po = etl.fromdicts(po_data)
        etl.tocsv(po, self.file_name(""))
        po_nos = [row["po_no"] for row in po_data]

        po_line_data, url = self._client.query_odataservice(
            "p21_view_po_line",
            selects=[
                "po_no",
                "line_no",
                "item_id",
                "item_description",
                "qty_ordered",
                "qty_received",
                "date_created",
                "complete",
            ],
            filters=["complete eq 'N'"]
            + self._client.get_datetime_filter("date_created", start_date, end_date),
            order_by=["po_no asc", "line_no asc"],
        )
        if not po_line_data:
            return

        # Filter data for only line items on a matching open PO
        po_line_data = [row for row in po_line_data if row["po_no"] in po_nos]

        po_line = etl.fromdicts(po_line_data)
        etl.tocsv(po_line, self.file_name("line"))
