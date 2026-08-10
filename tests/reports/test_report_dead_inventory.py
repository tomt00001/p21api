"""Tests for ReportDeadInventory."""

from datetime import datetime
from unittest.mock import patch

import petl as etl
from p21api.report_dead_inventory import ReportDeadInventory


class TestReportDeadInventory:
    def _make_report(self, mock_config, mock_odata_client):
        return ReportDeadInventory(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        report = self._make_report(mock_config, mock_odata_client)
        assert report.file_name_prefix == "dead_inventory_"

    @patch("petl.tocsv")
    def test_run_with_data(self, mock_tocsv, mock_config, mock_odata_client):
        # 1. inv_loc returns item with supplier
        inv_loc_row = {
            "item_id": "A",
            "qty_on_hand": 10,
            "standard_cost": 5.0,
            "primary_supplier_id": 123,
        }
        # 2. sales_history returns sale before cutoff
        sales_history_row = {"item_id": "A", "invoice_date": "2023-12-31"}
        # 3. supplier lookup returns supplier name
        supplier_row = {"supplier_id": 123, "supplier_name": "Test Supplier"}
        mock_odata_client.query.side_effect = [
            ([inv_loc_row], "url1"),
            ([sales_history_row], "url2"),
            ([{"item_id": "A", "date_created": "2023-01-15"}], "url3"),
            ([supplier_row], "url4"),
        ]

        report = self._make_report(mock_config, mock_odata_client)
        report._run()

        mock_tocsv.assert_called_once()
        rows = list(etl.dicts(mock_tocsv.call_args[0][0]))
        assert any(row.get("Supplier Name") == "Test Supplier" for row in rows), (
            f"Supplier Name not found in output rows: {rows}"
        )

    @patch("petl.tocsv")
    def test_run_missing_cost_and_supplier(
        self, mock_tocsv, mock_config, mock_odata_client
    ):
        """Item with no cost and no supplier should still appear, with blanks."""
        inv_loc_row = {
            "item_id": "A",
            "qty_on_hand": 10,
            "standard_cost": None,
            "primary_supplier_id": None,
        }
        sales_history_row = {"item_id": "A", "invoice_date": "2023-12-31"}
        # No primary_supplier_id anywhere -> supplier lookup query is skipped.
        mock_odata_client.query.side_effect = [
            ([inv_loc_row], "url1"),
            ([sales_history_row], "url2"),
            ([], "url3"),
        ]

        report = self._make_report(mock_config, mock_odata_client)
        report._run()

        assert mock_odata_client.query.call_count == 3
        rows = list(etl.dicts(mock_tocsv.call_args[0][0]))
        assert len(rows) == 1
        row = rows[0]
        assert row["Item ID"] == "A"
        assert row["Quantity on hand (QOH)"] == 10
        assert row["Unit cost"] is None
        assert row["Value on hand"] is None
        assert row["Supplier Name"] == ""

    @patch("petl.tocsv")
    def test_run_supplier_id_not_found_in_lookup(
        self, mock_tocsv, mock_config, mock_odata_client
    ):
        """A supplier_id with no matching row in the supplier lookup -> blank name."""
        inv_loc_row = {
            "item_id": "A",
            "qty_on_hand": 10,
            "standard_cost": 5.0,
            "primary_supplier_id": 999,
        }
        sales_history_row = {"item_id": "A", "invoice_date": "2023-12-31"}
        mock_odata_client.query.side_effect = [
            ([inv_loc_row], "url1"),
            ([sales_history_row], "url2"),
            ([], "url3"),
            ([], "url4"),  # supplier lookup returns nothing for id 999
        ]

        report = self._make_report(mock_config, mock_odata_client)
        report._run()

        assert mock_odata_client.query.call_count == 4
        rows = list(etl.dicts(mock_tocsv.call_args[0][0]))
        assert len(rows) == 1
        assert rows[0]["Supplier Name"] == ""

    @patch("petl.tocsv")
    def test_run_zero_and_negative_qty_excluded(
        self, mock_tocsv, mock_config, mock_odata_client
    ):
        """Items with zero or negative qty_on_hand never appear in the report."""
        inv_loc_rows = [
            {
                "item_id": "ZERO",
                "qty_on_hand": 0,
                "standard_cost": 5.0,
                "primary_supplier_id": None,
            },
            {
                "item_id": "NEG",
                "qty_on_hand": -3,
                "standard_cost": 5.0,
                "primary_supplier_id": None,
            },
        ]
        mock_odata_client.query.side_effect = [
            (inv_loc_rows, "url1"),
            ([], "url2"),  # no sales history
            ([], "url3"),  # no receipts
        ]
        report = self._make_report(mock_config, mock_odata_client)
        report._run()

        mock_tocsv.assert_not_called()

    @patch("petl.tocsv")
    def test_run_multiple_location_rows_summed(
        self, mock_tocsv, mock_config, mock_odata_client
    ):
        """qty_on_hand sums across multiple location rows for the same item;
        cost and supplier use the first non-null value encountered."""
        inv_loc_rows = [
            {
                "item_id": "A",
                "qty_on_hand": 5,
                "standard_cost": 10.0,
                "primary_supplier_id": 1,
            },
            {
                "item_id": "A",
                "qty_on_hand": 3,
                "standard_cost": 99.0,  # should be ignored - first non-null wins
                "primary_supplier_id": 2,  # should be ignored - first non-null wins
            },
        ]
        sales_history_row = {"item_id": "A", "invoice_date": "2023-12-31"}
        supplier_row = {"supplier_id": 1, "supplier_name": "Supplier One"}
        mock_odata_client.query.side_effect = [
            (inv_loc_rows, "url1"),
            ([sales_history_row], "url2"),
            ([], "url3"),
            ([supplier_row], "url4"),
        ]

        report = self._make_report(mock_config, mock_odata_client)
        report._run()

        rows = list(etl.dicts(mock_tocsv.call_args[0][0]))
        assert len(rows) == 1
        row = rows[0]
        assert row["Quantity on hand (QOH)"] == 8
        assert row["Unit cost"] == 10.0
        assert row["Value on hand"] == 80.0
        assert row["Supplier Name"] == "Supplier One"

    @patch("petl.tocsv")
    def test_run_invalid_qty_value_ignored(
        self, mock_tocsv, mock_config, mock_odata_client
    ):
        """A non-numeric qty_on_hand value is ignored rather than crashing;
        valid values for the same item still sum correctly."""
        inv_loc_rows = [
            {
                "item_id": "B",
                "qty_on_hand": "not-a-number",
                "standard_cost": None,
                "primary_supplier_id": None,
            },
            {
                "item_id": "B",
                "qty_on_hand": 5,
                "standard_cost": None,
                "primary_supplier_id": None,
            },
        ]
        mock_odata_client.query.side_effect = [
            (inv_loc_rows, "url1"),
            ([], "url2"),
            ([], "url3"),
        ]

        report = self._make_report(mock_config, mock_odata_client)
        report._run()

        rows = list(etl.dicts(mock_tocsv.call_args[0][0]))
        assert len(rows) == 1
        assert rows[0]["Quantity on hand (QOH)"] == 5.0
