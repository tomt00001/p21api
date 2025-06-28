"""Tests for ReportInventory."""

from datetime import datetime
from unittest.mock import Mock, patch

from p21api.report_inventory import ReportInventory


class TestReportInventory:
    """Test cases for ReportInventory."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for inventory report."""
        report = ReportInventory(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "inventory_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_data(
        self,
        mock_fromdicts,
        mock_tocsv,
        mock_config,
        mock_odata_client,
        sample_inventory_data,
    ):
        """Test inventory report execution with data."""
        mock_odata_client.query_odataservice.return_value = (
            sample_inventory_data,
            "test_url",
        )
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportInventory(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Inventory report makes multiple calls
        # (stockstatus, inventory_value, inactive_items)
        assert mock_odata_client.query_odataservice.call_count >= 1
        mock_fromdicts.assert_called()
        mock_tocsv.assert_called()
