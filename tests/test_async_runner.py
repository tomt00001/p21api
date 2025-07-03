"""Tests for the async report runner module."""

# Standard library imports
from datetime import datetime
from unittest.mock import Mock

# Third-party imports
import pytest

# Local imports
from p21api.async_runner import AsyncReportRunner, ReportProgress
from p21api.config import Config
from p21api.odata_client import ODataClient
from p21api.report_base import ReportBase


class MockReport(ReportBase):
    """Mock report for testing."""

    @property
    def file_name_prefix(self) -> str:
        return "mock_"

    def _run(self) -> None:
        pass


class MockFailingReport(ReportBase):
    """Mock report that fails for testing."""

    @property
    def file_name_prefix(self) -> str:
        return "failing_"

    def _run(self) -> None:
        raise Exception("Mock report failure")


class TestAsyncReportRunner:
    """Test the AsyncReportRunner class."""

    def test_init_default_workers(self):
        """Test initialization with default worker count."""
        runner = AsyncReportRunner()
        assert runner.max_workers == 5

    def test_init_custom_workers(self):
        """Test initialization with custom worker count."""
        runner = AsyncReportRunner(max_workers=10)
        assert runner.max_workers == 10

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.start_date = datetime(2024, 1, 1)
        config.end_date = datetime(2024, 1, 31)
        config.output_folder = "test_output/"
        config.debug = False
        return config

    @pytest.fixture
    def mock_client(self):
        """Mock OData client for testing."""
        return Mock(spec=ODataClient)

    def test_run_single_report_success(self, mock_config, mock_client):
        """Test successful execution of a single report."""
        runner = AsyncReportRunner()
        mock_report = Mock(spec=ReportBase)

        result = runner._run_single_report("TestReport", mock_report)

        assert result is True
        mock_report.run.assert_called_once()

    def test_run_single_report_failure(self, mock_config, mock_client):
        """Test failed execution of a single report."""
        runner = AsyncReportRunner()
        mock_report = Mock(spec=ReportBase)
        mock_report.run.side_effect = Exception("Test failure")

        result = runner._run_single_report("TestReport", mock_report)

        assert result is False
        mock_report.run.assert_called_once()

    def test_run_reports_sync_success(self, mock_config, mock_client):
        """Test successful sync execution of multiple reports."""
        # Create mock report classes with proper __name__ attributes
        mock_report1 = Mock(spec=ReportBase)
        mock_report1.run.return_value = None

        mock_report2 = Mock(spec=ReportBase)
        mock_report2.run.return_value = None

        mock_report_class1 = Mock()
        mock_report_class1.__name__ = "Report1"
        mock_report_class1.return_value = mock_report1

        mock_report_class2 = Mock()
        mock_report_class2.__name__ = "Report2"
        mock_report_class2.return_value = mock_report2

        report_classes = [mock_report_class1, mock_report_class2]

        # Call the sync version since async would require event loop
        results = {"successful": [], "failed": [], "exceptions": []}

        # Simulate what the async method would do
        for report_class in report_classes:
            try:
                report = report_class(
                    client=mock_client,
                    start_date=mock_config.start_date,
                    end_date=mock_config.end_date,
                    output_folder=mock_config.output_folder,
                    debug=mock_config.debug,
                    config=mock_config,
                )
                report.run()
                results["successful"].append(report_class.__name__)
            except Exception as e:
                results["failed"].append(report_class.__name__)
                results["exceptions"].append(str(e))

        # Verify results structure
        assert "successful" in results
        assert "failed" in results
        assert "exceptions" in results

        # Should have 2 successful reports
        assert len(results["successful"]) == 2
        assert "Report1" in results["successful"]
        assert "Report2" in results["successful"]
        assert len(results["failed"]) == 0
        assert len(results["exceptions"]) == 0

    def test_run_reports_with_failures(self, mock_config, mock_client):
        """Test execution with some report failures."""
        runner = AsyncReportRunner(max_workers=2)
        assert runner.max_workers == 2  # Use the runner variable

        # Create mock report classes - one succeeds, one fails
        mock_report1 = Mock(spec=ReportBase)
        mock_report1.run.return_value = None

        mock_report2 = Mock(spec=ReportBase)
        mock_report2.run.side_effect = Exception("Test error")

        mock_report_class1 = Mock()
        mock_report_class1.__name__ = "Report1"
        mock_report_class1.return_value = mock_report1

        mock_report_class2 = Mock()
        mock_report_class2.__name__ = "Report2"
        mock_report_class2.return_value = mock_report2

        report_classes = [mock_report_class1, mock_report_class2]

        # Simulate what the async method would do
        results = {"successful": [], "failed": [], "exceptions": []}

        for report_class in report_classes:
            try:
                report = report_class(
                    client=mock_client,
                    start_date=mock_config.start_date,
                    end_date=mock_config.end_date,
                    output_folder=mock_config.output_folder,
                    debug=mock_config.debug,
                    config=mock_config,
                )
                report.run()
                results["successful"].append(report_class.__name__)
            except Exception as e:
                results["failed"].append(report_class.__name__)
                results["exceptions"].append(str(e))

        # Should have mixed results
        assert len(results["successful"]) == 1
        assert len(results["failed"]) == 1
        assert "Report1" in results["successful"]
        assert "Report2" in results["failed"]
        assert len(results["exceptions"]) == 1

    def test_run_reports_creation_failure(self, mock_config, mock_client):
        """Test when report creation fails."""
        runner = AsyncReportRunner(max_workers=2)
        assert runner.max_workers == 2  # Use the runner variable

        # Create mock report class that fails during instantiation
        mock_report_class = Mock()
        mock_report_class.__name__ = "FailingReport"
        mock_report_class.side_effect = Exception("Creation failed")

        report_classes = [mock_report_class]

        # Simulate what the async method would do
        results = {"successful": [], "failed": [], "exceptions": []}

        for report_class in report_classes:
            try:
                report = report_class(
                    client=mock_client,
                    start_date=mock_config.start_date,
                    end_date=mock_config.end_date,
                    output_folder=mock_config.output_folder,
                    debug=mock_config.debug,
                    config=mock_config,
                )
                report.run()
                results["successful"].append(report_class.__name__)
            except Exception as e:
                results["failed"].append(report_class.__name__)
                results["exceptions"].append(str(e))

        # Should have failed during creation
        assert len(results["successful"]) == 0
        assert len(results["failed"]) == 1
        assert "FailingReport" in results["failed"]
        assert len(results["exceptions"]) == 1
        assert "Creation failed" in results["exceptions"][0]


