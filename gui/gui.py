import sys
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QApplication,
    QDateEdit,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from p21api.config import Config


class DatePickerDialog(QDialog):
    def __init__(self, config: "Config", parent=None) -> None:
        super().__init__(parent)

        # Set dialog title and size
        self.setWindowTitle("P21 Data Export Configuration")
        self.setGeometry(100, 100, 300, 300)

        # Create the layout
        layout = QVBoxLayout()

        # Start Date Picker
        layout.addWidget(QLabel("Start Date"))
        self.start_date_picker = QDateEdit()
        self.start_date_picker.setCalendarPopup(True)
        # Set default start date
        if config.start_date:
            self.start_date_picker.setDate(
                QDate(
                    config.start_date.year,
                    config.start_date.month,
                    config.start_date.day,
                )  # noqa
            )
        else:
            self.start_date_picker.setDate(
                QDate.currentDate()
            )  # Set current date as default
        layout.addWidget(self.start_date_picker)

        # End Date Picker
        layout.addWidget(QLabel("End Date"))
        self.end_date_picker = QDateEdit()
        self.end_date_picker.setCalendarPopup(True)
        # Set default end date
        if config.end_date:
            self.end_date_picker.setDate(
                QDate(config.end_date.year, config.end_date.month, config.end_date.day)
            )
        else:
            self.end_date_picker.setDate(
                QDate.currentDate()
            )  # Set current date as default
        layout.addWidget(self.end_date_picker)

        # Username
        layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        self.username_edit.setText(config.username)  # Set default username
        layout.addWidget(self.username_edit)

        # Password
        layout.addWidget(QLabel("Password"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )  # Mask the password input
        self.password_edit.setText(config.password)  # Set default password
        layout.addWidget(self.password_edit)

        # Output Folder Picker
        layout.addWidget(QLabel("Output Folder"))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setText(config.output_folder)
        layout.addWidget(self.output_folder_edit)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.browse_button)

        # Collapsible GroupBox for Report Selection
        report_group = QGroupBox("Select Report Groups")
        report_group.setCheckable(True)  # Makes it collapsible
        report_group.setChecked(False)  # Start collapsed

        report_layout = QVBoxLayout()
        self.reports_list = QListWidget()
        self.reports_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.reports_list.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Populate the reports list from config
        self.populate_reports(config.get_reports_list(), config.report_groups)

        report_layout.addWidget(self.reports_list)
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)

        # Toggle visibility when the group box is expanded/collapsed
        report_group.toggled.connect(self.reports_list.setVisible)

        # Ensure the report list starts hidden
        self.reports_list.setVisible(False)

        # Buttons (OK and Cancel)
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Set the dialog layout
        self.setLayout(layout)

        # Connect buttons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.output_folder_edit.setText(folder)

    def get_data(self):
        data = {}
        # Get the date values
        start_date = self.start_date_picker.date().toPyDate()
        if start_date:
            data["start_date"] = start_date
        end_date = self.end_date_picker.date().toPyDate()
        if end_date:
            data["end_date"] = end_date

        # Get the username and password
        username = self.username_edit.text()
        if username:
            data["username"] = username
        password = self.password_edit.text()
        if password:
            data["password"] = password

        # Get the output folder
        output_folder = self.output_folder_edit.text()
        if output_folder:
            data["output_folder"] = f"{output_folder.replace("\\", "/").rstrip("/")}//"

        reports = self.get_selected_reports()
        if reports:
            data["reports"] = reports

        return data

    def populate_reports(self, reports: list[str], default_reports: list[str]) -> None:
        """Populates the QListWidget with reports and sets default selections."""
        for report in reports:
            item = QListWidgetItem(report)
            self.reports_list.addItem(item)
            # Set default selection if report is in the default list
            if report in default_reports:
                item.setSelected(True)

    def get_selected_reports(self) -> list[str]:
        """Returns a list of selected reports."""
        return [item.text() for item in self.reports_list.selectedItems()]


def show_gui_dialog(
    config: "Config",
) -> tuple[dict[str, datetime | str | None] | None, bool]:
    _ = QApplication(sys.argv)  # Initialize the QApplication

    dialog = DatePickerDialog(config=config)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # Get data if OK is clicked
        data = dialog.get_data()
        return data, True
    else:
        return None, False
