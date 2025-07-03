"""Integration tests for multiple reports."""

from datetime import datetime


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
