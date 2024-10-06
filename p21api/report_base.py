from abc import ABC, abstractmethod
from datetime import datetime

from .config import Config
from .odata_client import ODataClient


class ReportBase(ABC):
    def __init__(self, client: "ODataClient", config: "Config") -> None:
        self._client = client
        self.config = config
        self._start_date = config.start_date
        self._debug = config.debug

    @property
    @abstractmethod
    def file_name_prefix(self) -> str:
        pass

    def file_name(self, name_part: str) -> str:
        return (
            f"{self.config.output_folder}{self.file_name_prefix}{name_part}_"
            f"{self._file_name_suffix()}.csv"
        )

    def _file_name_suffix(self, input_date: datetime | None = None) -> str:
        if input_date is None:
            date_to_output = self._start_date
        else:
            date_to_output = input_date
        return date_to_output.strftime("%Y-%m-%d")

    @abstractmethod
    def run(self) -> None:
        pass
