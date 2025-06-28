"""Tests for ReportDailySales."""

from datetime import datetime
from unittest.mock import Mock, patch

from p21api.report_daily_sales import ReportDailySales


class TestReportDailySales:
    """Test cases for ReportDailySales."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for daily sales report."""
        report = ReportDailySales(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "daily_sales_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_data(
        self,
        mock_fromdicts,
        mock_tocsv,
        mock_config,
        mock_odata_client,
        sample_invoice_data,
    ):
        """Test report execution with data."""
        mock_odata_client.query_odataservice.return_value = (
            sample_invoice_data,
            "test_url",
        )
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportDailySales(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        mock_odata_client.query_odataservice.assert_called_once_with(
            "p21_view_invoice_hdr",
            start_date=datetime(2024, 1, 1),
            selects=[
                "bill2_name",
                "freight",
                "invoice_date",
                "invoice_no",
                "other_charge_amount",
                "period",
                "tax_amount",
                "total_amount",
                "year_for_period",
                "salesrep_id",
            ],
            order_by=["year_for_period asc", "invoice_no asc"],
        )
        mock_fromdicts.assert_called_once_with(sample_invoice_data)
        mock_tocsv.assert_called_once()

    def test_run_with_no_data(self, mock_config, mock_odata_client):
        """Test report execution with no data."""
        mock_odata_client.query_odataservice.return_value = (None, "test_url")

        report = ReportDailySales(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        # Should not raise exception
        report._run()
