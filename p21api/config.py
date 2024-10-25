import calendar
from dataclasses import dataclass
from datetime import date, datetime
from os import getenv
from pathlib import Path

from .reports import get_reports_list


@dataclass
class Config:
    def __init__(
        self,
        output_folder: str | None = None,
        report_groups: str | None = None,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        debug: bool | str | None = False,
        show_gui: bool | str | None = None,
    ) -> None:
        if not (base_url := getenv("BASE_URL")):
            raise ValueError(
                "Base URL in environment variables is missing. Exiting.",
            )
        self.base_url = base_url

        self.set_output_folder(output_folder)
        self.set_report_groups(report_groups)
        self.set_username(username)
        self.set_password(password)
        self.set_start_date(start_date)
        self.set_end_date(end_date)

        self.show_gui = False
        if show_gui and isinstance(show_gui, bool):
            self.show_gui = show_gui
        if not show_gui:
            show_gui = getenv("SHOW_GUI")
        if show_gui and isinstance(show_gui, str):
            self.show_gui = show_gui == "True"
        elif not show_gui and not self.start_date:
            self.show_gui = True

        self.debug = False
        if debug and isinstance(debug, bool):
            self.debug = debug
        if not debug:
            debug = getenv("DEBUG")
        elif debug and isinstance(debug, str):
            if debug and debug == "True":
                self.debug = True

    base_url: str
    username: str | None
    password: str | None
    start_date: datetime
    end_date: datetime
    output_folder: str
    show_gui: bool = True
    debug: bool = False

    def set_username(self, username: str | None) -> None:
        if username is not None:
            self.username = username
        else:
            self.username = getenv("APIUSERNAME")

    def set_password(self, password: str | None) -> None:
        if password is not None:
            self.password = password
        else:
            self.password = getenv("APIPASSWORD")

    def set_start_date(self, start_date: str | datetime | None) -> None:
        if not start_date:
            start_date = getenv("START_DATE")
        if start_date and isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        elif start_date and isinstance(start_date, datetime):
            self.start_date = start_date
        elif start_date and isinstance(start_date, date):
            self.start_date = datetime.combine(start_date, datetime.min.time())
        else:
            self.start_date = self._date_start_of_month(datetime.now())

    def set_end_date(self, end_date: str | datetime | None) -> None:
        if not end_date:
            end_date = getenv("END_DATE")
        if end_date and isinstance(end_date, str):
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        elif end_date and isinstance(end_date, datetime):
            self.end_date = end_date
        elif end_date and isinstance(end_date, date):
            self.end_date = datetime.combine(end_date, datetime.min.time())
        elif not end_date and self.start_date:
            self.end_date = self._date_end_of_month(self.start_date)

    def set_output_folder(self, output_folder: str | None = None) -> None:
        if not output_folder:
            output_folder = getenv("OUTPUT_FOLDER")
        if output_folder and isinstance(output_folder, str):
            self.output_folder = output_folder
        elif not output_folder:
            self.output_folder = "./output/"
        self.output_folder = f"{self.output_folder.replace("\\", "/").rstrip("/")}//"
        Path(self.output_folder).mkdir(parents=True, exist_ok=True)

    def set_report_groups(self, report_groups: str | None) -> None:
        if not report_groups:
            report_groups = getenv("REPORT_GROUPS")
        if report_groups and isinstance(report_groups, str):
            self.report_groups = [item.strip() for item in report_groups.split(",")]
        elif not report_groups:
            self.report_groups = ["monthly"]

    def from_gui_input(
        self,
        input_data: dict[str, str | datetime | None],
    ) -> None:
        if start_date := input_data.get("start_date"):
            self.set_start_date(start_date)
        if end_date := input_data.get("end_date"):
            self.set_end_date(end_date)

        username = input_data.get("username")
        if username and isinstance(username, str):
            self.set_username(username)
        password = input_data.get("password")
        if password and isinstance(password, str):
            self.set_password(password)

        output_folder = input_data.get("output_folder")
        if output_folder and isinstance(output_folder, str):
            self.set_output_folder(output_folder)

        reports = input_data.get("reports")
        if reports and isinstance(reports, list):
            self.set_report_groups(",".join(reports))

    def _date_start_of_month(self, input_date: datetime) -> datetime:
        return datetime(input_date.year, input_date.month, 1)

    def _date_end_of_month(self, input_date: datetime) -> datetime:
        last_day_of_month = calendar.monthrange(
            input_date.year,
            input_date.month,
        )[1]
        return input_date.replace(day=last_day_of_month)

    @property
    def has_login(self) -> bool:
        return self.username is not None and self.password is not None

    @property
    def should_show_gui(self) -> bool:
        if self.show_gui:
            return True
        return not self.has_login or not self.start_date

    @property
    def reports(self) -> list[str]:
        return get_reports_list()
