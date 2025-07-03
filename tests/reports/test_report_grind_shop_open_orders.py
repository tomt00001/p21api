"""Tests for ReportGrindShopOpenOrders."""

from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch


class TestReportGrindShopOpenOrders:
    """Test cases for ReportGrindShopOpenOrders."""

    def test_file_name_prefix(self, mock_config, mock_odata_client):
        """Test file name prefix for grind shop open orders report."""
        from p21api.report_grind_shop_open_orders import ReportGrindShopOpenOrders

        report = ReportGrindShopOpenOrders(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        assert report.file_name_prefix == "grind_shop_open_orders_"

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
        """Test grind shop open orders report execution with data."""
        from p21api.report_grind_shop_open_orders import ReportGrindShopOpenOrders

        # Mock order header data
        order_hdr_data = [
            {
                "customer_id": 12096,
                "order_no": "SO001",
                "order_date": "2024-01-15",
                "requested_date": "2024-01-20",
                "promise_date": "2024-01-25",
                "taker": "RC",
                "delete_flag": "N",
                "completed": "N",
                "company_id": "CMS",
            }
        ]

        # Mock order line data
        order_line_data = [
            {
                "order_no": "SO001",
                "inv_mast_uid": 123,
                "qty_ordered": 10,
                "qty_allocated": 5,
                "qty_on_pick_tickets": 0,
                "qty_invoiced": 0,
                "qty_canceled": 0,
                "disposition": "Open",
                "delete_flag": "N",
                "complete": "N",
            }
        ]

        # Mock inventory master data
        inv_mast_data = [
            {
                "inv_mast_uid": 123,
                "item_id": "KDB001",
                "item_desc": "Test KDB Item",
            }
        ]

        # Mock customer data
        customer_data = [
            {
                "customer_id": 12096,
                "customer_name": "Test Customer",
            }
        ]

        # Configure mock client to return different data for different queries
        def mock_query_side_effect(
            endpoint: str, **kwargs: Any
        ) -> tuple[list[dict[str, Any]], str]:
            if endpoint == "p21_view_oe_hdr":
                return order_hdr_data, "url"
            elif endpoint == "p21_view_oe_line":
                return order_line_data, "url"
            elif endpoint == "p21_view_inv_mast":
                return inv_mast_data, "url"
            elif endpoint == "p21_view_customer":
                return customer_data, "url"
            return [], "url"

        mock_odata_client.query_odataservice.side_effect = mock_query_side_effect

        # Mock petl operations
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table
        mock_join.return_value = mock_table
        mock_cut.return_value = mock_table
        mock_sort.return_value = mock_table
        mock_select.return_value = mock_table

        # Create and run report
        report = ReportGrindShopOpenOrders(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        report.run()

        # Verify the client was called with correct parameters
        assert mock_odata_client.query_odataservice.call_count >= 4

        # Check that the order header query had correct filters
        order_hdr_call = mock_odata_client.query_odataservice.call_args_list[0]
        assert order_hdr_call[1]["endpoint"] == "p21_view_oe_hdr"
        assert "company_id eq 'CMS'" in order_hdr_call[1]["filters"]
        assert "taker eq 'RC'" in order_hdr_call[1]["filters"]
        assert "delete_flag eq 'N'" in order_hdr_call[1]["filters"]
        assert "completed ne 'Y'" in order_hdr_call[1]["filters"]

    def test_run_with_no_data(self, mock_config, mock_odata_client):
        """Test grind shop open orders report execution with no data."""
        from p21api.report_grind_shop_open_orders import ReportGrindShopOpenOrders

        # Configure mock client to return no data
        mock_odata_client.query_odataservice.return_value = ([], "url")

        # Create and run report
        report = ReportGrindShopOpenOrders(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        # Should return early without error
        report.run()

        # Should have called query_odataservice at least once
        assert mock_odata_client.query_odataservice.call_count >= 1
