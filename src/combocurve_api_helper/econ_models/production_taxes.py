import collections
import datetime
from typing import Annotated, Any, NamedTuple, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, EconModelMapper, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import (
    csv_to_float,
    csv_to_num,
    enum_from_csv,
    enum_to_csv,
    escalation_from_csv,
    escalation_to_csv,
    num_to_csv,
    num_to_csv_float,
)

# API 'key' (phase) -> CSV 'Key' column value, for severance_tax rows.
_PHASE_TO_CSV = {'oil': 'oil', 'gas': 'gas', 'ngl': 'ngl', 'drip_condensate': 'drip cond'}
_PHASE_FROM_CSV = {v: k for k, v in _PHASE_TO_CSV.items()}

# API 'unit' -> CSV 'Unit' column value. '$/month' is the Expenses export's spelling;
# '$/boe' follows the '$/bbl' pattern and rests on no export.
_UNIT_TO_CSV = {
    'pct_of_revenue': '% of rev',
    'dollar_per_bbl': '$/bbl',
    'dollar_per_mcf': '$/mcf',
    'dollar_per_boe': '$/boe',
    'dollar_per_month': '$/month',
}
_UNIT_FROM_CSV = {v: k for k, v in _UNIT_TO_CSV.items()}

# API 'criteria' -> CSV 'Criteria' column value. Unknown criteria raise. The offset and
# spellings are from a raw CC ProductionTaxes export (fixtures/production_taxes_criteria.csv).
# CC's API refuses water_rate on severance rows; it is an ad valorem criteria.
_FLAT_CRITERIA_CSV = 'flat'
_DATES_CRITERIA_CSV = 'dates'
_CRITERIA_TO_CSV = {
    'entire_well_life': _FLAT_CRITERIA_CSV,
    'dates': _DATES_CRITERIA_CSV,
    'offset_to_fpd': 'fpd',
    'offset_to_as_of_date': 'as of',
    'offset_to_discount_date': 'disc date',
    'offset_to_first_segment': 'maj seg',
    'offset_to_end_history': 'end hist',
    'oil_rate': 'oil rate',
    'gas_rate': 'gas rate',
    'water_rate': 'water rate',
}
_CRITERIA_FROM_CSV = {v: k for k, v in _CRITERIA_TO_CSV.items()}
# Every other criteria's period is a list of numbers: month offsets or rate thresholds.

# For a 'dates' criteria CC's export writes the Period as 'MM/YYYY' ('2023-07-01' ->
# '07/2023', '1900-01-01' -> '01/1900'). Versions up to 2.5.0 wrote '%b-%y' ('Jul-23'),
# which is how Excel displays '07/2023'; that form lost the century. It is still read, with
# its old rule: 'Jan-00' is CC's 1900-01-01 sentinel, every other year is 20xx.
_LEGACY_MONTH_ABBREVIATIONS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
_LEGACY_DATES_START_SENTINEL_CSV = 'Jan-00'
_DATES_START_SENTINEL_ISO = '1900-01-01'


def _dates_period_to_csv(iso: str) -> str:
    period_date = datetime.datetime.strptime(iso[:10], '%Y-%m-%d').date()
    return f'{period_date.month:02d}/{period_date.year:04d}'


def _dates_period_from_csv(period_csv: str) -> str:
    if '/' in period_csv:
        month, year = period_csv.split('/')
        return datetime.date(int(year), int(month), 1).isoformat()
    if period_csv == _LEGACY_DATES_START_SENTINEL_CSV:
        return _DATES_START_SENTINEL_ISO
    month_abbreviation, two_digit_year = period_csv.split('-')
    month_number = _LEGACY_MONTH_ABBREVIATIONS.index(month_abbreviation) + 1
    return datetime.date(2000 + int(two_digit_year), month_number, 1).isoformat()


_SEVERANCE_CATEGORY_API = 'severance_tax'
_SEVERANCE_CATEGORY_CSV = 'Severance Tax'

# Ad valorem rows: the API 'category' is 'ad_val_tax' (NOT 'ad_valorem_tax' -- that
# string is instead the constant, recoverable API 'key' on these rows), e.g.
# {"key": "ad_valorem_tax", "category": "ad_val_tax", ...}.
_AD_VALOREM_CATEGORY_API = 'ad_val_tax'
_AD_VALOREM_KEY_API = 'ad_valorem_tax'
_AD_VALOREM_KEY_CSV = 'Ad Valorem Tax'
_AD_VALOREM_CATEGORY_CSV = 'Ad Val Tax'


