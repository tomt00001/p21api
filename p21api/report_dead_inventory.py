from collections import defaultdict
from typing import Any, Dict, List, Set

import petl as etl

from .report_base import ReportBase


class ReportDeadInventory(ReportBase):
    """
    Report for inventory items (from inv_mast) that have not moved (no sales)
    since a cutoff date. Joins invoice_hdr, invoice_line, and inv_mast to find unsold
    inventory.
    """

    @property
    def file_name_prefix(self) -> str:
        return "dead_inventory_"

    def _run(self) -> None:
        # Fetch qty_on_hand and standard_cost from p21_view_inv_loc, aggregate by item
        try:
            inv_loc_data, _ = self._client.query_odataservice(
                endpoint="p21_view_inv_loc",
                selects=["item_id", "qty_on_hand", "standard_cost"],
                page_size=1000,
            )
        except StopIteration:
            inv_loc_data = None
        qty_on_hand_map: Dict[str, float] = defaultdict(float)
        cost_map: Dict[str, float] = {}
        if inv_loc_data:
            for row in inv_loc_data:
                item_id = row.get("item_id")
                qty = row.get("qty_on_hand")
                cost = row.get("standard_cost")
                if item_id:
                    if qty is not None:
                        try:
                            qty_on_hand_map[item_id] += float(qty)
                        except (TypeError, ValueError):
                            pass
                    # Use the first non-null cost encountered for the item
                    if item_id not in cost_map and cost is not None:
                        try:
                            cost_map[item_id] = float(cost)
                        except (TypeError, ValueError):
                            pass

        # Fetch all invoice lines (all time) to determine last sales date
        invoice_lines_raw, _ = self._client.query_odataservice(
            endpoint="p21_view_invoice_line",
            selects=["item_id", "invoice_no"],
            page_size=1000,
        )
        invoice_lines: List[Dict[str, Any]] = (
            invoice_lines_raw if invoice_lines_raw else []
        )
        invoice_nos: Set[Any] = {
            row["invoice_no"] for row in invoice_lines if row.get("invoice_no")
        }

        # Fetch invoice headers to get invoice_date for each invoice_no
        if invoice_nos:
            try:
                invoice_hdrs_raw, _ = self._client.query_odataservice(
                    endpoint="p21_view_invoice_hdr",
                    selects=["invoice_no", "invoice_date"],
                    page_size=1000,
                    filter=(
                        f"invoice_no in ({','.join([str(no) for no in invoice_nos])})"
                    ),
                )
            except StopIteration:
                invoice_hdrs_raw = None
            invoice_hdrs: List[Dict[str, Any]] = (
                invoice_hdrs_raw if invoice_hdrs_raw else []
            )
            invoice_date_map_inner = {
                row["invoice_no"]: row["invoice_date"]
                for row in invoice_hdrs
                if row.get("invoice_no") and row.get("invoice_date")
            }
        else:
            invoice_date_map_inner = {}
        invoice_date_map: Dict[Any, Any] = invoice_date_map_inner

        # Build last sales date per item
        item_sales_dates: defaultdict[str, List[Any]] = defaultdict(list)
        for row in invoice_lines:
            item_id = row.get("item_id")
            invoice_no = row.get("invoice_no")
            invoice_date = invoice_date_map.get(invoice_no)
            if item_id and invoice_date:
                item_sales_dates[item_id].append(invoice_date)
        last_sales_date: Dict[str, Any] = {
            item_id: max(dates) for item_id, dates in item_sales_dates.items() if dates
        }

        # Filter inventory for items not sold since cutoff (no sales after cutoff)
        dead_inventory_rows: List[Dict[str, Any]] = []
        cutoff_str = self._start_date.strftime("%Y-%m-%d")
        for item_id in qty_on_hand_map.keys():
            qoh = qty_on_hand_map.get(item_id, 0)
            if qoh <= 0:
                continue  # Skip items with no inventory on hand
            # If item has no sales, or last sales date < cutoff, include
            last_date = last_sales_date.get(item_id)
            unit_cost = cost_map.get(item_id, None)
            value_on_hand = None
            try:
                if unit_cost is not None:
                    value_on_hand = float(unit_cost) * float(qoh)
            except Exception:
                value_on_hand = None
            if not last_date or last_date < cutoff_str:
                dead_inventory_rows.append(
                    {
                        "Item ID": item_id,
                        "Quantity on hand (QOH)": qoh,
                        "Last sales date": last_date or "",
                        "Unit cost": unit_cost,
                        "Value on hand": value_on_hand,
                    }
                )

        if dead_inventory_rows:
            # Sort by Value on hand descending
            sorted_rows = sorted(
                dead_inventory_rows,
                key=lambda row: (
                    row["Value on hand"]
                    if row["Value on hand"] is not None
                    else -float("inf")
                ),
                reverse=True,
            )
            etl.tocsv(etl.fromdicts(sorted_rows), self.file_name("report"))
