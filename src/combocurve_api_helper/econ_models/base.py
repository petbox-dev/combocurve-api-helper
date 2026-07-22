import csv
import io
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, NamedTuple, Optional, TextIO, Tuple, Union

from . import formats


class Context(NamedTuple):
    id: Optional[str] = None
    created_at: Optional[str] = None
    project_name: Optional[str] = None


def common_columns(model: Dict[str, Any], context: Optional[Context]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if context is not None:
        out['Model Id'] = context.id or model.get('id', '') or ''
        out['Created At'] = formats.to_csv_datetime(context.created_at or model.get('createdAt'))
        out['Project Name'] = context.project_name or ''
    out['Model Type'] = formats.model_type(bool(model.get('unique', False)))
    out['Model Name'] = model.get('name', '') or ''
    out['New Name'] = ''
    out['Embedded Lookup Table'] = ''
    out['Last Update'] = formats.to_csv_datetime(model.get('updatedAt'))
    return out


def model_identity(rows: List[Dict[str, str]]) -> Tuple[str, bool]:
    """Extract `(name, unique)` from a mapper's `from_csv_rows` input, matching the
    'Model Name'/'Model Type' convention `common_columns` emits on every row of a model.

    `name` is the LAST-seen 'Model Name' across `rows` (default '' if `rows` is empty or
    no row carries the key); `unique` is whether the LAST row's 'Model Type' equals
    'unique' (recomputed fresh each row, not merged with the running value -- matching
    every mapper's original inline loop exactly). Every row of a real model carries an
    identical 'Model Name'/'Model Type', so in practice this only ever reads the common
    value; the last-seen semantics exist to replicate the original per-mapper loops
    byte-for-byte. One-row mappers get identical behavior by passing a single-element
    list.
    """
    name = ''
    unique = False
    for row in rows:
        name = row.get('Model Name', name)
        unique = row.get('Model Type') == 'unique'
    return name, unique


def group_rows_by_model_name(rows: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    """Split CSV rows into per-model groups keyed by 'Model Name', preserving first-seen order.

    A CC econ-model CSV stacks many models of one type, each spanning one or more rows that
    share a 'Model Name'. This is the production counterpart of the test helper of the same
    intent; `from_csv` uses it to feed one model's rows at a time to `from_csv_rows`.
    """
    groups: Dict[str, List[Dict[str, str]]] = {}
    order: List[str] = []
    for row in rows:
        name = row.get('Model Name', '')
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(row)
    return [groups[name] for name in order]


class EconModelMapper(ABC):
    """Base for econ-model API<->CSV mappers.

    Subclasses supply the type-specific pieces (`econ_model_type`, `columns`, `to_csv_rows`,
    `from_csv_rows`); this base implements the file-level conversions once in terms of them.
    """

    econ_model_type: str
    columns: List[str]

    @abstractmethod
    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        """Convert one econ-model API dict to its CSV rows (each keyed by `self.columns`)."""
        ...

    @abstractmethod
    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        """Reconstruct one econ-model API dict from the CSV rows of a single model."""
        ...

    def to_csv(self, models: List[Dict[str, Any]], context: Optional[Context] = None) -> str:
        """Serialize econ-model API dicts to a multi-model CSV string.

        The header (from `self.columns`) is always written, so `to_csv([])` returns a
        header-only string. Lines use the csv module's default CRLF terminator; write the
        result to a file opened with `newline=''` to avoid doubled newlines on Windows
        (`write_csv` does this).
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.columns)
        writer.writeheader()
        for model in models:
            writer.writerows(self.to_csv_rows(model, context))
        return buffer.getvalue()

    def from_csv(self, source: Union[str, TextIO]) -> List[Dict[str, Any]]:
        """Parse a multi-model CSV (a string or text file-like) into a list of API dicts, one
        per model, grouped by 'Model Name' in first-seen order.

        Raises `ValueError` if the CSV lacks a 'Model Name' column (not a CC econ-model export).
        """
        text = source if isinstance(source, str) else source.read()
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None or 'Model Name' not in reader.fieldnames:
            raise ValueError("CSV has no 'Model Name' column; not a ComboCurve econ-model export.")
        return [self.from_csv_rows(group) for group in group_rows_by_model_name(list(reader))]

    def read_csv(self, path: Union[str, os.PathLike[str]]) -> List[Dict[str, Any]]:
        """Read a multi-model CSV file into a list of econ-model API dicts."""
        with open(path, 'r', encoding='utf-8', newline='') as handle:
            return self.from_csv(handle)

    def write_csv(
        self,
        path: Union[str, os.PathLike[str]],
        models: List[Dict[str, Any]],
        context: Optional[Context] = None,
    ) -> None:
        """Write a list of econ-model API dicts to a multi-model CSV file (UTF-8)."""
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            handle.write(self.to_csv(models, context))
