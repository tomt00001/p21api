import petl as etl

from report_base import Report_Base


class ReportKennametalPos(Report_Base):
    @property
    def file_name_prefix(self) -> str:
        return "kennametal_pos_"

    def run(self) -> None:
        # p21_sales_history_view
        # bill2_country
        # customer_id
        # cogs_amount
        # inv_mast_uid
        # invoice_date
        # invoice_no
        # item_desc
        # qty_shipped
        # ship2_address1
        # ship2_city
        # ship2_name
        # ship2_postal_code
        # ship2_state
        # supplier_id
        # unit_price

        # filters = ["supplier_id eq 11777"]
        # AND ( p21_sales_history_view.year_for_period = $2017 )
        # AND ( p21_sales_history_view.period = $6 ) )

        p21_view_customer_data = self._client.query(
            "p21_view_customer",
            start_date=self._start_date,
            select=[
                "customer_id_string",
                "federal_exemption_number",
                "other_exemption_number",
                "state_excise_tax_exemption_no",
            ],
        )
        p21_view_customer = etl.fromdicts(p21_view_customer_data)
        etl.tocsv(
            p21_view_customer,
            self.file_name("p21_view_customer"),
        )

        p21_view_inventory_supplier_data = self._client.query(
            "p21_view_inventory_supplier",
            start_date=self._start_date,
            select=["cost", "item_id", "inv_mast_uid", "supplier_id"],
        )
        p21_view_inventory_supplier = etl.fromdicts(p21_view_inventory_supplier_data)
        etl.tocsv(
            p21_view_inventory_supplier,
            self.file_name("p21_view_inventory_supplier"),
        )
