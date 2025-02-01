import os
from datetime import date, datetime
from pathlib import Path
from typing import Type

from pydantic import Field, field_validator
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
    base_url: str = Field(default="", validation_alias="BASE_URL")
    username: str | None = Field(default=None, validation_alias="APIUSERNAME")
    password: str | None = Field(default=None, validation_alias="APIPASSWORD")
    output_folder: str = Field(default="./output/", validation_alias="OUTPUT_FOLDER")
    report_groups: list[str] = Field(
        default_factory=lambda: ["monthly"], validation_alias="REPORT_GROUPS"
    )
    debug: bool = Field(default=False, validation_alias="DEBUG")
    show_gui: bool = Field(default=False, validation_alias="SHOW_GUI")
    start_date: datetime | None = Field(default=None, validation_alias="START_DATE")
    end_date: datetime | None = Field(default=None, validation_alias="END_DATE")

    @field_validator("output_folder", mode="before")
    @classmethod
    def normalize_output_folder(cls, value: str) -> str:
        """Ensure output folder path is properly formatted."""
        # Normalize path and ensure exactly one trailing slash
        value = os.path.normpath(value) + os.sep
        Path(value).mkdir(parents=True, exist_ok=True)
        return value

    @field_validator("start_date", mode="before")
    @classmethod
    def parse_start_date(cls, value: str | datetime | date | None) -> datetime:
        """Parse start_date from environment or default to first day of current month."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d")
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return datetime(datetime.now().year, datetime.now().month, 1)

    @field_validator("end_date", mode="before")
    @classmethod
    def parse_end_date(cls, value: str | datetime | date | None, values) -> datetime:
        """Parse end_date or default to the last day of the start_date's month."""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d")
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        start_date = values.data.get("start_date") or datetime.now()
        return cls._date_start_of_next_month(start_date)

    @staticmethod
    def _date_start_of_next_month(input_date: datetime) -> datetime:
        """Return midnight of the first day of the next month."""
        year, month = input_date.year, input_date.month
        if month == 12:
            return datetime(year + 1, 1, 1)
        return datetime(year, month + 1, 1)

    @property
    def has_login(self) -> bool:
        """Check if login credentials are provided."""
        return bool(self.username and self.password)

    @property
    def should_show_gui(self) -> bool:
        """Determine whether the GUI should be shown."""
        for condition in [self.show_gui, not self.has_login, not self.start_date]:
            if condition:
                return True
        return False

    @classmethod
    def from_gui_input(cls, data: dict) -> "Config":
        """Create a Config instance from GUI input data without overriding defaults."""
        return cls.model_construct(**data)

    model_config = {
        "env_prefix": "",  # No prefix for environment variables
        "env_file": ".env",  # Load environment variables from .env file
        "env_file_encoding": "utf-8",
        "extra": "allow",  # Allow extra fields in environment variables
    }

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
