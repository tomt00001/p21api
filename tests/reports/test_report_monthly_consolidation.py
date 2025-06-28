"""Tests for ReportMonthlyConsolidation."""

from datetime import datetime
from unittest.mock import Mock, patch


class TestReportMonthlyConsolidation:
    """Test cases for ReportMonthlyConsolidation."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for monthly consolidation report."""
        from p21api.report_monthly_consolidation import ReportMonthlyConsolidation

        report = ReportMonthlyConsolidation(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "monthly_consolidation_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test monthly consolidation report execution with data."""
        from p21api.report_monthly_consolidation import ReportMonthlyConsolidation

        # Mock consolidation data
        consolidation_data = [
            {
                "period": 1,
                "year_for_period": 2024,
                "total_amount": 10000.00,
                "invoice_count": 50,
                "customer_count": 25,
            }
        ]

        mock_odata_client.query_odataservice.return_value = (
            consolidation_data,
            "test_url",
        )
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportMonthlyConsolidation(
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
        """Test monthly consolidation report execution with no data."""
        from p21api.report_monthly_consolidation import ReportMonthlyConsolidation

        mock_odata_client.query_odataservice.return_value = ([], "test_url")

        report = ReportMonthlyConsolidation(
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
