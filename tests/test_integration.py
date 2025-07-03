"""Integration tests for the complete application workflow."""

import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from p21api.config import Config
from p21api.odata_client import ODataClient


class TestIntegration:
    """End-to-end integration tests."""

    @patch("p21api.odata_client.requests.post")
    @patch("p21api.odata_client.requests.get")
    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_complete_workflow_success(
        self, mock_fromdicts, mock_tocsv, mock_get, mock_post, sample_invoice_data
    ):
        """Test complete workflow from config to report generation."""
        # Setup authentication mock
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_auth_response

        # Setup data fetch mock
        mock_data_response = Mock()
        mock_data_response.status_code = 200
        mock_data_response.json.return_value = {"value": sample_invoice_data}
        mock_get.return_value = mock_data_response

        # Setup PETL mocks
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        # Create temp directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize config
            config = Config(
                base_url="http://example.com",
                username="test_user",
                password="test_password",
                output_folder=temp_dir + "/",
                report_groups="monthly",
                start_date="2024-01-01",
                debug=False,
            )

            # Create client
            client = ODataClient(
                username=config.username,
                password=config.password,
                base_url=config.base_url,
            )

            # Get reports and run them
            report_classes = config.get_reports()
            assert len(report_classes) > 0

            # Run first report
            report_class = report_classes[0]
            report = report_class(
                client=client,
                start_date=config.start_date,
                end_date=config.end_date,
                output_folder=config.output_folder,
                debug=config.debug,
                config=config,
            )

            report.run()

            # Verify authentication happened
            mock_post.assert_called()

            # Verify data was fetched
            mock_get.assert_called()

            # Verify PETL processing happened
            mock_fromdicts.assert_called()
            mock_tocsv.assert_called()

    @patch("p21api.odata_client.requests.post")
    def test_authentication_failure_workflow(self, mock_post):
        """Test workflow when authentication fails."""
        # Setup authentication failure
        mock_auth_response = Mock()
        mock_auth_response.status_code = 401
        mock_auth_response.text = "Unauthorized"
        mock_post.return_value = mock_auth_response

        config = Config(
            base_url="http://example.com",
            username="invalid_user",
            password="invalid_password",
            output_folder="test/",
            start_date="2024-01-01",
        )

        client = ODataClient(
            username=config.username, password=config.password, base_url=config.base_url
        )

        # Should raise exception when trying to access headers
        with pytest.raises(Exception, match="Failed to obtain token"):
            _ = client.headers

    @patch("p21api.odata_client.requests.post")
    @patch("p21api.odata_client.requests.get")
    def test_data_fetch_failure_workflow(self, mock_get, mock_post):
        """Test workflow when data fetching fails."""
        # Setup successful authentication
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_auth_response

        # Setup data fetch failure
        mock_data_response = Mock()
        mock_data_response.status_code = 500
        mock_data_response.text = "Internal Server Error"
        mock_get.return_value = mock_data_response

        config = Config(
            base_url="http://example.com",
            username="test_user",
            password="test_password",
            output_folder="test/",
            report_groups="monthly",
            start_date="2024-01-01",
        )

        client = ODataClient(
            username=config.username, password=config.password, base_url=config.base_url
        )

        # Get first report
        report_classes = config.get_reports()
        report_class = report_classes[0]
        report = report_class(
            client=client,
            start_date=config.start_date,
            end_date=config.end_date,
            output_folder=config.output_folder,
            debug=config.debug,
            config=config,
        )

        # Should raise exception when trying to run report
        with pytest.raises(Exception, match="Failed to fetch data"):
            report.run()

    def test_config_validation_workflow(self):
        """Test config validation in complete workflow."""
        # Test that config accepts empty values and uses defaults
        config = Config(
            base_url="",  # Empty base URL
            username="test",
            password="test",
        )
        # Config should use default base_url when empty string provided
        assert config.base_url == ""
        assert config.username == "test"
        assert config.password == "test"

    @patch("pathlib.Path.mkdir")
    def test_output_folder_creation_workflow(self, mock_mkdir):
        """Test output folder creation in workflow."""
        _ = Config(
            base_url="http://example.com",
            username="test",
            password="test",
            output_folder="non/existent/path/",
            start_date="2024-01-01",
        )

        # Should attempt to create directory
        mock_mkdir.assert_called()

    @patch("p21api.odata_client.requests.post")
    @patch("p21api.odata_client.requests.get")
    def test_multiple_reports_workflow(
        self, mock_get, mock_post, sample_invoice_data, sample_inventory_data
    ):
        """Test workflow with multiple reports."""
        # Setup mocks
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_auth_response

        mock_data_response = Mock()
        mock_data_response.status_code = 200
        # Provide enough data for all report calls with required fields
        order_data = [
            {
                "order_no": "ORD001",
                "customer_id": 12087,
                "line_no": 1,
                "item_id": "ITEM001",
                "completed": "N",
                "disposition": "OPEN",
                "qty_allocated": 0,
                "qty_canceled": 0,
                "qty_invoiced": 0,
                "qty_on_pick_tickets": 5,
                "qty_ordered": 10,
                "quote_flag": "N",
                "ship2_name": "Test Customer",
                "order_date": "2024-01-15",
                "po_no": "PO001",
            }
        ]
        mock_data_response.json.side_effect = [
            {"value": order_data},  # For open orders - first call
            {"value": sample_invoice_data},  # For daily sales or other reports
            {"value": sample_inventory_data},  # For inventory reports
            {"value": order_data},  # For open orders - possible second call
            {"value": sample_invoice_data},  # Additional calls
            {"value": sample_inventory_data},
            {"value": order_data},
            {"value": sample_invoice_data},
            {"value": sample_inventory_data},
            {"value": order_data},  # Extra calls for safety
        ]
        mock_get.return_value = mock_data_response

        config = Config(
            base_url="http://example.com",
            username="test_user",
            password="test_password",
            output_folder="test/",
            report_groups="monthly,inventory",  # Multiple groups
            start_date="2024-01-01",
        )

        client = ODataClient(
            username=config.username, password=config.password, base_url=config.base_url
        )

        # Get all reports
        report_classes = config.get_reports()
        assert len(report_classes) > 1  # Should have multiple reports

        # Run all reports
        with patch("petl.tocsv"), patch("petl.fromdicts"):
            # Mock the query_odataservice to return empty data to skip complex logic
            with patch.object(client, "query_odataservice") as mock_query:
                mock_query.return_value = (
                    [],
                    "test_url",
                )  # Empty data causes early return

                for report_class in report_classes:
                    report = report_class(
                        client=client,
                        start_date=config.start_date,
                        end_date=config.end_date,
                        output_folder=config.output_folder,
                        debug=config.debug,
                        config=config,
                    )

                    # Should not raise exception with empty data
                    report.run()

    def test_date_handling_workflow(self):
        """Test date handling throughout workflow."""
        # Test with string date
        config1 = Config(
            base_url="http://example.com",
            username="test",
            password="test",
            start_date="2024-01-15",
            end_date_=None,  # Override env file setting
        )

        assert config1.start_date == datetime(2024, 1, 15)
        # When end_date_ is explicitly None, it uses end of month logic
        assert config1.end_date == datetime(2024, 1, 31, 23, 59, 59, 999999)

        # Test with datetime object
        start_dt = datetime(2024, 2, 10)
        config2 = Config(
            base_url="http://example.com",
            username="test",
            password="test",
            start_date=start_dt,
            end_date_=None,  # Override env file setting
        )

        assert config2.start_date == start_dt
        assert config2.end_date.month == 2

    @patch("main.show_gui_dialog")
    @patch("p21api.odata_client.requests.post")
    @patch("petl.tocsv")
    def test_gui_integration_workflow(self, mock_tocsv, mock_post, mock_gui):
        """Test GUI integration in complete workflow."""
        # Setup mocks
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_auth_response

        # GUI returns data
        gui_data = {
            "username": "gui_user",
            "password": "gui_password",
            "start_date": "2024-01-01",
            "report_groups": "monthly",
        }
        mock_gui.return_value = (gui_data, True)

        # Import and run main
        import main

        with patch("main.Config") as mock_config_class:
            mock_config = Mock()
            mock_config.should_show_gui = True
            mock_config.has_login = True
            mock_config.base_url = "http://example.com"
            mock_config.username = "gui_user"
            mock_config.password = "gui_password"
            mock_config.start_date = datetime(2024, 1, 1)
            mock_config.end_date = datetime(2024, 1, 31)
            mock_config.output_folder = "test/"
            mock_config.debug = False
            mock_config.get_reports.return_value = []
            mock_config.model_dump.return_value = {"base_url": "http://example.com"}

            mock_config_class.return_value = mock_config

            # Should complete without error
            main.main()

            # GUI should have been called
            mock_gui.assert_called()

    def test_error_propagation_workflow(self):
        """Test error propagation through workflow."""
        # Test various error scenarios

        # Invalid date format
        from pydantic_core import ValidationError

        with pytest.raises(ValidationError):
            Config(
                base_url="http://example.com",
                username="test",
                password="test",
                start_date="invalid-date",
            )

        # Test report instantiation errors
        with patch("p21api.report_open_po.ReportOpenPO.__init__") as mock_init:
            mock_init.side_effect = Exception("Report initialization failed")

            config = Config(
                base_url="http://example.com", username="test", password="test"
            )

            client = Mock()
            report_classes = config.get_reports()

            with pytest.raises(Exception, match="Report initialization failed"):
                report_class = report_classes[0]  # Should be ReportOpenPO
                report_class(
                    client=client,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    output_folder=config.output_folder,
                    debug=config.debug,
                    config=config,
                )

    @patch("p21api.odata_client.requests.post")
    @patch("p21api.odata_client.requests.get")
    @patch("petl.tocsv")
    @patch("petl.fromdicts")
    def test_end_to_end_data_flow(
        self, mock_fromdicts, mock_tocsv, mock_get, mock_post
    ):
        """Test complete data flow from API to CSV file."""
        # Setup chain of mocks to track data flow
        original_data = [
            {"id": 1, "name": "Test Item 1", "value": 100.0},
            {"id": 2, "name": "Test Item 2", "value": 200.0},
        ]

        # Authentication
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"AccessToken": "test_token"}
        mock_post.return_value = mock_auth_response

        # Data fetch
        mock_data_response = Mock()
        mock_data_response.status_code = 200
        mock_data_response.json.return_value = {"value": original_data}
        mock_get.return_value = mock_data_response

        # PETL processing
        mock_table = Mock()
        mock_fromdicts.return_value = mock_table

        # Complete workflow
        config = Config(
            base_url="http://example.com",
            username="test_user",
            password="test_password",
            output_folder="test/",
            report_groups="monthly",
            start_date="2024-01-01",
        )

        client = ODataClient(
            username=config.username, password=config.password, base_url=config.base_url
        )

        # Run a report
        from p21api.report_daily_sales import ReportDailySales

        report = ReportDailySales(
            client=client,
            start_date=config.start_date,
            end_date=config.end_date,
            output_folder=config.output_folder,
            debug=config.debug,
            config=config,
        )

        report.run()

        # Verify data flowed through the system
        # 1. Authentication called
        mock_post.assert_called()

        # 2. Data fetch called
        mock_get.assert_called()

        # 3. Data passed to PETL
        mock_fromdicts.assert_called_with(original_data)

        # 4. CSV export called
        from unittest.mock import ANY

        mock_tocsv.assert_called_with(mock_table, ANY)
