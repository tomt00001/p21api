"""Tests for ReportOpenOrders."""

from datetime import datetime
from unittest.mock import Mock, patch


class TestReportOpenOrders:
    """Test cases for ReportOpenOrders."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for open orders report."""
        from p21api.report_open_orders import ReportOpenOrders

        report = ReportOpenOrders(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "open_orders_"

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
        """Test open orders report execution with data."""
        from p21api.report_open_orders import ReportOpenOrders

        # Mock order data
        order_data = [
            {
                "completed": "N",
                "customer_id": 12087,
                "disposition": "Open",
                "item_id": "ITEM001",
                "line_no": 1,
                "order_date": "2024-01-15",
                "order_no": "ORD001",
                "po_no": "PO001",
                "qty_allocated": 5,
                "qty_canceled": 0,
                "qty_invoiced": 0,
                "qty_on_pick_tickets": 0,
                "qty_ordered": 10,
                "quote_flag": "N",
                "ship2_name": "Test Company",
            }
        ]

        # Mock order ack line data
        order_ack_line_data = [
            {
                "item_desc": "Test Item Description",
                "item_id": "ITEM001",
                "line_number": 1,
                "order_no": "ORD001",
            }
        ]

        mock_odata_client.query_odataservice.side_effect = [
            (order_data, "url1"),
            (order_ack_line_data, "url2"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_join.return_value = mock_table
        mock_cut.return_value = mock_table
        mock_sort.return_value = mock_table

        report = ReportOpenOrders(
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
        mock_join.assert_called()
        mock_cut.assert_called()
        mock_sort.assert_called()
        mock_tocsv.assert_called()

    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_run_with_no_order_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test open orders report execution with no order data."""
        from p21api.report_open_orders import ReportOpenOrders

        mock_odata_client.query_odataservice.return_value = ([], "test_url")

        report = ReportOpenOrders(
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
    def test_run_with_no_ack_line_data(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test open orders report execution with no ack line data."""
        from p21api.report_open_orders import ReportOpenOrders

        order_data = [{"order_no": "ORD001", "customer_id": 12087}]

        mock_odata_client.query_odataservice.side_effect = [
            (order_data, "url1"),
            ([], "url2"),  # No ack line data
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportOpenOrders(
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
    def test_run_with_debug(
        self, mock_fromdicts, mock_tocsv, mock_config, mock_odata_client
    ):
        """Test open orders report execution with debug enabled."""
        from p21api.report_open_orders import ReportOpenOrders

        order_data = [{"order_no": "ORD001", "customer_id": 12087}]
        order_ack_line_data = [{"order_no": "ORD001", "item_id": "ITEM001"}]

        mock_odata_client.query_odataservice.side_effect = [
            (order_data, "url1"),
            (order_ack_line_data, "url2"),
        ]

        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        report = ReportOpenOrders(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=True,  # Enable debug
            config=mock_config,
        )

        report._run()

        # Should write debug CSV files
        assert mock_tocsv.call_count >= 3  # order, order_ack_line, joined
