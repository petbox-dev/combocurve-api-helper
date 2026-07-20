from typing import Any, Dict, List, NamedTuple, Optional, Protocol, Tuple

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


class EconModelMapper(Protocol):
    econ_model_type: str
    columns: List[str]

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]: ...
    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]: ...
