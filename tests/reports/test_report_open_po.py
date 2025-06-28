"""Tests for ReportOpenPO."""

from datetime import datetime
from unittest.mock import Mock, patch

from p21api.report_open_po import ReportOpenPO


class TestReportOpenPO:
    """Test cases for ReportOpenPO."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for open PO report."""
        report = ReportOpenPO(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "open_po_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test open PO report execution with data."""
        po_data = [
            {
                "po_no": "PO001",
                "supplier_id": "12345",
                "vendor_name": "Test Vendor",
                "po_date": "2024-01-15",
                "order_date": "2024-01-15",
                "expected_date": "2024-01-30",
                "total_amount": 1000.00,
                "status": "Open",
            }
        ]

        mock_odata_client.query_odataservice.return_value = (po_data, "test_url")
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportOpenPO(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Open PO report makes multiple calls (po_hdr, po_line, supplier)
        assert mock_odata_client.query_odataservice.call_count >= 1
        mock_fromdicts.assert_called()
        mock_tocsv.assert_called()