class ProductionTaxApiRow(BaseModel):
    """One `data.rows[]` element of the ProductionTaxes API shape.

    `deduct_severance_tax` (API `deductSeveranceTax`) is the structurally interesting
    field: severance rows (`category == 'severance_tax'`) never carry this key at all --
    it is a real absence, not a null value -- while ad valorem rows (`category ==
    'ad_val_tax'`) always carry it as a bool. Leaving the field at its `None` default and
    dumping with `model_dump(by_alias=True, exclude_none=True)` reproduces that: unset ->
    key omitted (severance), explicitly set -> key emitted (ad valorem).
    """

    model_config = ConfigDict(populate_by_name=True)

    key: str
    category: str
    criteria: str
    period: list[Any]
    value: list[Any]
    unit: str
    shrinkage_condition: Annotated[Optional[str], Field(alias='shrinkageCondition')] = None
    escalation: Optional[str] = None
    calculation: Optional[str] = None
    deduct_severance_tax: Annotated[Optional[bool], Field(alias='deductSeveranceTax')] = None
    rate_type: Annotated[Optional[str], Field(alias='rateType')] = None
    rate_rows_calculation_method: Annotated[Optional[str], Field(alias='rateRowsCalculationMethod')] = None


class KeyCategoryDeduct(NamedTuple):
    """The CSV 'Key'/'Category'/'Deduct Severance Tax' cell strings for one production-tax
    row, as resolved by `_key_category_deduct`."""

    key_csv: str  # 'Key' column
    category_csv: str  # 'Category' column
    deduct: str  # 'Deduct Severance Tax' column ('' for severance rows, yes/no for ad valorem)


def _numbered_category(category_csv: str, rows_total: int, ordinal: int) -> str:
    """A key with one row keeps the bare Category; a key with several rows numbers them
    ('Severance Tax 1', 'Severance Tax 2'), so the inverse can tell them apart. The CC
    export shows that form for severance; for ad valorem ('Ad Val Tax 1') it is unverified."""
    return category_csv if rows_total == 1 else f'{category_csv} {ordinal}'


def _key_category_deduct(
    row: ProductionTaxApiRow, rows_total: dict[str, int], rows_seen: dict[str, int]
) -> KeyCategoryDeduct:
    """`rows_total`/`rows_seen` count rows per API `key`: a phase for severance rows, the
    constant 'ad_valorem_tax' for ad valorem rows."""
    rows_seen[row.key] = rows_seen.get(row.key, 0) + 1
    if row.category == _SEVERANCE_CATEGORY_API:
        if row.key not in _PHASE_TO_CSV:
            raise NotImplementedError(f'Unknown production tax phase: {row.key}')
        category_csv = _numbered_category(_SEVERANCE_CATEGORY_CSV, rows_total[row.key], rows_seen[row.key])
        return KeyCategoryDeduct(_PHASE_TO_CSV[row.key], category_csv, '')
    if row.category == _AD_VALOREM_CATEGORY_API:
        category_csv = _numbered_category(_AD_VALOREM_CATEGORY_CSV, rows_total[row.key], rows_seen[row.key])
        return KeyCategoryDeduct(_AD_VALOREM_KEY_CSV, category_csv, formats.yes_no(row.deduct_severance_tax))
    raise NotImplementedError(f'Unknown production tax category: {row.category}')


# CC's export writes a null API value (live flat rows can carry `value: [null]`) as 'nan'
# (fixtures/production_taxes_null_value.csv). A blank Value, which 2.6.0 development builds
# wrote, also reads as null.
_NULL_VALUE_CSV = 'nan'


def _optional_float_to_csv(value: Optional[Union[int, float]]) -> str:
    return _NULL_VALUE_CSV if value is None else num_to_csv_float(value)


def _optional_csv_to_float(value_csv: str) -> Optional[float]:
    return None if value_csv in ('', _NULL_VALUE_CSV) else csv_to_float(value_csv)


def _is_category(category_csv: str, base_category_csv: str) -> bool:
    """True for the bare Category or its numbered form (see `_numbered_category`)."""
    if category_csv == base_category_csv:
        return True
    prefix = f'{base_category_csv} '
    return category_csv.startswith(prefix) and category_csv[len(prefix) :].isdigit()


