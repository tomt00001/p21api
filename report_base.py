from abc import ABC, abstractmethod
from datetime import datetime

from p21_odata_client import P21ODataClient


class Report_Base(ABC):
    def __init__(
        self,
        client: "P21ODataClient",
        start_date: datetime,
        debug: bool = False,
    ) -> None:
        self._client = client
        self._start_date = start_date
        self.output_path = "output/"
        self._debug = debug

    @property
    @abstractmethod
    def file_name_prefix(self) -> str:
        pass

    def file_name(self, name_part: str) -> str:
        return (
            f"{self.output_path}{self.file_name_prefix}{name_part}_"
            f"{self._file_name_suffix()}.csv"
        )

    def _file_name_suffix(self, input_date: datetime | None = None) -> str:
        if input_date is None:
            date_to_output = self._start_date
        else:
            date_to_output = input_date
        return date_to_output.strftime("%Y-%m-%d")
