"""Tests for the gui module.

DatePickerDialog subclasses PyQt6's QDialog directly, so patching
gui.gui.QDialog does not stop real Qt widget construction - only patching
gui.gui.DatePickerDialog itself (as show_gui_dialog does) is safe in a
headless environment. Tests that would construct a real DatePickerDialog
are intentionally not included here; they have historically crashed
headless test runs.
"""

from unittest.mock import Mock, patch

import pytest


def test_gui_module_imports():
    """The gui module and its key symbols should be importable."""
    import gui.gui

    assert hasattr(gui.gui, "DatePickerDialog")
    assert hasattr(gui.gui, "show_gui_dialog")


@patch("gui.gui.QApplication")
@patch("gui.gui.DatePickerDialog")
def test_show_gui_dialog_accepted_returns_data(mock_dialog_class, mock_qapp):
    """When the dialog is accepted, show_gui_dialog returns (data, True)."""
    from gui.gui import show_gui_dialog

    mock_dialog = Mock()
    mock_dialog.exec.return_value = 1  # QDialog.DialogCode.Accepted
    mock_dialog.get_data.return_value = {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "output_folder": "output/",
        "report_groups": "monthly",
    }
    mock_dialog_class.return_value = mock_dialog

    data, save_clicked = show_gui_dialog(Mock())

    assert save_clicked is True
    assert data == mock_dialog.get_data.return_value


@patch("gui.gui.QApplication")
@patch("gui.gui.DatePickerDialog")
def test_show_gui_dialog_rejected_returns_none(mock_dialog_class, mock_qapp):
    """When the dialog is rejected/closed, show_gui_dialog returns (None, False)."""
    from gui.gui import show_gui_dialog

    mock_dialog = Mock()
    mock_dialog.exec.return_value = 0  # QDialog.DialogCode.Rejected
    mock_dialog_class.return_value = mock_dialog

    data, save_clicked = show_gui_dialog(Mock())

    assert save_clicked is False
    assert data is None
    mock_dialog.get_data.assert_not_called()


@pytest.mark.skip(reason="Not safely testable headless - see module docstring.")
def test_date_picker_dialog_construction():
    """Known gap: real widget construction/layout (populate_reports, get_data,
    browse_folder) is not covered headlessly."""
