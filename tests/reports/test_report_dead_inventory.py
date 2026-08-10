"""Tests for ReportDeadInventory."""

from datetime import datetime
from unittest.mock import Mock, patch

from p21api.report_dead_inventory import ReportDeadInventory


class TestReportDeadInventory:
    def test_file_name_prefix(self, mock_config, mock_odata_client):
        report = ReportDeadInventory(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "dead_inventory_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_data(
        self,
        mock_fromdicts,
        mock_tocsv,
        mock_config,
        mock_odata_client,
    ):
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
        captured_rows = []

        def fake_fromdicts(rows):
            captured_rows.extend(rows)
            return Mock()

        mock_fromdicts.side_effect = fake_fromdicts
        report = ReportDeadInventory(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        report._run()
        mock_fromdicts.assert_called()
        mock_tocsv.assert_called()
        # Check that Supplier Name is present and correct
        assert any(
            row.get("Supplier Name") == "Test Supplier" for row in captured_rows
        ), f"Supplier Name not found in output rows: {captured_rows}"
