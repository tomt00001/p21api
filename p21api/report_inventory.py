import petl as etl

from .report_base import ReportBase


class ReportInventory(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "inventory_"

    def run(self) -> None:
        stockstatus_data, url = self._client.query_odataservice(
            "p21_view_stockstatus_report",
            selects=[
                "item_id",
                "delete_flag",
                "location_id",
                "qty_on_hand",
                "company_id",
                "product_group_id",
                "product_group_desc",
                "purchase_class",
                "order_quantity",
                "qty_allocated",
                "qty_backordered",
                "qty_in_transit",
                "qty_reserved_due_in",
                "requisition",
                "company_name",
                "location_name",
                "supplier_id",
                "supplier_name",
                "primary_supplier",
                "net_stock",
                "vendor_consigned",
                "item_desc",
                "location_delete_flag",
            ],
            filters=[
                "supplier_id eq 11777",
                "location_id eq 101",
                "qty_on_hand gt 0",
            ],
        )
        if not stockstatus_data:
            return
        stockstatus = etl.fromdicts(stockstatus_data)
        etl.tocsv(
            stockstatus,
            self.file_name("stockstatus"),
        )

        inventoryvalue_data, url = self._client.query_odataservice(
            "p21_view_inventory_value_report",
            selects=[
                "item_id",
                "item_desc",
                "track_lots",
                "use_lot_cost",
                "vendor_consigned",
                "company_id",
                "company_name",
                "location_id",
                "location_name",
                "default_branch_id",
                "branch_description",
                "product_group_id",
                "product_group_desc",
                "primary_supplier_id",
                "supplier_name",
                "requisition",
                "purchase_class",
                "qty_on_hand",
                "special_layer_qty",
                "special_layer_value",
                "fifo_layer_qty",
                "fifo_layer_value",
                "lot_qty",
                "lot_value",
                "cost",
                "cost_basis",
                "inv_mast_uid",
                "revision_level",
                "current_revision_level",
                "rental_item_flag",
                "special_dts_layer_qty",
                "special_dts_layer_value",
            ],
            filters=[
                "primary_supplier_id eq 11777",
                "location_id eq 101",
            ],
        )
        if not inventoryvalue_data:
            return
        inventoryvalue = etl.fromdicts(inventoryvalue_data)
        etl.tocsv(
            inventoryvalue,
            self.file_name("inventory_value"),
        )

        inactive_items_data, url = self._client.query_odataservice(
            "p21_view_inactive_items_report",
            selects=[
                "item_id",
                "item_desc",
                "delete_flag",
                "track_lots",
                "location_id",
                "company_id",
                "company_name",
                "product_group_id",
                "product_group_desc",
                "purchase_discount_group",
                "sales_discount_group",
                "primary_supplier_id",
                "supplier_name",
                "qty_on_hand",
                "qty_allocated",
                "qty_available",
                "qty_backordered",
                "qty_on_PO",
                "qty_in_transit",
                "qty_in_process",
                "standard_cost",
                "moving_average_cost",
                "next_due_in_po_cost",
                "last_purchase_date",
                "last_order_date",
                "use_lot_cost",
                "inventory_cost",
                "stockable",
                "qty_reserved_due_in",
                "sales_pricing_unit_size",
                "period_usage",
                "StockTracker",
            ],
            filters=[
                "primary_supplier_id eq 11777",
                "location_id eq 101",
            ],
        )
        if not inactive_items_data:
            return
        inactive_items = etl.fromdicts(inactive_items_data)
        etl.tocsv(
            inactive_items,
            self.file_name("inactive_items"),
        )
