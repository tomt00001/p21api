import calendar
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Type

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings

from .report_base import ReportBase
from .report_daily_sales import ReportDailySales
from .report_inventory import ReportInventory
from .report_jarp import ReportJarp
from .report_kennametal_pos import ReportKennametalPos
from .report_monthly_consolidation import ReportMonthlyConsolidation
from .report_monthly_invoices import ReportMonthlyInvoices
from .report_open_orders import ReportOpenOrders
from .report_open_po import ReportOpenPO


class Config(BaseSettings):
    base_url: str = Field(default="https://christensenmachinery.epicordistribution.com")
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    output_folder: str = Field(default="output\\")
    report_groups: list[str] = Field(default_factory=lambda: ["monthly"])
    debug: bool = Field(default=False)
    show_gui: bool = Field(default=False)
    start_date: datetime | None = Field(default=None)
    end_date_: datetime | None = Field(default=None)

    @field_validator("output_folder", mode="before")
    @classmethod
    def normalize_output_folder(cls, value: str) -> str:
        """Ensure output folder path is properly formatted."""
        value = os.path.normpath(value) + os.sep
        Path(value).mkdir(parents=True, exist_ok=True)
        return value

    @field_validator("start_date", mode="before")
    @classmethod
    def parse_start_date(cls, value: str | datetime | date | None) -> datetime:
        """
        Parse start_date from environment or default to first day of current month.
        """
        start_date = None
        if isinstance(value, str):
            start_date = datetime.strptime(value, "%Y-%m-%d")
        if isinstance(value, date):
            start_date = value
        if not start_date:
            start_date = date(datetime.now().year, datetime.now().month, 1)
        return datetime.combine(start_date, datetime.min.time())

    @field_validator("end_date", mode="before")
    @classmethod
    def parse_end_date(
        cls, value: str | datetime | date | None, values
    ) -> datetime | None:
        """Parse end_date or default to the last day of the start_date's month."""
        end_date = None
        if isinstance(value, str):
            end_date = datetime.strptime(value, "%Y-%m-%d")
        if isinstance(value, date):
            end_date = value
        if end_date:
            datetime.combine(end_date, datetime.max.time())

    @model_validator(mode="before")
    def set_end_date_if_not_set(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start_date = cls.parse_start_date(values.get("start_date"))
        if not values.get("end_date") and start_date:
            values["end_date"] = cls._date_start_of_next_month(start_date)
        return values

    @computed_field
    @property
    def end_date(self) -> datetime:
        if not self.end_date_ and self.start_date:
            # Get the last day of the month
            last_day_of_month = calendar.monthrange(
                self.start_date.year, self.start_date.month
            )[1]
            return datetime.combine(
                self.start_date.replace(day=last_day_of_month), datetime.max.time()
            )
        if not self.end_date_:
            raise ValueError("End date is required")
        return self.end_date_

    @staticmethod
    def _date_start_of_next_month(input_date: datetime) -> datetime:
        """Return midnight of the first day of the next month."""
        year, month = input_date.year, input_date.month
        if month == 12:
            return datetime(year + 1, 1, 1)
        return datetime(year, month + 1, 1)

    model_config = {
        "env_prefix": "",  # No prefix for environment variables
        "env_file": "env",  # Load environment variables from .env file
        "env_file_encoding": "utf-8",
        "extra": "allow",  # Allow extra fields in environment variables
        "case_sensitive": True,
    }

    @property
    def has_login(self) -> bool:
        """Check if login credentials are provided."""
        return bool(self.username and self.password)

    @property
    def should_show_gui(self) -> bool:
        for condition in [self.show_gui, not self.has_login]:
            if condition:
                return True
        return False

    @staticmethod
    def get_report_groups() -> dict[str, list[Type[ReportBase]]]:
        return {
            "monthly": [
                ReportKennametalPos,
                ReportDailySales,
                ReportOpenOrders,
                ReportMonthlyInvoices,
                ReportMonthlyConsolidation,
                ReportJarp,
            ],
            "inventory": [
                ReportInventory,
            ],
            "po": [
                ReportOpenPO,
            ],
        }

    @staticmethod
    def get_reports_list() -> list[str]:
        return list(Config.get_report_groups().keys())
