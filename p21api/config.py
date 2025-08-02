import calendar
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Type

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings

from .report_base import ReportBase
from .report_daily_sales import ReportDailySales
from .report_grind_shop_open_orders import ReportGrindShopOpenOrders
from .report_jarp import ReportJarp
from .report_kennametal_pos import ReportKennametalPos
from .report_monthly_consolidation import ReportMonthlyConsolidation
from .report_monthly_invoices import ReportMonthlyInvoices
from .report_open_orders import ReportOpenOrders


class Config(BaseSettings):
    base_url: str = Field(default="https://christensenmachinery.epicordistribution.com")
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    output_folder: str = Field(default="output\\")
    report_groups: str = Field(default="monthly")
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
        if isinstance(value, str):
            start_date_obj = datetime.strptime(value, "%Y-%m-%d").date()
        elif isinstance(value, datetime):
            start_date_obj = value.date()
        elif isinstance(value, date):
            start_date_obj = value
        else:
            start_date_obj = date(datetime.now().year, datetime.now().month, 1)
        return datetime.combine(start_date_obj, datetime.min.time())

    @field_validator("end_date_", mode="before")
    @classmethod
    def parse_end_date(cls, value: str | datetime | date | None) -> datetime | None:
        """Parse end_date or default to the last day of the start_date's month."""
        if value is None:
            return None

        if isinstance(value, str):
            end_date_obj = datetime.strptime(value, "%Y-%m-%d").date()
            return datetime.combine(end_date_obj, datetime.max.time())
        elif isinstance(value, datetime):
            # If it's already a datetime, preserve the time component
            return value
        else:
            # Must be a date object at this point
            return datetime.combine(value, datetime.max.time())

    @model_validator(mode="before")
    @classmethod
    def set_end_date_if_not_set(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start_date = cls.parse_start_date(values.get("start_date"))
        if not values.get("end_date_") and start_date:
            # Set to last day of the start_date's month
            last_day_of_month = calendar.monthrange(start_date.year, start_date.month)[
                1
            ]
            values["end_date_"] = datetime.combine(
                start_date.replace(day=last_day_of_month), datetime.max.time()
            )
        return values

    @computed_field
    def end_date_computed(self) -> datetime:
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

    @property
    def end_date(self) -> datetime:
        """Provide backward compatibility access to end_date."""
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

    @classmethod
    def _date_start_of_next_month(cls, input_date: datetime) -> datetime:
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

    def get_reports(self) -> list[Type[ReportBase]]:
        report_groups = self.report_groups.split(",")
        return [
            report
            for report_group in [
                self.get_config_report_groups().get(x) for x in report_groups
            ]
            for report in report_group or []
        ]

    @staticmethod
    def get_config_report_groups() -> dict[str, list[Type[ReportBase]]]:
        return {
            "monthly": [
                ReportKennametalPos,
                ReportDailySales,
                ReportOpenOrders,
                ReportMonthlyInvoices,
                ReportMonthlyConsolidation,
                ReportJarp,
                ReportGrindShopOpenOrders,
            ],
            "inventory": [],
        }

    @staticmethod
    def get_config_reports_list() -> list[str]:
        return list(Config.get_config_report_groups().keys())
