import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple, Union


def model_type(unique: bool) -> str:
    return 'unique' if unique else 'project'


def _parse_iso(value: str) -> datetime.datetime:
    v = value.replace('Z', '+00:00') if value.endswith('Z') else value
    return datetime.datetime.fromisoformat(v)


def to_csv_date(iso: Optional[str]) -> str:
    if not iso:
        return ''
    return _parse_iso(iso).strftime('%m/%d/%Y')


def to_csv_datetime(iso: Optional[str]) -> str:
    if not iso:
        return ''
    return _parse_iso(iso).strftime('%m/%d/%Y %H:%M:%S')


def from_csv_date(s: str) -> str:
    if not s:
        return ''
    return datetime.datetime.strptime(s, '%m/%d/%Y').date().isoformat()


def yes_blank(b: Optional[bool]) -> str:
    return 'yes' if b else ''


def yes_no(b: Optional[bool]) -> str:
    return 'yes' if b else 'no'


def parse_yes_blank(s: str) -> bool:
    return s.strip().lower() == 'yes'


def parse_yes_no(s: str) -> bool:
    return s.strip().lower() == 'yes'


def _float_str(f: float) -> str:
    """Shortest round-trippable decimal string for `f`, never in exponent form.

    Python's `str`/`repr` switch to scientific notation for |f| < 1e-4 (e.g.
    `str(5e-05) == '5e-05'`) and for very large magnitudes -- which does not match
    CC's decimal CSV cells and breaks the forward + round-trip contract. `repr`
    still gives the shortest string that round-trips to `f`; when that is in
    exponent form, `Decimal` re-expands it positionally without losing precision.
    """
    s = repr(f)
    if 'e' in s or 'E' in s:
        s = format(Decimal(s), 'f')
    return s


def num_to_csv(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    f = float(value)
    if f == int(f):
        return str(int(f))
    return _float_str(f)


def num_to_csv_float(value: Any) -> str:
    """Like num_to_csv, but always renders with a decimal point.

    StreamProperties 'Value' and Expenses 'Value'/'Paying WI / Earning WI' always
    display whole numbers as e.g. '100.0', not '100' -- unlike most other numeric
    columns across the econ-model CSV exports (Capex, Differentials, ProductionTaxes),
    which drop the trailing '.0' (handled by num_to_csv above). Per-type/per-column,
    not universal.
    """
    s = _float_str(float(value))
    if '.' not in s:
        s += '.0'
    return s


def csv_to_num(s: str) -> Union[int, float]:
    f = float(s)
    if f == int(f):
        return int(f)
    return f


# CC's `entireWellLife` field is the "flat criteria" marker. Both 'Flat' and the
# equivalent 'Entire Well Life' (carried by some Pricing models) denote the same flat
# criteria. We do not control CC's vocabulary, so any value outside this known set must
# fail loud rather than be silently mapped to 'flat' -- an unrecognized marker then
# surfaces (to be handled) instead of corrupting the mapping.
ENTIRE_WELL_LIFE_VALUES = frozenset({'Flat', 'Entire Well Life'})

# The literal `entireWellLife` value this package writes back on the inverse (CSV -> API)
# pass for a 'flat' criteria row -- 'Flat' is one of the two values `ENTIRE_WELL_LIFE_VALUES`
# accepts on read, and is the value used for write-back.
ENTIRE_WELL_LIFE_MARKER = 'Flat'


def check_entire_well_life(value: str) -> None:
    """Validate a CC `entireWellLife` flat-criteria marker; raise on any unknown value."""
    if value not in ENTIRE_WELL_LIFE_VALUES:
        raise NotImplementedError(f'Unknown entireWellLife value: {value!r}')


def flat_or_dates_criteria(entire_well_life: Optional[str], dates: Optional[str], *, what: str) -> Tuple[str, str]:
    """Shared 'flat'/'dates' (Criteria, Period) CSV pair for a pydantic row that carries
    exactly one of `entireWellLife`/`dates` (StreamProperties/Differentials/Pricing rows
    all share this exact shape). Validates `entire_well_life` via `check_entire_well_life`
    when present; raises `NotImplementedError` when neither field is set. `what` names the
    caller's row kind, for a legible error message only.
    """
    if entire_well_life is not None:
        check_entire_well_life(entire_well_life)
        return 'flat', ''
    if dates is not None:
        return 'dates', to_csv_date(dates)
    raise NotImplementedError(f'Unknown {what} criteria row: entireWellLife/dates both None')


def flat_or_dates_row_kwargs(criteria_csv: str, period_csv: str, marker: str) -> Dict[str, Any]:
    """Inverse of `flat_or_dates_criteria`: build the `{'entire_well_life': ...}` or
    `{'dates': ...}` row kwarg for a CSV 'Criteria'/'Period' cell pair. `marker` is the
    write-back `entire_well_life` value to use for a 'flat' row (see
    `ENTIRE_WELL_LIFE_MARKER`). Raises `NotImplementedError` on any other Criteria value --
    unlike the pre-refactor Differentials inverse, an unknown Criteria is never silently
    treated as 'dates'.
    """
    if criteria_csv == 'flat':
        return {'entire_well_life': marker}
    if criteria_csv == 'dates':
        return {'dates': from_csv_date(period_csv)}
    raise NotImplementedError(f'Unknown Criteria: {criteria_csv!r}')


# API model-name value <-> CSV display for 'Escalation' (and, in Capex, 'Depreciation')
# columns. ProductionTaxes and Capex render the API 'none' model as the title-cased
# string 'None' -- NOT lowercase 'none'. Differentials and Expenses CSVs, by contrast,
# render 'none' unchanged (lowercase) -- pass `title=False` for those. Any other model
# name passes through unchanged in both modes. Python `None` (the field simply absent/
# unset) always inverts with '' regardless of `title`.
_API_NONE_MODEL = 'none'
_CSV_NONE_MODEL = 'None'


def escalation_to_csv(value: Optional[str], *, title: bool) -> str:
    if value is None:
        return ''
    if title and value == _API_NONE_MODEL:
        return _CSV_NONE_MODEL
    return value


def escalation_from_csv(s: str, *, title: bool) -> Optional[str]:
    if not s:
        return None
    if title and s == _CSV_NONE_MODEL:
        return _API_NONE_MODEL
    return s


# Underscore/space enum-token conversion for columns like ProductionTaxes' 'Rate Type'
# ('gross_well_head' <-> 'gross well head') and 'Rate Rows Calculation Method'
# ('non_monotonic' <-> 'non monotonic'). `None`/'' inverts to '' /`None` like every
# other optional-string column.
def enum_to_csv(v: Optional[str]) -> str:
    if v is None:
        return ''
    return v.replace('_', ' ')


def enum_from_csv(s: str) -> Optional[str]:
    if not s:
        return None
    return s.replace(' ', '_')


# API phase (camelCase, e.g. `dripCondensate`) -> CSV display value. Shared table used by
# the Differentials and Pricing mappers -- both mappers' phase set is exactly
# {oil, gas, ngl, dripCondensate}. NOT shared with ProductionTaxes/Expenses, which key
# drip cond as the snake_case `drip_condensate` (a real API difference, not an oversight),
# nor with StreamProperties, whose phase map is embedded in a larger category table.
PHASE_TO_CSV_CAMEL: Dict[str, str] = {'oil': 'oil', 'gas': 'gas', 'ngl': 'ngl', 'dripCondensate': 'drip cond'}