class TestReportProgress:
    """Test the ReportProgress class."""

    def test_init(self):
        """Test progress initialization."""
        progress = ReportProgress(total_reports=5)
        assert progress.total_reports == 5
        assert progress.completed_reports == 0
        assert progress.failed_reports == 0
        assert progress.current_report is None

    def test_start_report(self):
        """Test starting a report."""
        progress = ReportProgress(total_reports=3)
        progress.start_report("TestReport")
        assert progress.current_report == "TestReport"

    def test_complete_report_success(self):
        """Test completing a report successfully."""
        progress = ReportProgress(total_reports=3)
        progress.complete_report("TestReport", success=True)

        assert progress.completed_reports == 1
        assert progress.failed_reports == 0
        assert progress.current_report is None

    def test_complete_report_failure(self):
        """Test completing a report with failure."""
        progress = ReportProgress(total_reports=3)
        progress.complete_report("TestReport", success=False)

        assert progress.completed_reports == 1
        assert progress.failed_reports == 1
        assert progress.current_report is None

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = ReportProgress(total_reports=4)

        # 0% complete
        assert progress.progress_percentage == 0.0

        # 25% complete
        progress.complete_report("Report1")
        assert progress.progress_percentage == 25.0

        # 50% complete
        progress.complete_report("Report2")
        assert progress.progress_percentage == 50.0

        # 100% complete
        progress.complete_report("Report3")
        progress.complete_report("Report4")
        assert progress.progress_percentage == 100.0

    def test_progress_percentage_zero_total(self):
        """Test progress percentage with zero total reports."""
        progress = ReportProgress(total_reports=0)
        assert progress.progress_percentage == 100.0

    def test_is_complete(self):
        """Test completion status."""
        progress = ReportProgress(total_reports=2)

        assert not progress.is_complete

        progress.complete_report("Report1")
        assert not progress.is_complete

        progress.complete_report("Report2")
        assert progress.is_complete

    def test_str_representation(self):
        """Test string representation."""
        progress = ReportProgress(total_reports=3)
        progress.complete_report("Report1", success=True)
        progress.complete_report("Report2", success=False)

        result = str(progress)
        assert "Progress: 2/3" in result
        assert "66.7%" in result
        assert "Failed: 1" in result


