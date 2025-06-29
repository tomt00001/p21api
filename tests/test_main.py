"""Tests for the main application entry point."""

from datetime import datetime
from unittest.mock import Mock, patch

import main
import pytest


class TestMain:
    """Test cases for main application functionality."""

    @patch("main.show_gui_dialog")
    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_with_gui_save_clicked(
        self, mock_config_class, mock_odata_client_class, mock_show_gui
    ):
        """Test main function with GUI interaction and save clicked."""
        # Setup mocks
        mock_config = Mock()
        mock_config.should_show_gui = True
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = datetime(2024, 1, 1)
        mock_config.model_dump.return_value = {"base_url": "http://example.com"}
        mock_config.get_reports.return_value = []
        mock_config.debug = False

        mock_config_class.return_value = mock_config

        mock_show_gui.return_value = ({"username": "test_user"}, True)

        mock_client = Mock()
        mock_odata_client_class.return_value = mock_client

        # Call main
        main.main()

        # Verify GUI was shown
        mock_show_gui.assert_called_once_with(config=mock_config)

        # Verify client was created
        mock_odata_client_class.assert_called_once_with(
            username="test_user",
            password="test_password",
            base_url="http://example.com",
        )

    @patch("main.show_gui_dialog")
    @patch("main.Config")
    def test_main_with_gui_cancel_clicked(self, mock_config_class, mock_show_gui):
        """Test main function with GUI interaction and cancel clicked."""
        mock_config = Mock()
        mock_config.should_show_gui = True

        mock_config_class.return_value = mock_config
        mock_show_gui.return_value = (None, False)

        # Should return early without creating client
        main.main()

        mock_show_gui.assert_called_once()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_without_gui(self, mock_config_class, mock_odata_client_class):
        """Test main function without GUI."""
        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = datetime(2024, 1, 1)
        mock_config.get_reports.return_value = []
        mock_config.debug = False

        mock_config_class.return_value = mock_config

        mock_client = Mock()
        mock_odata_client_class.return_value = mock_client

        main.main()

        mock_odata_client_class.assert_called_once_with(
            username="test_user",
            password="test_password",
            base_url="http://example.com",
        )

    @patch("main.Config")
    def test_main_missing_credentials(self, mock_config_class):
        """Test main function with missing credentials."""
        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = False

        mock_config_class.return_value = mock_config

        with pytest.raises(
            main.ConfigurationError, match="Username and password are required"
        ):
            main.main()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_missing_base_url(self, mock_config_class, mock_odata_client_class):
        """Test main function with missing base URL."""
        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = None

        mock_config_class.return_value = mock_config

        with pytest.raises(
            main.ConfigurationError, match="Missing required fields: base_url"
        ):
            main.main()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_missing_username(self, mock_config_class, mock_odata_client_class):
        """Test main function with missing username."""
        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = None

        mock_config_class.return_value = mock_config

        with pytest.raises(
            main.ConfigurationError, match="Missing required fields: username"
        ):
            main.main()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_missing_password(self, mock_config_class, mock_odata_client_class):
        """Test main function with missing password."""
        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = None

        mock_config_class.return_value = mock_config

        with pytest.raises(
            main.ConfigurationError, match="Missing required fields: password"
        ):
            main.main()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_missing_start_date(self, mock_config_class, mock_odata_client_class):
        """Test main function with missing start date."""
        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = None

        mock_config_class.return_value = mock_config

        with pytest.raises(
            main.ConfigurationError, match="Missing required fields: start_date"
        ):
            main.main()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_with_reports_success(
        self, mock_config_class, mock_odata_client_class
    ):
        """Test main function with successful report execution."""
        mock_report_class = Mock()
        mock_report = Mock()
        mock_report_class.return_value = mock_report

        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = datetime(2024, 1, 1)
        mock_config.end_date = datetime(2024, 1, 31)
        mock_config.output_folder = "test_output/"
        mock_config.debug = False
        mock_config.get_reports.return_value = [mock_report_class]

        mock_config_class.return_value = mock_config

        mock_client = Mock()
        mock_odata_client_class.return_value = mock_client

        main.main()

        # Verify report was instantiated and run
        mock_report_class.assert_called_once_with(
            client=mock_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )
        mock_report.run.assert_called_once()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_with_report_exception_debug_mode(
        self, mock_config_class, mock_odata_client_class
    ):
        """Test main function with report exception in debug mode."""
        mock_report_class = Mock()
        mock_report_class.__name__ = "TestReport"  # Add __name__ attribute
        mock_report = Mock()
        mock_report.run.side_effect = Exception("Test exception")
        mock_report_class.return_value = mock_report

        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = datetime(2024, 1, 1)
        mock_config.end_date = datetime(2024, 1, 31)
        mock_config.output_folder = "test_output/"
        mock_config.debug = True  # Debug mode enabled
        mock_config.get_reports.return_value = [mock_report_class]

        mock_config_class.return_value = mock_config

        mock_client = Mock()
        mock_odata_client_class.return_value = mock_client

        with pytest.raises(
            main.ReportExecutionError, match="Failed to execute TestReport"
        ):
            main.main()

    @patch("main.logger")
    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_with_report_exception_production_mode(
        self, mock_config_class, mock_odata_client_class, mock_logger
    ):
        """Test main function with report exception in production mode."""
        mock_report_class = Mock()
        mock_report_class.__name__ = "TestReport"  # Add __name__ attribute
        mock_report = Mock()
        mock_report.run.side_effect = Exception("Test exception")
        mock_report_class.return_value = mock_report

        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = datetime(2024, 1, 1)
        mock_config.end_date = datetime(2024, 1, 31)
        mock_config.output_folder = "test_output/"
        mock_config.debug = False  # Debug mode disabled
        mock_config.get_reports.return_value = [mock_report_class]
        mock_config.model_dump.return_value = {"username": "test_user"}

        mock_config_class.return_value = mock_config

        mock_client = Mock()
        mock_odata_client_class.return_value = mock_client

        with pytest.raises(main.ReportExecutionError):
            main.main()

        # Should log config (excluding password) when there are exceptions
        mock_config.model_dump.assert_called_with(exclude={"password"})
        mock_logger.error.assert_called()

    @patch("main.ODataClient")
    @patch("main.Config")
    def test_main_with_multiple_reports(
        self, mock_config_class, mock_odata_client_class
    ):
        """Test main function with multiple reports."""
        mock_report_class1 = Mock()
        mock_report1 = Mock()
        mock_report_class1.return_value = mock_report1

        mock_report_class2 = Mock()
        mock_report2 = Mock()
        mock_report_class2.return_value = mock_report2

        mock_config = Mock()
        mock_config.should_show_gui = False
        mock_config.has_login = True
        mock_config.base_url = "http://example.com"
        mock_config.username = "test_user"
        mock_config.password = "test_password"
        mock_config.start_date = datetime(2024, 1, 1)
        mock_config.end_date = datetime(2024, 1, 31)
        mock_config.output_folder = "test_output/"
        mock_config.debug = False
        mock_config.get_reports.return_value = [mock_report_class1, mock_report_class2]

        mock_config_class.return_value = mock_config

        mock_client = Mock()
        mock_odata_client_class.return_value = mock_client

        main.main()

        # Verify both reports were instantiated and run
        mock_report_class1.assert_called_once()
        mock_report1.run.assert_called_once()
        mock_report_class2.assert_called_once()
        mock_report2.run.assert_called_once()

    @patch("main.main")
    def test_main_module_entry_point(self, mock_main):
        """Test that the module can be run as __main__."""
        # This tests the if __name__ == "__main__": main() pattern
        with patch("__main__.__name__", "__main__"):
            exec(open("main.py").read())

        # Note: This test may need adjustment based on actual module structure
