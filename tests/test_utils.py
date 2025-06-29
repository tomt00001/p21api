"""Utility functions and fixtures for testing."""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


def create_temp_directory():
    """Create a temporary directory for test outputs."""
    return tempfile.mkdtemp()


def cleanup_temp_directory(temp_dir):
    """Clean up a temporary directory."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def create_mock_response(status_code=200, json_data=None, text="Success"):
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = status_code
    response.text = text
    if json_data:
        response.json.return_value = json_data
    return response


def create_sample_config_data():
    """Create sample configuration data for testing."""
    return {
        "base_url": "http://example.com",
        "username": "test_user",
        "password": "test_password",
        "output_folder": "test_output/",
        "report_groups": "monthly",
        "debug": False,
        "show_gui": False,
        "start_date": "2024-01-01",
    }


def create_sample_odata_response(data_list):
    """Create a sample OData response format."""
    return {"value": data_list}


def assert_file_exists(file_path):
    """Assert that a file exists."""
    assert os.path.exists(file_path), f"File {file_path} does not exist"


def assert_file_not_exists(file_path):
    """Assert that a file does not exist."""
    assert not os.path.exists(file_path), f"File {file_path} should not exist"


def get_test_data_path():
    """Get the path to test data directory."""
    return Path(__file__).parent / "test_data"


def create_test_csv_data():
    """Create sample CSV data for testing."""
    return [
        ["id", "name", "value", "date"],
        ["1", "Item 1", "100.50", "2024-01-01"],
        ["2", "Item 2", "200.75", "2024-01-02"],
        ["3", "Item 3", "300.25", "2024-01-03"],
    ]


class MockDatetime:
    """Mock datetime class for testing."""

    def __init__(self, fixed_date=None):
        self.fixed_date = fixed_date or datetime(2024, 1, 15, 10, 30, 45)

    def now(self):
        return self.fixed_date

    def today(self):
        return self.fixed_date.date()


def patch_datetime_now(fixed_date=None):
    """Context manager to patch datetime.now() for testing."""
    mock_dt = MockDatetime(fixed_date)
    return patch("datetime.datetime", mock_dt)


def is_gui_available():
    """Check if GUI dependencies are available."""
    try:
        import PyQt6  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture
def skip_if_no_gui():
    """Pytest fixture to skip tests if GUI dependencies are not available."""
    if not is_gui_available():
        pytest.skip("GUI dependencies (PyQt6) not available")


# Decorator for conditional skipping of GUI tests
skip_without_gui = pytest.mark.skipif(
    not is_gui_available(), reason="GUI dependencies (PyQt6) not available"
)


def skip_if_no_network():
    """Skip test if network is not available."""
    import socket

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return False
    except OSError:
        return True


# Test data generators
def generate_invoice_data(count=10):
    """Generate sample invoice data for testing."""
    invoices = []
    for i in range(count):
        invoices.append(
            {
                "bill2_name": f"Customer {i + 1}",
                "freight": round(10.0 + i, 2),
                "invoice_date": f"2024-01-{(i % 28) + 1:02d}",
                "invoice_no": f"INV{i + 1:04d}",
                "other_charge_amount": round(5.0 + (i * 0.5), 2),
                "period": 1,
                "tax_amount": round(15.0 + (i * 2), 2),
                "total_amount": round(250.0 + (i * 50), 2),
                "year_for_period": 2024,
                "salesrep_id": f"REP{(i % 5) + 1:03d}",
            }
        )
    return invoices


def generate_inventory_data(count=10):
    """Generate sample inventory data for testing."""
    inventory = []
    for i in range(count):
        inventory.append(
            {
                "item_id": f"ITEM{i + 1:04d}",
                "item_desc": f"Test Item {i + 1}",
                "qty_on_hand": 100 + (i * 10),
                "unit_cost": round(25.50 + (i * 5), 2),
                "extended_cost": round((100 + (i * 10)) * (25.50 + (i * 5)), 2),
                "location_id": f"LOC{(i % 3) + 1:03d}",
            }
        )
    return inventory


def generate_po_data(count=10):
    """Generate sample purchase order data for testing."""
    pos = []
    for i in range(count):
        pos.append(
            {
                "po_no": f"PO{i + 1:04d}",
                "vendor_name": f"Vendor {i + 1}",
                "po_date": f"2024-01-{(i % 28) + 1:02d}",
                "total_amount": round(1000.0 + (i * 100), 2),
                "status": "Open" if i % 2 == 0 else "Closed",
                "buyer_id": f"BUYER{(i % 3) + 1:02d}",
            }
        )
    return pos


# Test assertion helpers
def assert_config_valid(config):
    """Assert that a config object is valid."""
    assert config.base_url is not None
    assert config.username is not None
    assert config.password is not None
    assert config.start_date is not None
    assert config.output_folder is not None


def assert_dates_equal(date1, date2, tolerance_seconds=1):
    """Assert that two dates are equal within a tolerance."""
    if isinstance(date1, str):
        date1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
    if isinstance(date2, str):
        date2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))

    diff = abs((date1 - date2).total_seconds())
    assert diff <= tolerance_seconds, f"Dates differ by {diff} seconds"


def assert_csv_structure(csv_data, expected_columns):
    """Assert that CSV data has the expected structure."""
    assert len(csv_data) > 0, "CSV data is empty"

    if isinstance(csv_data[0], dict):
        # Data is list of dictionaries
        for col in expected_columns:
            assert col in csv_data[0], f"Column {col} not found in CSV data"
    else:
        # Data is list of lists (header + rows)
        header = csv_data[0]
        for col in expected_columns:
            assert col in header, f"Column {col} not found in CSV header"


# Performance testing helpers
def measure_execution_time(func, *args, **kwargs):
    """Measure execution time of a function."""
    import time

    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    execution_time = end_time - start_time
    return result, execution_time


def assert_execution_time_under(func, max_seconds, *args, **kwargs):
    """Assert that function execution time is under the specified limit."""
    result, execution_time = measure_execution_time(func, *args, **kwargs)
    assert execution_time < max_seconds, (
        f"Execution took {execution_time:.2f}s, expected under {max_seconds}s"
    )
    return result