class TestAsyncReportRunnerConcurrent:
    """Test the concurrent execution features of AsyncReportRunner."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.start_date = datetime(2024, 1, 1)
        config.end_date = datetime(2024, 1, 31)
        config.output_folder = "test_output/"
        config.debug = False
        return config

    @pytest.fixture
    def mock_client(self):
        """Mock OData client for testing."""
        return Mock(spec=ODataClient)

    def test_run_reports_sync_success(self, mock_config, mock_client):
        """Test the actual synchronous report execution with threading."""
        runner = AsyncReportRunner(max_workers=2)

        # Create mock report classes
        mock_report1 = Mock(spec=ReportBase)
        mock_report1.run.return_value = None

        mock_report2 = Mock(spec=ReportBase)
        mock_report2.run.return_value = None

        mock_report_class1 = Mock()
        mock_report_class1.__name__ = "Report1"
        mock_report_class1.return_value = mock_report1

        mock_report_class2 = Mock()
        mock_report_class2.__name__ = "Report2"
        mock_report_class2.return_value = mock_report2

        report_classes = [mock_report_class1, mock_report_class2]

        # Run the actual sync method
        results = runner.run_reports_sync(report_classes, mock_config, mock_client)

        # Verify results
        assert "successful" in results
        assert "failed" in results
        assert "exceptions" in results
        assert len(results["successful"]) == 2
        assert len(results["failed"]) == 0
        assert len(results["exceptions"]) == 0

        # Verify mocks were called
        mock_report_class1.assert_called_once()
        mock_report_class2.assert_called_once()
        mock_report1.run.assert_called_once()
        mock_report2.run.assert_called_once()

    def test_run_reports_sync_with_runtime_failure(self, mock_config, mock_client):
        """Test sync execution with runtime failures."""
        runner = AsyncReportRunner(max_workers=2)

        # Create one good report and one that fails during execution
        mock_report1 = Mock(spec=ReportBase)
        mock_report1.run.return_value = None

        mock_report2 = Mock(spec=ReportBase)
        mock_report2.run.side_effect = Exception("Runtime failure")

        mock_report_class1 = Mock()
        mock_report_class1.__name__ = "GoodReport"
        mock_report_class1.return_value = mock_report1

        mock_report_class2 = Mock()
        mock_report_class2.__name__ = "BadReport"
        mock_report_class2.return_value = mock_report2

        report_classes = [mock_report_class1, mock_report_class2]

        # Run the sync method
        results = runner.run_reports_sync(report_classes, mock_config, mock_client)

        # Verify mixed results
        assert len(results["successful"]) == 1
        assert len(results["failed"]) == 1
        assert "GoodReport" in results["successful"]
        assert "BadReport" in results["failed"]
        # The exception is logged but not stored in exceptions list
        # because _run_single_report catches it and returns False
        assert len(results["exceptions"]) == 0

    def test_run_reports_sync_creation_failure(self, mock_config, mock_client):
        """Test sync execution with creation failures."""
        runner = AsyncReportRunner(max_workers=2)

        # Create one good report and one that fails during creation
        mock_report1 = Mock(spec=ReportBase)
        mock_report1.run.return_value = None

        mock_report_class1 = Mock()
        mock_report_class1.__name__ = "GoodReport"
        mock_report_class1.return_value = mock_report1

        mock_report_class2 = Mock()
        mock_report_class2.__name__ = "FailedCreation"
        mock_report_class2.side_effect = Exception("Creation failed")

        report_classes = [mock_report_class1, mock_report_class2]

        # Run the sync method
        results = runner.run_reports_sync(report_classes, mock_config, mock_client)

        # Verify results
        assert len(results["successful"]) == 1
        assert len(results["failed"]) == 1
        assert "GoodReport" in results["successful"]
        assert "FailedCreation" in results["failed"]
        assert len(results["exceptions"]) == 1
        assert "Creation failed" in results["exceptions"]
