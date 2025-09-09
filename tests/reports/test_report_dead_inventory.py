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
        mock_odata_client.query_odataservice.side_effect = [
            # 1. inv_loc (item_id, qty_on_hand, standard_cost)
            ([{"item_id": "A", "qty_on_hand": 10, "standard_cost": 5.0}], "url1"),
            # 2. sales_history (item_id, invoice_date BEFORE cutoff)
            ([{"item_id": "A", "invoice_date": "2023-12-31"}], "url2"),
            # 3. inventory receipts (item_id, date_created)
            ([{"item_id": "A", "date_created": "2023-01-15"}], "url3"),
        ]
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
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
