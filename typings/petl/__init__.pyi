"""
Basic type stubs for petl library.
This provides minimal type hints to avoid missing type stub warnings.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Table types
class TableView:
    def __iter__(self) -> Any: ...

class DictsView(TableView):
    def __iter__(self) -> Any: ...

class DictsGeneratorView(TableView):
    def __iter__(self) -> Any: ...

class JoinView(TableView):
    def __iter__(self) -> Any: ...

class CutView(TableView):
    def __iter__(self) -> Any: ...

class AddFieldView(TableView):
    def __iter__(self) -> Any: ...

class SortView(TableView):
    def __iter__(self) -> Any: ...

# Main functions
def fromdicts(dicts: Optional[List[Dict[str, Any]]]) -> DictsView: ...
def join(
    left: TableView,
    right: TableView,
    key: Optional[str] = None,
    lkey: Optional[Union[str, Tuple[str, ...]]] = None,
    rkey: Optional[Union[str, Tuple[str, ...]]] = None,
    presorted: bool = False,
    buffersize: Optional[int] = None,
    tempdir: Optional[str] = None,
    cache: bool = True,
    lprefix: Optional[str] = None,
    rprefix: Optional[str] = None,
) -> JoinView: ...
def outerjoin(
    left: TableView,
    right: TableView,
    key: Optional[str] = None,
    lkey: Optional[Union[str, Tuple[str, ...]]] = None,
    rkey: Optional[Union[str, Tuple[str, ...]]] = None,
    presorted: bool = False,
    buffersize: Optional[int] = None,
    tempdir: Optional[str] = None,
    cache: bool = True,
    lprefix: Optional[str] = None,
    rprefix: Optional[str] = None,
) -> JoinView: ...
def cut(table: TableView, *fields: str) -> CutView: ...
def addfield(
    table: TableView,
    field: str,
    value: Optional[Union[Any, Callable[[Dict[str, Any]], Any]]] = None,
    index: Optional[int] = None,
    missing: Optional[Any] = None,
) -> AddFieldView: ...
def sort(
    table: TableView,
    key: Optional[Union[str, List[str], Callable[..., Any]]] = None,
    reverse: bool = False,
    buffersize: Optional[int] = None,
    tempdir: Optional[str] = None,
    cache: bool = True,
) -> SortView: ...
def select(
    table: TableView,
    where: Union[str, Callable[[Dict[str, Any]], bool]],
) -> TableView: ...
def distinct(table: TableView, key: Optional[str] = None) -> TableView: ...
def tocsv(
    table: TableView,
    source: Optional[str] = None,
    encoding: Optional[str] = None,
    errors: str = "strict",
    write_header: bool = True,
    **csvargs: Any,
) -> None: ...
