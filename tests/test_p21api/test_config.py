from datetime import date, datetime

import pytest
from p21api.config import Config
from tests.config_test import ConfigTest


# Test for Config output_folder normalization
def test_output_folder_normalization():
    # Test with a folder path with a backslash on Windows
    config = ConfigTest(output_folder="C:\\path\\to\\folder\\")
    assert config.output_folder == "C:\\path\\to\\folder\\"

    # Test with folder path with a double trailing slashes
    config = ConfigTest(output_folder="./output//")
    assert config.output_folder == "output\\"


# Test for start_date parsing
@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("2025-01-01", datetime(2025, 1, 1, 0, 0)),
        (date(2025, 1, 1), datetime(2025, 1, 1, 0, 0)),
        (
            None,
            datetime(datetime.now().year, datetime.now().month, 1),
        ),  # Defaults to the first of the month
    ],
)
def test_parse_start_date(input_value, expected_output):
    config = ConfigTest(start_date=input_value)
    assert config.start_date == expected_output


# Test for end_date parsing
def test_parse_end_date():
    # Provide start_date and check if end_date is parsed correctly
    config = ConfigTest(start_date="2029-01-01")
    end_date = config.end_date
    assert end_date == datetime(2029, 2, 1, 0, 0)

    # Test if end_date can be set explicitly
    config = ConfigTest(start_date="2029-01-01", end_date_="2029-01-10")
    assert config.end_date == datetime(2029, 1, 10, 0, 0)


# Test for has_login property
def test_has_login():
    # Test with no username/password
    config = ConfigTest(username=None, password=None)
    assert not config.has_login

    # Test with username and password
    config = ConfigTest(username="test", password="password")
    assert config.has_login


# Test for should_show_gui property
@pytest.mark.parametrize(
    "username, password, show_gui, expected_result",
    [
        (
            None,
            None,
            False,
            True,
        ),  # No login, should show GUI
        (
            "test",
            "password",
            True,
            True,
        ),  # All data and should show, should show GUI
        (
            "test",
            "password",
            False,
            False,
        ),  # All data, shouldn't show GUI
    ],
)
def test_should_show_gui(
    username: str | None,
    password: str | None,
    show_gui: bool,
    expected_result: bool,
) -> None:
    config = ConfigTest(username=username, password=password, show_gui=show_gui)
    assert config.should_show_gui == expected_result


# Test from_gui_input method
def test_from_gui_input():
    # Simulate GUI input data (only including keys that might be input by the GUI)
    gui_data = {"username": "test_user"}

    # Create Config instance from GUI input, expect the other fields to be defaulted
    config = Config.from_gui_input(gui_data)

    # Check if the fields match
    assert config.username == "test_user"
    assert config.password is None  # Defaulted to None
    assert config.output_folder == "output\\"  # Defaulted value


# Test get_report_groups and get_reports_list methods
def test_get_report_groups():
    report_groups = Config.get_report_groups()

    # Check that report groups are correctly returned
    assert "monthly" in report_groups
    assert "inventory" in report_groups
    assert "po" in report_groups
    assert len(report_groups["monthly"]) > 0  # Ensure there are reports under "monthly"


def test_get_reports_list():
    reports_list = Config.get_reports_list()

    # Ensure report groups are correctly returned as keys
    assert "monthly" in reports_list
    assert "inventory" in reports_list
    assert "po" in reports_list