def _build_api_row(key_csv: str, category_csv: str, members: list[dict[str, str]]) -> dict[str, Any]:
    first = members[0]

    criteria_csv = first['Criteria']
    if criteria_csv not in _CRITERIA_FROM_CSV:
        raise NotImplementedError(f'Unknown production tax Criteria: {criteria_csv}')
    criteria_api = _CRITERIA_FROM_CSV[criteria_csv]

    unit_csv = first['Unit']
    if unit_csv not in _UNIT_FROM_CSV:
        raise NotImplementedError(f'Unknown production tax Unit: {unit_csv}')

    if key_csv == _AD_VALOREM_KEY_CSV:
        if not _is_category(category_csv, _AD_VALOREM_CATEGORY_CSV):
            raise NotImplementedError(f'Unknown production tax Category for Ad Valorem Tax: {category_csv}')
        phase = _AD_VALOREM_KEY_API
        category = _AD_VALOREM_CATEGORY_API
    else:
        if key_csv not in _PHASE_FROM_CSV:
            raise NotImplementedError(f'Unknown production tax Key: {key_csv}')
        if not _is_category(category_csv, _SEVERANCE_CATEGORY_CSV):
            raise NotImplementedError(f'Unknown production tax Category: {category_csv}')
        phase = _PHASE_FROM_CSV[key_csv]
        category = _SEVERANCE_CATEGORY_API

    flat_marker = formats.ENTIRE_WELL_LIFE_MARKER
    period: list[Any]
    if criteria_csv == _FLAT_CRITERIA_CSV:
        period = [flat_marker for _ in members]
    elif criteria_csv == _DATES_CRITERIA_CSV:
        period = [_dates_period_from_csv(m['Period']) for m in members]
    else:
        period = [csv_to_num(m['Period']) for m in members]
    value: list[Any] = [_optional_csv_to_float(m['Value']) for m in members]

    row_kwargs: dict[str, Any] = {
        'key': phase,
        'category': category,
        'criteria': criteria_api,
        'period': period,
        'value': value,
        'unit': _UNIT_FROM_CSV[unit_csv],
        'shrinkage_condition': first.get('Shrinkage Condition') or None,
        'escalation': escalation_from_csv(first.get('Escalation', ''), title=True),
        'calculation': first.get('Calculation') or None,
        'rate_type': enum_from_csv(first.get('Rate Type', '')),
        'rate_rows_calculation_method': enum_from_csv(first.get('Rate Rows Calculation Method', '')),
    }
    if category == _AD_VALOREM_CATEGORY_API:
        row_kwargs['deduct_severance_tax'] = formats.parse_yes_no(first.get('Deduct Severance Tax', ''))

    return ProductionTaxApiRow(**row_kwargs).model_dump(by_alias=True, exclude_none=True)


class ProductionTaxesMapper(EconModelMapper):
    econ_model_type = 'ProductionTaxes'
    columns = COLUMNS['ProductionTaxes']
    float_columns = frozenset({'Value'})

    def to_row_dicts(self, model: dict[str, Any], context: Optional[Context] = None) -> list[dict[str, str]]:
        common = common_columns(model, context)
        data = model.get('data') or {}
        state = data.get('state', '') or ''
        api_rows = data.get('rows', []) or []

        parsed = [ProductionTaxApiRow.model_validate(r) for r in api_rows]

        rows_total = collections.Counter(row.key for row in parsed)
        rows_seen: dict[str, int] = {}
        rows: list[dict[str, str]] = []
        for row in parsed:
            key_csv, category_csv, deduct_severance = _key_category_deduct(row, rows_total, rows_seen)
            if row.unit not in _UNIT_TO_CSV:
                raise NotImplementedError(f'Unknown production tax unit: {row.unit}')
            unit_csv = _UNIT_TO_CSV[row.unit]

            if row.criteria not in _CRITERIA_TO_CSV:
                raise NotImplementedError(f'Unknown production tax criteria: {row.criteria}')
            criteria_csv = _CRITERIA_TO_CSV[row.criteria]

            for period_elem, value_elem in zip(row.period, row.value):
                if criteria_csv == _FLAT_CRITERIA_CSV or period_elem is None:
                    period_csv = ''
                elif criteria_csv == _DATES_CRITERIA_CSV:
                    period_csv = _dates_period_to_csv(period_elem)
                else:
                    period_csv = num_to_csv(period_elem)
                csv_row = dict(common)
                csv_row.update(
                    {
                        'Production Taxes State': state,
                        'Key': key_csv,
                        'Stream Type': '',
                        'Category': category_csv,
                        'Criteria': criteria_csv,
                        'Value': _optional_float_to_csv(value_elem),
                        'Period': period_csv,
                        'Unit': unit_csv,
                        'Description': '',
                        'Shrinkage Condition': row.shrinkage_condition or '',
                        'Escalation': escalation_to_csv(row.escalation, title=True),
                        'Calculation': row.calculation or '',
                        'Deduct Severance Tax': deduct_severance,
                        'Rate Type': enum_to_csv(row.rate_type),
                        'Rate Rows Calculation Method': enum_to_csv(row.rate_rows_calculation_method),
                    }
                )
                rows.append({c: csv_row.get(c, '') for c in self.columns})
        return rows

    def from_row_dicts(self, rows: list[dict[str, str]]) -> dict[str, Any]:
        groups: dict[tuple[str, str], list[dict[str, str]]] = {}
        order: list[tuple[str, str]] = []
        name, unique = model_identity(rows)
        state = ''
        for row in rows:
            state = row.get('Production Taxes State', state) or state
            group_key = (row['Key'], row['Category'])
            if group_key not in groups:
                groups[group_key] = []
                order.append(group_key)
            groups[group_key].append(row)

        api_rows: list[dict[str, Any]] = []
        for key_csv, category_csv in order:
            api_rows.append(_build_api_row(key_csv, category_csv, groups[(key_csv, category_csv)]))

        return {'name': name, 'unique': unique, 'data': {'state': state, 'rows': api_rows}}
