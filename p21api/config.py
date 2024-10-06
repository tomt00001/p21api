import calendar
from dataclasses import dataclass
from datetime import datetime
from os import getenv


@dataclass
class Config:
    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        start_date: str | datetime | None = None,
        end_date: str | datetime | None = None,
        debug: bool | str | None = False,
        show_gui: bool = True,
    ) -> None:
        if not (base_url := getenv("BASE_URL")):
            raise ValueError(
                "Base URL in environment variables is missing. Exiting.",
            )
        self.base_url = base_url

        self.set_username(username)
        self.set_password(password)
        self.set_start_date(start_date)
        self.set_end_date(end_date)

        if show_gui and isinstance(show_gui, str):
            self.show_gui = show_gui == "True"
        elif show_gui and isinstance(show_gui, bool):
            self.show_gui = show_gui
        elif not show_gui and not self.start_date:
            self.show_gui = True
        else:
            self.show_gui = False

        if debug:
            self.debug = True
        else:
            self.debug = (getenv("DEBUG") and getenv("DEBUG") == "True") or False

    base_url: str
    username: str | None
    password: str | None
    start_date: datetime
    end_date: datetime
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
        if isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        elif isinstance(start_date, datetime):
            self.start_date = start_date
        else:
            return None

    def set_end_date(self, end_date: str | datetime | None) -> None:
        if end_date and isinstance(end_date, str):
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        elif end_date and isinstance(end_date, datetime):
            self.end_date = end_date
        elif not end_date and self.start_date:
            self.end_date = self._date_end_of_month(self.start_date)
        if not self.end_date:
            return None

    def from_gui_input(self, input_data: dict[str, str | datetime | None]) -> None:
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

    def _date_start_of_month(self, input_date: datetime) -> datetime:
        return datetime(input_date.year, input_date.month, 1)

    def _date_end_of_month(self, input_date: datetime) -> datetime:
        last_day_of_month = calendar.monthrange(input_date.year, input_date.month)[1]
        return input_date.replace(day=last_day_of_month)

    @property
    def has_login(self) -> bool:
        return self.username is not None and self.password is not None

    @property
    def should_show_gui(self) -> bool:
        return self.show_gui or not self.has_login or not self.start_date

    @property
    def gui_defaults(self) -> dict:
        data = {}
        if self.start_date:
            data["start_date"] = self.start_date
        if self.end_date:
            data["end_date"] = self.end_date
        if self.username:
            data["username"] = self.username
        if self.password:
            data["password"] = self.password
        return data
