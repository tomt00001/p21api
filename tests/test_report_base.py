"""Tests for report base functionality."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from p21api.report_base import ReportBase


class ConcreteReportForTesting(ReportBase):
    """Concrete implementation of ReportBase for testing."""

    @property
    def file_name_prefix(self) -> str:
        return "test_report_"

    def _run(self) -> None:
        """Test implementation of _run method."""
        pass


class TestReportBase:
    """Test cases for ReportBase class."""

    def test_report_base_initialization(self, mock_config, mock_odata_client):
        """Test ReportBase initialization."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        output_folder = "test_output/"

        report = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=start_date,
            end_date=end_date,
            output_folder=output_folder,
            debug=True,
            config=mock_config,
        )

        assert report._client == mock_odata_client
        assert report._start_date == start_date
        assert report._end_date == mock_config.end_date
        assert report._output_folder == output_folder
        assert report._debug == mock_config.debug

    def test_file_name_generation(self, mock_config, mock_odata_client):
        """Test file name generation."""
        start_date = datetime(2024, 1, 15)

        report = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=start_date,
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        file_name = report.file_name("data")
        expected = "test_output/test_report_data_2024-01-15.csv"
        assert file_name == expected

    def test_file_name_suffix_default_date(self, mock_config, mock_odata_client):
        """Test file name suffix with default date."""
        start_date = datetime(2024, 3, 10)

        report = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=start_date,
            end_date=datetime(2024, 3, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        suffix = report._file_name_suffix()
        assert suffix == "2024-03-10"

    def test_file_name_suffix_custom_date(self, mock_config, mock_odata_client):
        """Test file name suffix with custom date."""
        custom_date = datetime(2024, 5, 20)

        report = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        suffix = report._file_name_suffix(custom_date)
        assert suffix == "2024-05-20"

    def test_run_method_calls_internal_run(self, mock_config, mock_odata_client):
        """Test that run() calls _run()."""
        report = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        with patch.object(report, "_run") as mock_internal_run:
            report.run()
            mock_internal_run.assert_called_once()

    @patch("p21api.report_base.logger")
    def test_debug_printing(self, mock_logger, mock_config, mock_odata_client):
        """Test debug output when debug is enabled."""
        mock_config.debug = True

        _ = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=True,
            config=mock_config,
        )

        # Should call logger.info with the report name
        mock_logger.info.assert_called_once_with(
            "Running report ConcreteReportForTesting"
        )

    @patch("p21api.report_base.logger")
    def test_no_debug_printing(self, mock_logger, mock_config, mock_odata_client):
        """Test no debug output when debug is disabled."""
        mock_config.debug = False

        _ = ConcreteReportForTesting(
            client=mock_odata_client,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            output_folder="test_output/",
            debug=False,
            config=mock_config,
        )

        # Should not call logger.info when debug is disabled
        mock_logger.info.assert_not_called()

    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            # This should fail because we're trying to instantiate
            # an abstract class without implementing abstract methods
            ReportBase(
                client=Mock(),
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                output_folder="test/",
                debug=False,
                config=Mock(),
            )
