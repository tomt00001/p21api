from typing import Any, Dict, Optional

import petl as etl

from .report_base import ReportBase


def _safe_float_sum(values: Any) -> float:
    """Sum values that coerce to float, silently ignoring ones that don't."""
    total = 0.0
    for value in values:
        if value is None:
            continue
        try:
            total += float(value)
        except (TypeError, ValueError):
            continue
    return total


def _first_non_null(values: Any) -> Any:
    """Return the first non-null value encountered, or None."""
    for value in values:
        if value is not None:
            return value
    return None


def _first_non_null_float(values: Any) -> Optional[float]:
    """Return the first value that coerces to float, or None."""
    for value in values:
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _max_or_none(values: Any) -> Any:
    """Return the max of the truthy values, or None if there are none."""
    truthy_values = [value for value in values if value]
    return max(truthy_values) if truthy_values else None


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
        inv_loc_data, _ = self._client.query(
            endpoint="p21_view_inv_loc",
            selects=[
                "item_id",
                "qty_on_hand",
                "standard_cost",
                "primary_supplier_id",
            ],
            page_size=1000,
        )
        inventory = self._aggregate_inventory(inv_loc_data or [])

        sales_lines, _ = self._client.query(
            endpoint="p21_sales_history_view",
            selects=["item_id", "invoice_date"],
            page_size=1000,
        )
        last_sales_date = self._max_date_per_item(sales_lines or [], "invoice_date")

        receipts, _ = self._client.query(
            endpoint="p21_view_inventory_receipts_line",
            selects=["item_id", "date_created"],
            page_size=1000,
        )
        last_received_date = self._max_date_per_item(receipts or [], "date_created")

        supplier_name_map = self._fetch_supplier_names(inventory)

        cutoff_str = self._start_date.strftime("%Y-%m-%d")
        dead_inventory_rows = []
        for item_id, info in inventory.items():
            qoh = info["qty_on_hand"]
            if qoh <= 0:
                continue  # Skip items with no inventory on hand

            # If item has no sales, or last sales date < cutoff, include
            last_date = last_sales_date.get(item_id)
            if last_date and last_date >= cutoff_str:
                continue

            unit_cost = info["standard_cost"]
            value_on_hand = unit_cost * qoh if unit_cost is not None else None
            supplier_id = info["primary_supplier_id"]
            supplier_name = (
                supplier_name_map.get(supplier_id, "")
                if supplier_id is not None
                else ""
            )

            dead_inventory_rows.append(
                {
                    "Item ID": item_id,
                    "Quantity on hand (QOH)": qoh,
                    "Last sales date": last_date or "",
                    "Last received date": last_received_date.get(item_id, ""),
                    "Unit cost": unit_cost,
                    "Value on hand": value_on_hand,
                    "Supplier Name": supplier_name,
                }
            )

        if not dead_inventory_rows:
            return

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

    def _aggregate_inventory(
        self, inv_loc_data: list[dict[str, Any]]
    ) -> Dict[Any, Dict[str, Any]]:
        """Sum qty_on_hand and take the first non-null cost/supplier per item,
        across possibly multiple location rows per item."""
        rows_with_item_id = [row for row in inv_loc_data if row.get("item_id")]
        if not rows_with_item_id:
            return {}
        table = etl.fromdicts(rows_with_item_id)
        aggregated = etl.aggregate(
            table,
            "item_id",
            {
                "qty_on_hand": ("qty_on_hand", _safe_float_sum),
                "standard_cost": ("standard_cost", _first_non_null_float),
                "primary_supplier_id": ("primary_supplier_id", _first_non_null),
            },
        )
        return {row["item_id"]: row for row in etl.dicts(aggregated)}

    def _max_date_per_item(
        self, rows: list[dict[str, Any]], date_field: str
    ) -> Dict[Any, Any]:
        """Return the max value of date_field per item_id, for rows where both
        item_id and date_field are present."""
        filtered = [row for row in rows if row.get("item_id") and row.get(date_field)]
        if not filtered:
            return {}
        table = etl.fromdicts(filtered)
        aggregated = etl.aggregate(
            table, "item_id", {"max_date": (date_field, _max_or_none)}
        )
        return {
            row["item_id"]: row["max_date"]
            for row in etl.dicts(aggregated)
            if row["max_date"]
        }

    def _fetch_supplier_names(
        self, inventory: Dict[Any, Dict[str, Any]]
    ) -> Dict[Any, str]:
        """Fetch supplier names for all supplier IDs referenced in inventory."""
        unique_supplier_ids = {
            info["primary_supplier_id"]
            for info in inventory.values()
            if info["primary_supplier_id"] is not None
        }
        if not unique_supplier_ids:
            return {}

        supplier_filter = ReportBase.build_or_filter(
            "supplier_id", unique_supplier_ids, quote_strings=False
        )
        supplier_rows, _ = self._client.query(
            endpoint="p21_view_supplier",
            selects=["supplier_id", "supplier_name"],
            filters=[f"({supplier_filter})"] if supplier_filter else [],
            page_size=500,
        )
        return {
            row["supplier_id"]: row["supplier_name"]
            for row in (supplier_rows or [])
            if row.get("supplier_id") is not None
            and row.get("supplier_name") is not None
        }
