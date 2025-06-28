"""
Asynchronous report runner for improved performance.

This module provides async capabilities for running multiple reports concurrently,
improving overall application performance.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from .config import Config
from .odata_client import ODataClient
from .report_base import ReportBase

logger = logging.getLogger(__name__)


class AsyncReportRunner:
    """Asynchronous report execution engine."""

    def __init__(self, max_workers: int = 5):
        """
        Initialize the async report runner.

        Args:
            max_workers: Maximum number of concurrent report executions
        """
        self.max_workers = max_workers

    async def run_reports_async(
        self, report_classes: List[Any], config: Config, client: ODataClient
    ) -> Dict[str, Any]:
        """
        Run multiple reports asynchronously.

        Args:
            report_classes: List of report classes to execute
            config: Application configuration
            client: OData client instance

        Returns:
            Dict containing results and any exceptions
        """
        # Use the synchronous implementation for now since we're using threads
        return self.run_reports_sync(report_classes, config, client)

    def run_reports_sync(
        self, report_classes: List[Any], config: Config, client: ODataClient
    ) -> Dict[str, Any]:
        """
        Run multiple reports synchronously with concurrent execution.

        Args:
            report_classes: List of report classes to execute
            config: Application configuration
            client: OData client instance

        Returns:
            Dict containing results and any exceptions
        """
        results: Dict[str, Any] = {"successful": [], "failed": [], "exceptions": []}

        # Create report instances
        reports = []
        for report_class in report_classes:
            try:
                report = report_class(
                    client=client,
                    start_date=config.start_date,  # type: ignore[arg-type]
                    end_date=config.end_date,
                    output_folder=config.output_folder,
                    debug=config.debug,
                    config=config,
                )
                reports.append((report_class.__name__, report))
            except Exception as e:
                logger.error(f"Failed to create {report_class.__name__}: {e}")
                results["failed"].append(report_class.__name__)
                results["exceptions"].append(str(e))

        # Run reports concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all report tasks
            future_to_report = {
                executor.submit(self._run_single_report, name, report): name
                for name, report in reports
            }

            # Collect results as they complete
            for future in as_completed(future_to_report):
                report_name = future_to_report[future]
                try:
                    success = future.result()
                    if success:
                        results["successful"].append(report_name)
                        logger.info(f"Successfully completed {report_name}")
                    else:
                        results["failed"].append(report_name)
                except Exception as e:
                    logger.error(f"Exception in {report_name}: {e}")
                    results["failed"].append(report_name)
                    results["exceptions"].append(f"{report_name}: {str(e)}")

        return results

    def _run_single_report(self, name: str, report: ReportBase) -> bool:
        """
        Run a single report (to be executed in thread pool).

        Args:
            name: Report name for logging
            report: Report instance to execute

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Starting {name}")
            report.run()
            logger.info(f"Completed {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to run {name}: {e}")
            return False


class ReportProgress:
    """Track progress of report execution."""

    def __init__(self, total_reports: int):
        self.total_reports = total_reports
        self.completed_reports = 0
        self.failed_reports = 0
        self.current_report: Optional[str] = None

    def start_report(self, report_name: str) -> None:
        """Mark a report as started."""
        self.current_report = report_name
        logger.info(f"Starting report: {report_name}")

    def complete_report(self, report_name: str, success: bool = True) -> None:
        """Mark a report as completed."""
        self.completed_reports += 1
        if not success:
            self.failed_reports += 1

        self.current_report = None
        status = "completed successfully" if success else "failed"
        logger.info(
            f"Report {report_name} {status} "
            f"({self.completed_reports}/{self.total_reports})"
        )

    @property
    def progress_percentage(self) -> float:
        """Get current progress as percentage."""
        if self.total_reports == 0:
            return 100.0
        return (self.completed_reports / self.total_reports) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if all reports are complete."""
        return self.completed_reports >= self.total_reports

    def __str__(self) -> str:
        """String representation of progress."""
        return (
            f"Progress: {self.completed_reports}/{self.total_reports} "
            f"({self.progress_percentage:.1f}%) - "
            f"Failed: {self.failed_reports}"
        )
