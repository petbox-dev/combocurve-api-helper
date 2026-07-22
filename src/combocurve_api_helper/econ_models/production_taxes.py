import datetime
from typing import Annotated, Any, Dict, List, NamedTuple, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import csv_to_num, enum_from_csv, enum_to_csv, escalation_from_csv, escalation_to_csv, num_to_csv

# API 'key' (phase) -> CSV 'Key' column value, for severance_tax rows.
_PHASE_TO_CSV = {'oil': 'oil', 'gas': 'gas', 'ngl': 'ngl', 'drip_condensate': 'drip cond'}
_PHASE_FROM_CSV = {v: k for k, v in _PHASE_TO_CSV.items()}

# API 'unit' -> CSV 'Unit' column value.
_UNIT_TO_CSV = {'pct_of_revenue': '% of rev', 'dollar_per_bbl': '$/bbl', 'dollar_per_mcf': '$/mcf'}
_UNIT_FROM_CSV = {v: k for k, v in _UNIT_TO_CSV.items()}

# API 'criteria' -> CSV 'Criteria' column value. Unknown criteria raise.
_CRITERIA_TO_CSV = {'entire_well_life': 'flat', 'offset_to_fpd': 'fpd', 'dates': 'dates'}
_CRITERIA_FROM_CSV = {v: k for k, v in _CRITERIA_TO_CSV.items()}

# For a 'dates' criteria the Period column is the schedule date rendered as month-abbrev +
# 2-digit year ('2023-07-01' -> 'Jul-23'). Every dates schedule's first period is CC's
# 1900-01-01 "beginning of time" sentinel, which renders as 'Jan-00'. '%b-%y' cannot carry
# the century, so that exact string is special-cased on the inverse to keep the round-trip
# lossless; all other periods are 21st-century first-of-month dates. A fixed English month
# table keeps output locale-independent.
_MONTH_ABBRS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
_DATES_START_SENTINEL_ISO = '1900-01-01'
_DATES_START_SENTINEL_CSV = 'Jan-00'


def _dates_period_to_csv(iso: str) -> str:
    d = datetime.datetime.strptime(iso[:10], '%Y-%m-%d').date()
    return f'{_MONTH_ABBRS[d.month - 1]}-{d.year % 100:02d}'


def _dates_period_from_csv(period_csv: str) -> str:
    if period_csv == _DATES_START_SENTINEL_CSV:
        return _DATES_START_SENTINEL_ISO
    mon_abbr, yy = period_csv.split('-')
    return datetime.date(2000 + int(yy), _MONTH_ABBRS.index(mon_abbr) + 1, 1).isoformat()


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
    period: List[Any]
    value: List[Any]
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


def _key_category_deduct(
    row: ProductionTaxApiRow, severance_total: Dict[str, int], severance_seen: Dict[str, int]
) -> KeyCategoryDeduct:
    if row.category == _SEVERANCE_CATEGORY_API:
        phase = row.key
        if phase not in _PHASE_TO_CSV:
            raise NotImplementedError(f'Unknown production tax phase: {phase}')
        severance_seen[phase] = severance_seen.get(phase, 0) + 1
        ordinal = severance_seen[phase]
        key_csv = _PHASE_TO_CSV[phase]
        category_csv = (
            _SEVERANCE_CATEGORY_CSV if severance_total[phase] == 1 else f'{_SEVERANCE_CATEGORY_CSV} {ordinal}'
        )
        return KeyCategoryDeduct(key_csv, category_csv, '')
    if row.category == _AD_VALOREM_CATEGORY_API:
        return KeyCategoryDeduct(
            _AD_VALOREM_KEY_CSV, _AD_VALOREM_CATEGORY_CSV, formats.yes_no(row.deduct_severance_tax)
        )
    raise NotImplementedError(f'Unknown production tax category: {row.category}')


def _is_severance_category(category_csv: str) -> bool:
    if category_csv == _SEVERANCE_CATEGORY_CSV:
        return True
    prefix = f'{_SEVERANCE_CATEGORY_CSV} '
    return category_csv.startswith(prefix) and category_csv[len(prefix) :].isdigit()


