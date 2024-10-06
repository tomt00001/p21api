import sys
from datetime import datetime

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QApplication,
    QDateEdit,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from p21api.config import Config


class DatePickerDialog(QDialog):
    def __init__(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        username: str | None = "",
        password: str | None = "",
        output_folder: str | None = "",
        parent=None,
    ) -> None:
        super().__init__(parent)

        # Set dialog title and size
        self.setWindowTitle("P21 Date Export Configuration")
        self.setGeometry(100, 100, 300, 200)

        # Create the layout
        layout = QVBoxLayout()

        # Start Date Picker
        layout.addWidget(QLabel("Start Date"))
        self.start_date_picker = QDateEdit()
        self.start_date_picker.setCalendarPopup(True)
        # Set default start date
        if start_date:
            self.start_date_picker.setDate(
                QDate(start_date.year, start_date.month, start_date.day)
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
        if end_date:
            self.end_date_picker.setDate(
                QDate(end_date.year, end_date.month, end_date.day)
            )
        else:
            self.end_date_picker.setDate(
                QDate.currentDate()
            )  # Set current date as default
        layout.addWidget(self.end_date_picker)

        # Username
        layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        self.username_edit.setText(username)  # Set default username
        layout.addWidget(self.username_edit)

        # Password
        layout.addWidget(QLabel("Password"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(
            QLineEdit.EchoMode.Password
        )  # Mask the password input
        self.password_edit.setText(password)  # Set default password
        layout.addWidget(self.password_edit)

        # Output Folder Picker
        layout.addWidget(QLabel("Output Folder"))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setText(output_folder)
        layout.addWidget(self.output_folder_edit)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.browse_button)

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
            data["output_folder"] = f"{output_folder}/"

        return data


def show_date_picker_dialog(
    config: "Config",
) -> tuple[dict[str, datetime | str | None] | None, bool]:
    _ = QApplication(sys.argv)  # Initialize the QApplication

    dialog = DatePickerDialog(**config.gui_defaults)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        # Get data if OK is clicked
        data = dialog.get_data()
        return data, True
    else:
        return None, False
