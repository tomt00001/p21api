"""Tests for ReportKennametalPos."""

from datetime import datetime
from unittest.mock import Mock, patch


class TestReportKennametalPos:
    """Test cases for ReportKennametalPos."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for Kennametal POS report."""
        from p21api.report_kennametal_pos import ReportKennametalPos

        report = ReportKennametalPos(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "kennametal_pos_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    @patch("petl.join")
    @patch("petl.cut")
    @patch("petl.sort")
    def test_run_with_data(
        self,
        mock_sort,
        mock_cut,
        mock_join,
        mock_fromdicts,
        mock_tocsv,
        mock_config,
        mock_odata_client,
    ):
        """Test Kennametal POS report execution with data."""
        from p21api.report_kennametal_pos import ReportKennametalPos

        # Mock the datetime filter methods
        mock_odata_client.get_datetime_filter.return_value = [
            "invoice_date ge '2024-01-01'"
        ]
        mock_odata_client.get_current_month_end_date.return_value = datetime(
            2024, 1, 31
        )

        # Mock sales data
        sales_data = [
            {
                "invoice_no": "INV001",
                "item_id": "ITEM001",
                "supplier_id": 11777,
                "unit_price": 50.00,
                "extended_price": 500.00,
            }
        ]

        # Mock PO data
        po_data = [
            {"po_no": "PO001", "line_no": 1, "item_id": "ITEM001", "unit_cost": 45.00}
        ]

        mock_odata_client.query_odataservice.side_effect = [
            (sales_data, "url1"),
            (po_data, "url2"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_join.return_value = mock_table
        mock_cut.return_value = mock_table
        mock_sort.return_value = mock_table

        report = ReportKennametalPos(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Should make 2 calls to query_odataservice
        assert mock_odata_client.query_odataservice.call_count == 2
        mock_fromdicts.assert_called()
        mock_tocsv.assert_called()

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_no_po_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test Kennametal POS report execution with no sales data."""
        from p21api.report_kennametal_pos import ReportKennametalPos

        # Mock the datetime filter methods
        mock_odata_client.get_datetime_filter.return_value = [
            "invoice_date ge '2024-01-01'"
        ]
        mock_odata_client.get_current_month_end_date.return_value = datetime(
            2024, 1, 31
        )

        mock_odata_client.query_odataservice.return_value = ([], "test_url")

        report = ReportKennametalPos(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Should only make 1 call and return early
        assert mock_odata_client.query_odataservice.call_count == 1
        mock_fromdicts.assert_not_called()
        mock_tocsv.assert_not_called()

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_debug(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test Kennametal POS report execution with debug enabled."""
        from p21api.report_kennametal_pos import ReportKennametalPos

        # Mock the datetime filter methods
        mock_odata_client.get_datetime_filter.return_value = [
            "invoice_date ge '2024-01-01'"
        ]
        mock_odata_client.get_current_month_end_date.return_value = datetime(
            2024, 1, 31
        )

        sales_data = [{"invoice_no": "INV001", "supplier_id": 11777}]
        po_data = [{"po_no": "PO001", "item_id": "ITEM001"}]

        mock_odata_client.query_odataservice.side_effect = [
            (sales_data, "url1"),
            (po_data, "url2"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportKennametalPos(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=True,  # Enable debug
            config=mock_config,
        )

        report._run()

        # Should write debug CSV files
        assert mock_tocsv.call_count >= 2
