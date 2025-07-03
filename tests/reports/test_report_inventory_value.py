"""Tests for ReportInventoryValue."""

from datetime import datetime
from unittest.mock import Mock, patch

from p21api.report_inventory_value import ReportInventoryValue


class TestReportInventoryValue:
    """Test cases for ReportInventoryValue."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for inventory value report."""
        report = ReportInventoryValue(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "inventory_value_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    @patch("petl.join")
    def test_run_complex_report(
        self, mock_join, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test complex inventory value report execution."""
        # Mock multiple data sources
        inventory_data = [{"item_id": "ITEM001", "qty": 100}]
        po_data = [{"item_id": "ITEM001", "po_qty": 50}]
        sales_data = [{"item_id": "ITEM001", "sales_qty": 25}]

        mock_odata_client.query_odataservice.side_effect = [
            (inventory_data, "url1"),
            (po_data, "url2"),
            (sales_data, "url3"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_join.return_value = mock_table

        report = ReportInventoryValue(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Should make multiple calls to query_odataservice
        assert mock_odata_client.query_odataservice.call_count >= 3
