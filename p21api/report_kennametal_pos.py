import petl as etl

from .report_base import ReportBase


class ReportKennametalPos(ReportBase):
    @property
    def file_name_prefix(self) -> str:
        return "kennametal_pos_"

    def run(self) -> None:
        supplier_filters = ["supplier_id eq 11777"]
        filters = supplier_filters.copy()
        filters.extend(
            self._client.get_datetime_filter(
                "invoice_date",
                self._start_date,
                self._client.get_current_month_end_date(self._start_date),
            )
        )
        sales_data, url = self._client.query_odataservice(
            "p21_sales_history_view",
            selects=[
                "bill2_country",
                "cogs_amount",
                "customer_id",
                "inv_mast_uid",
                "invoice_date",
                "invoice_no",
                "item_desc",
                "period",
                "qty_shipped",
                "ship2_address1",
                "ship2_city",
                "ship2_name",
                "ship2_postal_code",
                "ship2_state",
                "supplier_id",
                "unit_price",
                "year_for_period",
            ],
            filters=filters,
        )
        if not sales_data:
            return
        sales = etl.fromdicts(sales_data)
        if self._debug:
            etl.tocsv(sales, self.file_name("sales"))

        customer_data = self._client.post_odataservice(
            "p21_view_customer",
            selects=[
                "customer_id",
                "customer_id_string",
                "federal_exemption_number",
                "other_exemption_number",
                "state_excise_tax_exemption_no",
            ],
            filters=["customer_id ne 1"],
            orderby=["customer_id asc"],
        )
        customer = etl.fromdicts(customer_data)
        if self._debug:
            etl.tocsv(customer, self.file_name("customer"))

        supplier_data, url = self._client.query_odataservice(
            "p21_view_inventory_supplier",
            selects=[
                "cost",
                "inv_mast_uid",
                "item_id",
                "supplier_id",
            ],
            filters=supplier_filters,
        )
        if not supplier_data:
            return
        supplier = etl.fromdicts(supplier_data)
        if self._debug:
            etl.tocsv(supplier, self.file_name("supplier"))

        sales_customer_joined = etl.join(
            sales,
            customer,
            lkey="customer_id",
            rkey="customer_id_string",
        )
        if self._debug:
            etl.tocsv(supplier, self.file_name("sales_customer_joined"))

        final_join = etl.join(
            sales_customer_joined,
            supplier,
            lkey=("inv_mast_uid", "supplier_id"),
            rkey=("inv_mast_uid", "supplier_id"),
        )
        if self._debug:
            etl.tocsv(supplier, self.file_name("final_joined"))

        selected_columns = etl.cut(
            final_join,
            "bill2_country",
            "cogs_amount",
            "invoice_date",
            "invoice_no",
            "item_desc",
            "qty_shipped",
            "ship2_address1",
            "ship2_city",
            "ship2_name",
            "ship2_postal_code",
            "ship2_state",
            "unit_price",
            "federal_exemption_number",
            "other_exemption_number",
            "state_excise_tax_exemption_no",
            "cost",
            "item_id",
        )

        etl.tocsv(selected_columns, self.file_name("report"))