def _build_api_row(key_csv: str, category_csv: str, members: List[Dict[str, str]]) -> Dict[str, Any]:
    first = members[0]

    criteria_csv = first['Criteria']
    if criteria_csv not in _CRITERIA_FROM_CSV:
        raise NotImplementedError(f'Unknown production tax Criteria: {criteria_csv}')
    criteria_api = _CRITERIA_FROM_CSV[criteria_csv]

    unit_csv = first['Unit']
    if unit_csv not in _UNIT_FROM_CSV:
        raise NotImplementedError(f'Unknown production tax Unit: {unit_csv}')

    if key_csv == _AD_VALOREM_KEY_CSV:
        if category_csv != _AD_VALOREM_CATEGORY_CSV:
            raise NotImplementedError(f'Unknown production tax Category for Ad Valorem Tax: {category_csv}')
        phase = _AD_VALOREM_KEY_API
        category = _AD_VALOREM_CATEGORY_API
    else:
        if key_csv not in _PHASE_FROM_CSV:
            raise NotImplementedError(f'Unknown production tax Key: {key_csv}')
        if not _is_severance_category(category_csv):
            raise NotImplementedError(f'Unknown production tax Category: {category_csv}')
        phase = _PHASE_FROM_CSV[key_csv]
        category = _SEVERANCE_CATEGORY_API

    flat_marker = formats.ENTIRE_WELL_LIFE_MARKER
    period: List[Any]
    if criteria_csv == 'flat':
        period = [flat_marker for _ in members]
    elif criteria_csv == 'dates':
        period = [_dates_period_from_csv(m['Period']) for m in members]
    else:
        period = [m['Period'] for m in members]
    value: List[Any] = [csv_to_num(m['Value']) for m in members]

    row_kwargs: Dict[str, Any] = {
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


class ProductionTaxesMapper:
    econ_model_type = 'ProductionTaxes'
    columns = COLUMNS['ProductionTaxes']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        data = model.get('data') or {}
        state = data.get('state', '') or ''
        api_rows = data.get('rows', []) or []

        parsed = [ProductionTaxApiRow.model_validate(r) for r in api_rows]

        severance_total: Dict[str, int] = {}
        for row in parsed:
            if row.category == _SEVERANCE_CATEGORY_API:
                severance_total[row.key] = severance_total.get(row.key, 0) + 1

        severance_seen: Dict[str, int] = {}
        rows: List[Dict[str, str]] = []
        for row in parsed:
            key_csv, category_csv, deduct_severance = _key_category_deduct(row, severance_total, severance_seen)
            if row.unit not in _UNIT_TO_CSV:
                raise NotImplementedError(f'Unknown production tax unit: {row.unit}')
            unit_csv = _UNIT_TO_CSV[row.unit]

            if row.criteria not in _CRITERIA_TO_CSV:
                raise NotImplementedError(f'Unknown production tax criteria: {row.criteria}')
            criteria_csv = _CRITERIA_TO_CSV[row.criteria]

            for period_elem, value_elem in zip(row.period, row.value):
                if criteria_csv == 'flat' or period_elem is None:
                    period_csv = ''
                elif criteria_csv == 'dates':
                    period_csv = _dates_period_to_csv(period_elem)
                else:
                    period_csv = str(period_elem)
                csv_row = dict(common)
                csv_row.update(
                    {
                        'Production Taxes State': state,
                        'Key': key_csv,
                        'Stream Type': '',
                        'Category': category_csv,
                        'Criteria': criteria_csv,
                        'Value': num_to_csv(value_elem),
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

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        groups: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
        order: List[Tuple[str, str]] = []
        name, unique = model_identity(rows)
        state = ''
        for row in rows:
            state = row.get('Production Taxes State', state) or state
            group_key = (row['Key'], row['Category'])
            if group_key not in groups:
                groups[group_key] = []
                order.append(group_key)
            groups[group_key].append(row)

        api_rows: List[Dict[str, Any]] = []
        for key_csv, category_csv in order:
            api_rows.append(_build_api_row(key_csv, category_csv, groups[(key_csv, category_csv)]))

        return {'name': name, 'unique': unique, 'data': {'state': state, 'rows': api_rows}}
