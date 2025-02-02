from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from .odata_client import ODataClient

if TYPE_CHECKING:
    from .config import Config


class ReportBase(ABC):
    def __init__(
        self,
        client: "ODataClient",
        start_date: datetime,
        end_date: datetime,
        output_folder: str,
        debug: bool,
        config: "Config",
    ) -> None:
        self._client = client
        self._start_date = start_date
        self._end_date = config.end_date
        self._output_folder = output_folder
        self._debug = config.debug

        if self._debug:
            print(f"Running report {self.__class__.__name__}")

    @property
    @abstractmethod
    def file_name_prefix(self) -> str: ...

    @abstractmethod
    def _run(self) -> None: ...

    def run(self) -> None:
        self._run()

    def file_name(self, name_part: str) -> str:
        return (
            f"{self._output_folder}{self.file_name_prefix}{name_part}_"
            f"{self._file_name_suffix()}.csv"
        )

    def _file_name_suffix(self, input_date: datetime | None = None) -> str:
        if input_date is None:
            date_to_output = self._start_date
        else:
            date_to_output = input_date
        return date_to_output.strftime("%Y-%m-%d")
