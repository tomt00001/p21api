"""Tests for ReportMonthlyInvoices."""

from datetime import datetime
from unittest.mock import Mock, patch


class TestReportMonthlyInvoices:
    """Test cases for ReportMonthlyInvoices."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for monthly invoices report."""
        from p21api.report_monthly_invoices import ReportMonthlyInvoices

        report = ReportMonthlyInvoices(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "monthly_invoices_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test monthly invoices report execution with data."""
        from p21api.report_monthly_invoices import ReportMonthlyInvoices

        # Mock invoice data
        invoice_data = [
            {
                "invoice_no": "INV001",
                "invoice_date": "2024-01-15",
                "customer_id": 12345,
                "total_amount": 1500.00,
                "period": 1,
                "year_for_period": 2024,
            }
        ]

        mock_odata_client.query_odataservice.return_value = (invoice_data, "test_url")
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportMonthlyInvoices(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        mock_odata_client.query_odataservice.assert_called_once()
        mock_fromdicts.assert_called()
        mock_tocsv.assert_called()

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_no_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test monthly invoices report execution with no data."""
        from p21api.report_monthly_invoices import ReportMonthlyInvoices

        mock_odata_client.query_odataservice.return_value = ([], "test_url")

        report = ReportMonthlyInvoices(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        mock_odata_client.query_odataservice.assert_called_once()
        mock_fromdicts.assert_not_called()
        mock_tocsv.assert_not_called()
