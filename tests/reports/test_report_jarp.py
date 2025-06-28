"""Tests for ReportJarp."""

from datetime import datetime
from unittest.mock import Mock, patch


class TestReportJarp:
    """Test cases for ReportJarp."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for JARP report."""
        from p21api.report_jarp import ReportJarp

        report = ReportJarp(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "jarp_"

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    @patch("petl.join")
    @patch("petl.cut")
    @patch("petl.sort")
    @patch("petl.select")
    def test_run_with_data(
        self,
        mock_select,
        mock_sort,
        mock_cut,
        mock_join,
        mock_fromdicts,
        mock_tocsv,
        mock_config,
        mock_odata_client,
    ):
        """Test JARP report execution with data."""
        from p21api.report_jarp import ReportJarp

        # Mock invoice data
        invoice_data = [
            {
                "bill2_name": "Test Company",
                "freight": 10.00,
                "invoice_date": "2024-01-15",
                "invoice_no": "INV001",
                "other_charge_amount": 5.00,
                "period": 1,
                "po_no": "PO001",
                "ship2_address1": "123 Test St",
                "tax_amount": 8.00,
                "total_amount": 123.00,
                "year_for_period": 2024,
                "ship_to_id": 12755,
                "salesrep_id": "REP001",
            }
        ]

        # Mock invoice line data
        invoice_line_data = [
            {
                "item_id": "ITEM001",
                "item_desc": "Test Item",
                "qty_requested": 10,
                "qty_shipped": 10,
                "unit_price": 10.00,
                "extended_price": 100.00,
                "customer_part_number": "CUST001",
                "invoice_no": "INV001",
                "line_no": 1,
            }
        ]

        # Mock sales history data
        sales_history_data = [
            {
                "item_id": "ITEM001",
                "item_desc": "Test Item",
                "unit_price": 10.00,
                "customer_id": 12755,
                "inv_mast_uid": 1001,
                "supplier_id": 100,
                "invoice_no": "INV001",
                "line_no": 1,
                "ship_to_id": 12755,
            }
        ]

        # Mock supplier data
        supplier_data = [
            {
                "inv_mast_uid": 1001,
                "supplier_id": 100,
                "item_id": "ITEM001",
            }
        ]

        mock_odata_client.query_odataservice.side_effect = [
            (invoice_data, "url1"),
            (invoice_line_data, "url2"),
            (sales_history_data, "url3"),
            (supplier_data, "url4"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_select.return_value = mock_table
        mock_join.return_value = mock_table
        mock_cut.return_value = mock_table
        mock_sort.return_value = mock_table

        report = ReportJarp(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Should make 4 calls to query_odataservice
        assert mock_odata_client.query_odataservice.call_count == 4
        mock_fromdicts.assert_called()
        mock_tocsv.assert_called()

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_no_invoice_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test JARP report execution with no invoice data."""
        from p21api.report_jarp import ReportJarp

        mock_odata_client.query_odataservice.return_value = ([], "test_url")

        report = ReportJarp(
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
    @patch("petl.select")
    def test_run_with_no_invoice_line_data(
        self, mock_select, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test JARP report execution with no invoice line data."""
        from p21api.report_jarp import ReportJarp

        invoice_data = [{"invoice_no": "INV001", "po_no": "PO001"}]

        mock_odata_client.query_odataservice.side_effect = [
            (invoice_data, "url1"),
            ([], "url2"),  # No invoice line data
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_select.return_value = mock_table

        report = ReportJarp(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Should make 2 calls and return early
        assert mock_odata_client.query_odataservice.call_count == 2

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    @patch("petl.select")
    def test_run_with_debug(
        self, mock_select, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test JARP report execution with debug enabled."""
        from p21api.report_jarp import ReportJarp

        invoice_data = [{"invoice_no": "INV001", "po_no": "PO001"}]
        invoice_line_data = [{"invoice_no": "INV001", "item_id": "ITEM001"}]
        sales_history_data = [{"invoice_no": "INV001", "supplier_id": 100}]
        supplier_data = [{"supplier_id": 100}]

        mock_odata_client.query_odataservice.side_effect = [
            (invoice_data, "url1"),
            (invoice_line_data, "url2"),
            (sales_history_data, "url3"),
            (supplier_data, "url4"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_select.return_value = mock_table

        report = ReportJarp(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=True,  # Enable debug
            config=mock_config,
        )

        report._run()

        # Should write debug CSV files
        assert (
            mock_tocsv.call_count >= 4
        )  # invoice, invoice_line, sales_history, supplier

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    @patch("petl.select")
    def test_run_with_po_filter(
        self, mock_select, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test JARP report execution with PO filtering."""
        from p21api.report_jarp import ReportJarp

        invoice_data = [
            {"invoice_no": "INV001", "po_no": "PO001"},
            {"invoice_no": "INV002", "po_no": "P123"},  # Should be filtered out
        ]

        mock_odata_client.query_odataservice.side_effect = [
            (invoice_data, "url1"),
            ([], "url2"),  # No invoice line data to stop early
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_select.return_value = mock_table

        report = ReportJarp(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report._run()

        # Should call select to filter out POs starting with "P"
        mock_select.assert_called()
