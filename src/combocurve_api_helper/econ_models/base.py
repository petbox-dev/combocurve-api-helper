import csv
import io
import os
from abc import ABC, abstractmethod
from typing import Any, NamedTuple, Optional, TextIO, Union

from .._csv_writer import RowWriter
from . import formats


class Context(NamedTuple):
    id: Optional[str] = None
    created_at: Optional[str] = None
    project_name: Optional[str] = None


def common_columns(model: dict[str, Any], context: Optional[Context]) -> dict[str, str]:
    out: dict[str, str] = {}
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


def model_identity(rows: list[dict[str, str]]) -> tuple[str, bool]:
    """Extract `(name, unique)` from a mapper's `from_row_dicts` input, matching the
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


def group_rows_by_model_name(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Split CSV rows into per-model groups keyed by 'Model Name', preserving first-seen order.

    A CC econ-model CSV stacks many models of one type, each spanning one or more rows that
    share a 'Model Name'. This is the production counterpart of the test helper of the same
    intent; `from_csv` uses it to feed one model's rows at a time to `from_row_dicts`.
    """
    groups: dict[str, list[dict[str, str]]] = {}
    order: list[str] = []
    for row in rows:
        name = row.get('Model Name', '')
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(row)
    return [groups[name] for name in order]


class EconModelMapper(RowWriter, ABC):
    """Base for econ-model API<->CSV mappers.

    Subclasses supply the type-specific pieces (`econ_model_type`, `columns`, `to_row_dicts`,
    `from_row_dicts`); this base implements the file-level conversions once in terms of them.
    The round-trip half (`from_row_dicts`, `from_csv`) lives here; the one-way WRITE half
    (`columns` -> CSV) is inherited from `RowWriter`, which one-way exporters share.
    """

    econ_model_type: str

    @abstractmethod
    def to_row_dicts(self, model: dict[str, Any], context: Optional[Context] = None) -> list[dict[str, str]]:
        """Convert one econ-model API dict to its CSV rows (each keyed by `self.columns`)."""
        ...

    @abstractmethod
    def from_row_dicts(self, rows: list[dict[str, str]]) -> dict[str, Any]:
        """Reconstruct one econ-model API dict from the CSV rows of a single model."""
        ...

    def to_csv(self, models: list[dict[str, Any]], context: Optional[Context] = None) -> str:
        """Serialize econ-model API dicts to a multi-model CSV string.

        The header (from `self.columns`) is always written, so `to_csv([])` returns a
        header-only string. Lines use the csv module's default CRLF terminator; write the
        result to a file opened with `newline=''` to avoid doubled newlines on Windows
        (`write_csv` does this).
        """
        rows: list[dict[str, str]] = []
        for model in models:
            rows.extend(self.to_row_dicts(model, context))
        return self.rows_to_csv(rows)

    def from_csv(self, source: Union[str, TextIO]) -> list[dict[str, Any]]:
        """Parse a multi-model CSV (a string or text file-like) into a list of API dicts, one
        per model, grouped by 'Model Name' in first-seen order.

        Raises `ValueError` if the CSV lacks a 'Model Name' column (not a CC econ-model export).
        """
        text = source if isinstance(source, str) else source.read()
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None or 'Model Name' not in reader.fieldnames:
            raise ValueError("CSV has no 'Model Name' column; not a ComboCurve econ-model export.")
        return [self.from_row_dicts(group) for group in group_rows_by_model_name(list(reader))]

    def read_csv(self, path: Union[str, os.PathLike[str]]) -> list[dict[str, Any]]:
        """Read a multi-model CSV file into a list of econ-model API dicts."""
        with open(path, encoding='utf-8', newline='') as handle:
            return self.from_csv(handle)

    def write_csv(
        self,
        path: Union[str, os.PathLike[str]],
        models: list[dict[str, Any]],
        context: Optional[Context] = None,
    ) -> None:
        """Write a list of econ-model API dicts to a multi-model CSV file (UTF-8)."""
        with open(path, 'w', encoding='utf-8', newline='') as handle:
            handle.write(self.to_csv(models, context))
