"""Type stubs for PyQt6 core classes."""

from typing import Any

class QDate:
    @staticmethod
    def currentDate() -> "QDate": ...
    def addDays(self, days: int) -> "QDate": ...
    def toPython(self) -> Any: ...

QDate_currentDate = QDate.currentDate
