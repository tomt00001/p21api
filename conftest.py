"""Pytest configuration and shared fixtures."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from p21api.odata_client import ODataClient
from tests.test_config_legacy import ConfigTest


@pytest.fixture
def mock_config():
    """Fixture providing a test configuration."""
    return ConfigTest(
        base_url="http://example.com",
        username="test_user",
        password="test_password",  # nosec B106 # Test fixture, not real password
        output_folder="test_output/",
        report_groups="monthly",
        debug=True,
        show_gui=False,
        start_date=datetime(2024, 1, 1),
        end_date_=datetime(2024, 1, 31),
    )


@pytest.fixture
def mock_odata_client():
    """Fixture providing a mocked OData client."""
    client = Mock(spec=ODataClient)
    client.username = "test_user"
    client.password = "test_password"  # nosec B105 # Test fixture, not real password
    client.base_url = "http://example.com"
    client.headers = {"Authorization": "Bearer test_token"}
    return client


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing reports."""
    return [
        {
            "bill2_name": "Test Customer 1",
            "freight": 10.50,
            "invoice_date": "2024-01-15",
            "invoice_no": "INV001",
            "other_charge_amount": 5.25,
            "period": 1,
            "tax_amount": 15.75,
            "total_amount": 250.00,
            "year_for_period": 2024,
            "salesrep_id": "REP001",
        },
        {
            "bill2_name": "Test Customer 2",
            "freight": 20.00,
            "invoice_date": "2024-01-20",
            "invoice_no": "INV002",
            "other_charge_amount": 0.00,
            "period": 1,
            "tax_amount": 25.50,
            "total_amount": 500.00,
            "year_for_period": 2024,
            "salesrep_id": "REP002",
        },
    ]


@pytest.fixture
def sample_inventory_data():
    """Sample inventory data for testing."""
    return [
        {
            "item_id": "ITEM001",
            "item_desc": "Test Item 1",
            "qty_on_hand": 100,
            "unit_cost": 25.50,
            "extended_cost": 2550.00,
            "location_id": "LOC001",
        },
        {
            "item_id": "ITEM002",
            "item_desc": "Test Item 2",
            "qty_on_hand": 50,
            "unit_cost": 45.75,
            "extended_cost": 2287.50,
            "location_id": "LOC002",
        },
    ]


@pytest.fixture
def mock_requests_response():
    """Mock requests response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"AccessToken": "test_token_value"}
    response.text = "Success"
    return response


@pytest.fixture
def mock_requests_auth_failure():
    """Mock failed authentication response."""
    response = Mock()
    response.status_code = 401
    response.text = "Unauthorized"
    return response


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return str(output_dir) + "/"


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    # Cleanup code can be added here if needed
    pass


@pytest.fixture
def mock_date_now():
    """Mock datetime.now() for consistent testing."""
    with patch("p21api.config.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2024, 6, 15, 10, 30, 45)
        mock_dt.combine = datetime.combine
        mock_dt.strptime = datetime.strptime
        mock_dt.min = datetime.min
        mock_dt.max = datetime.max
        yield mock_dt
