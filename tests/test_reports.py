"""Tests for specific report implementations."""

from datetime import datetime
from unittest.mock import Mock, patch

from p21api.report_daily_sales import ReportDailySales
from p21api.report_inventory import ReportInventory
from p21api.report_inventory_value import ReportInventoryValue
from p21api.report_open_po import ReportOpenPO


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


class TestReportIntegration:
    """Integration tests for multiple reports."""

    def test_all_reports_have_unique_prefixes(self, mock_config, mock_odata_client):
        """Test that all reports have unique file name prefixes."""
        from p21api.config import Config

        report_classes = []
        for group in Config.get_config_report_groups().values():
            report_classes.extend(group)

        prefixes = []
        for report_class in report_classes:
            report = report_class(
                client=mock_odata_client,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                output_folder="test_output/",
                debug=False,
                config=mock_config,
            )
            prefixes.append(report.file_name_prefix)

        # All prefixes should be unique
        assert len(prefixes) == len(set(prefixes))

    def test_all_reports_can_be_instantiated(self, mock_config, mock_odata_client):
        """Test that all report classes can be instantiated without errors."""
        from p21api.config import Config

        report_classes = []
        for group in Config.get_config_report_groups().values():
            report_classes.extend(group)

        for report_class in report_classes:
            # Should not raise exception
            report = report_class(
                client=mock_odata_client,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                output_folder="test_output/",
                debug=False,
                config=mock_config,
            )

            # Should have required abstract methods implemented
            assert hasattr(report, "file_name_prefix")
            assert hasattr(report, "_run")
            assert callable(getattr(report, "_run"))


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
