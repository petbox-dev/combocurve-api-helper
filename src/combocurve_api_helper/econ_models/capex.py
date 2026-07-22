import json
import warnings
from typing import Annotated, Any, Dict, List, NamedTuple, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, EconModelMapper, common_columns, model_identity
from .csv_columns import COLUMNS
from .enums import (
    CRITERIA_FROM_CSV,
    CRITERIA_TO_CSV,
    OFFSET_FROM_HEADER_CSV,
    OFFSET_FROM_SCHEDULE_CSV,
    OFFSET_TO_API_DATEKEY,
    OFFSET_TO_HEADER_CSV,
    OFFSET_TO_SCHEDULE_CSV,
    Criteria,
)
from .formats import csv_to_num, enum_from_csv, enum_to_csv, escalation_from_csv, escalation_to_csv
from .formats import num_to_csv

# otherCapex `fromHeaders` rows carry the token 'offset_to_first_prod_date' with companion
# API date-key 'firstProdDate' (e.g. {'fromHeaders': 'offset_to_first_prod_date',
# 'firstProdDate': 185}). This is now `OffsetTo.FirstProductionDate` in enums.py (it
# previously held the different string 'offset_to_first_production_date', with no other
# consumer anywhere in the repo -- see enums.py) with a matching
# `OFFSET_TO_HEADER_CSV`/`OFFSET_TO_API_DATEKEY` entry, so no local override table is needed
# here anymore; the bare enums.py imports above are used directly.
# `OFFSET_TO_SCHEDULE_CSV`/`OFFSET_FROM_SCHEDULE_CSV` remain untouched: no `fromSchedule`
# row using this token is known, so extending it would be speculative; an unmapped token
# still raises loudly.

# escalationStart API key -> CSV 'Escalation Start Criteria' display. Exactly two keys
# occur -- {'applyToCriteria': <int>} and {'asOfDate': <int>} -- plus a None escalationStart
# (rendered blank by _escalation_start_to_csv). Both values are integer day-offsets, so
# num_to_csv is correct for each. 'apply to criteria' and 'as of date' are CC's two
# escalation-start UI options, lowercased. Fail loud on any other shape.
_ESCALATION_START_KEY_TO_CSV: Dict[str, str] = {
    'applyToCriteria': 'apply to criteria',
    'asOfDate': 'as of date',
}
_ESCALATION_START_KEY_FROM_CSV: Dict[str, str] = {v: k for k, v in _ESCALATION_START_KEY_TO_CSV.items()}

# CC's CSV export OMITS the model-level $/ft `drillingCost`/`completionCost` objects.
# Rather than drop them, CapexMapper captures each as a compact JSON blob in an extra
# column. CC ignores unknown column headers on import, so the CSV stays re-importable.
# These header strings MUST match csv_columns.COLUMNS['Capex'].
_DRILLING_COST_COL = 'Drilling Cost ($/ft)'
_COMPLETION_COST_COL = 'Completion Cost ($/ft)'


def _perfoot_to_json(obj: Optional[Dict[str, Any]]) -> str:
    """Serialize a model-level $/ft object (drillingCost/completionCost) to a compact,
    key-sorted JSON string; '' when absent. Lossless -- preserves the nested `rows[]`
    timing schedule and completion's tiered `dollarPerFtOfHorizontal` list."""
    if obj is None:
        return ''
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)


def _perfoot_from_json(cell: str) -> Optional[Dict[str, Any]]:
    """Inverse of `_perfoot_to_json`: parse a $/ft JSON cell back to its object, or None
    when the cell is blank."""
    if not cell:
        return None
    parsed: Dict[str, Any] = json.loads(cell)
    return parsed


# otherCapex rows also carry probabilistic fields with no CSV column at all (distribution
# type/mean/stdev/bounds/mode/seed). These normally sit at a fixed, invariant default --
# so on the inverse pass we reconstruct that default, giving exact round-trip equality for
# the common case. A row with non-default probabilistic values will not round-trip;
# to_row_dicts warns rather than silently dropping the distinction.
_PROBABILISTIC_DEFAULTS: Dict[str, Any] = {
    'distributionType': 'na',
    'mean': 0,
    'standardDeviation': 0,
    'lowerBound': 0,
    'upperBound': 0,
    'mode': 0,
    'seed': 1,
}


class CapexOtherRow(BaseModel):
    """One `otherCapex.rows[]` element of the Capex API shape.

    Named fields cover the always-present scalar columns. The row's single Criteria
    key (one of twelve -- see `Criteria`), its optional companion API date-header key
    (see `OFFSET_TO_API_DATEKEY`, populated only for `fromHeaders`/`fromSchedule`
    rows), and the seven probabilistic-distribution fields are deliberately left as
    free-form extras (`extra='allow'`) rather than ~40 individually-named optional
    fields: a real row carries exactly one criterion key (plus, for fromHeaders/
    fromSchedule, one companion date key out of 24 possible OffsetTo tokens), so
    naming all of them would be both unwieldy and -- for any token this mapper doesn't
    yet recognize -- would silently swallow the raw value under pydantic's default
    `extra='ignore'`. Keeping them as extras (accessible via `model_extra`) preserves
    the original dict-based criterion-detection/probabilistic-check logic
    byte-for-byte; see `_detect_criterion`/`_criteria_value_headers`/
    `_check_probabilistic` below.

    `escalation_model`/`depreciation_model` have the same None-vs-'none' round-trip
    quirk as Differentials' escalationModel (see `DifferentialPhaseNode` docstring):
    CapexMapper.from_row_dicts must keep these keys present (possibly `None`) on the
    reconstructed row rather than letting a blanket `exclude_none=True` drop them.
    """

    model_config = ConfigDict(populate_by_name=True, extra='allow')

    category: str
    description: Optional[str] = None
    tangible: Union[int, float] = 0
    intangible: Union[int, float] = 0
    capex_expense: Annotated[Optional[str], Field(alias='capexExpense')] = None
    after_econ_limit: Annotated[Optional[bool], Field(alias='afterEconLimit')] = None
    calculation: Optional[str] = None
    escalation_model: Annotated[Optional[str], Field(alias='escalationModel')] = None
    escalation_start: Annotated[Optional[Dict[str, Any]], Field(alias='escalationStart')] = None
    depreciation_model: Annotated[Optional[str], Field(alias='depreciationModel')] = None
    deal_terms: Annotated[Union[int, float], Field(alias='dealTerms')] = 1


def _escalation_start_to_csv(escalation_start: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    if not escalation_start:
        return '', ''
    if len(escalation_start) != 1:
        raise NotImplementedError(f'Unsupported escalationStart shape: {escalation_start}')
    ((api_key, value),) = escalation_start.items()
    if api_key not in _ESCALATION_START_KEY_TO_CSV:
        raise NotImplementedError(f'Unknown escalationStart key: {api_key!r}')
    return _ESCALATION_START_KEY_TO_CSV[api_key], num_to_csv(value)


def _escalation_start_from_csv(criteria_csv: str, value_csv: str) -> Dict[str, Any]:
    if not criteria_csv:
        return {}
    if criteria_csv not in _ESCALATION_START_KEY_FROM_CSV:
        raise NotImplementedError(f'Unknown Escalation Start Criteria: {criteria_csv!r}')
    api_key = _ESCALATION_START_KEY_FROM_CSV[criteria_csv]
    return {api_key: csv_to_num(value_csv or '0')}


def _detect_criterion(extra: Dict[str, Any]) -> Criteria:
    for criterion in Criteria:
        if criterion.value in extra:
            return criterion
    raise NotImplementedError(f'No recognized capex criterion on row: {extra}')


class CriteriaValueHeaders(NamedTuple):
    """The four CSV cell strings a Capex otherCapex row's single criterion maps to."""

    criteria: str  # 'Criteria' column
    value: str  # 'Value' column
    from_headers: str  # 'From Headers' column (only populated for a fromHeaders row)
    from_schedule: str  # 'From Schedule' column (only populated for a fromSchedule row)


def _criteria_value_headers(extra: Dict[str, Any], criterion: Criteria) -> CriteriaValueHeaders:
    """Returns (Criteria, Value, From Headers, From Schedule) CSV cell strings for the
    row's single criterion."""
    csv_criteria = CRITERIA_TO_CSV[criterion.value]
    if criterion == Criteria.Date:
        return CriteriaValueHeaders(csv_criteria, formats.to_csv_date(extra[criterion.value]), '', '')
    if criterion in (Criteria.FromHeaders, Criteria.FromSchedule):
        token = extra[criterion.value]
        display_map = OFFSET_TO_HEADER_CSV if criterion == Criteria.FromHeaders else OFFSET_TO_SCHEDULE_CSV
        display = display_map.get(token)
        if display is None:
            raise NotImplementedError(f'Unsupported {criterion.value} OffsetTo token: {token!r}')
        companion_key = OFFSET_TO_API_DATEKEY.get(token)
        if companion_key is None:
            raise NotImplementedError(f'No companion API date-key mapped for OffsetTo token: {token!r}')
        value_csv = num_to_csv(extra.get(companion_key, 0))
        if criterion == Criteria.FromHeaders:
            return CriteriaValueHeaders(csv_criteria, value_csv, display, '')
        return CriteriaValueHeaders(csv_criteria, value_csv, '', display)
    return CriteriaValueHeaders(csv_criteria, num_to_csv(extra[criterion.value]), '', '')


def _criteria_from_csv_label(label: str) -> Criteria:
    api_value = CRITERIA_FROM_CSV.get(label)
    if api_value is None:
        raise NotImplementedError(f'Unknown Capex Criteria: {label!r}')
    return Criteria(api_value)


def _criterion_from_csv(row: Dict[str, str]) -> Dict[str, Any]:
    criterion = _criteria_from_csv_label(row.get('Criteria', ''))
    value_cell = row.get('Value', '') or '0'
    if criterion == Criteria.Date:
        return {criterion.value: formats.from_csv_date(row.get('Value', ''))}
    if criterion in (Criteria.FromHeaders, Criteria.FromSchedule):
        column = 'From Headers' if criterion == Criteria.FromHeaders else 'From Schedule'
        offset_from_map = OFFSET_FROM_HEADER_CSV if criterion == Criteria.FromHeaders else OFFSET_FROM_SCHEDULE_CSV
        display = row.get(column, '')
        token = offset_from_map.get(display)
        if token is None:
            raise NotImplementedError(f'Unknown {column} display: {display!r}')
        companion_key = OFFSET_TO_API_DATEKEY.get(token)
        if companion_key is None:
            raise NotImplementedError(f'No companion API date-key mapped for OffsetTo token: {token!r}')
        return {criterion.value: token, companion_key: csv_to_num(value_cell)}
    return {criterion.value: csv_to_num(value_cell)}


def _check_probabilistic(extra: Dict[str, Any]) -> None:
    mismatched = {k: extra[k] for k, default in _PROBABILISTIC_DEFAULTS.items() if k in extra and extra[k] != default}
    if mismatched:
        warnings.warn(
            'Capex row has non-default probabilistic fields with no CSV representation; '
            f'they will not round-trip via from_row_dicts: {mismatched}',
            stacklevel=2,
        )


class CapexMapper(EconModelMapper):
    econ_model_type = 'Capex'
    columns = COLUMNS['Capex']

    def to_row_dicts(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        rows: List[Dict[str, str]] = []
        for r in model.get('otherCapex', {}).get('rows', []):
            rows.append(self._row_to_csv(common, r))
        # Model-level $/ft objects have no native CC column; capture them losslessly as
        # JSON on the FIRST row. If the model carries them but has no otherCapex rows, emit
        # a single carrier row (blank line-item cells, model identity intact) so nothing is
        # dropped -- from_row_dicts skips carrier rows (they have no Criteria).
        drilling_json = _perfoot_to_json(model.get('drillingCost'))
        completion_json = _perfoot_to_json(model.get('completionCost'))
        if drilling_json or completion_json:
            if not rows:
                carrier = {c: '' for c in self.columns}
                carrier.update(common)
                rows.append(carrier)
            rows[0][_DRILLING_COST_COL] = drilling_json
            rows[0][_COMPLETION_COST_COL] = completion_json
        return rows

    def _row_to_csv(self, common: Dict[str, str], r: Dict[str, Any]) -> Dict[str, str]:
        row_model = CapexOtherRow.model_validate(r)
        extra = row_model.model_extra or {}
        _check_probabilistic(extra)
        criterion = _detect_criterion(extra)
        csv_criteria, value_csv, from_headers, from_schedule = _criteria_value_headers(extra, criterion)
        esc_start_criteria, esc_start_value = _escalation_start_to_csv(row_model.escalation_start)
        row = dict(common)
        row.update(
            {
                'Category': enum_to_csv(row_model.category),
                'Description': row_model.description or '',
                'Tangible (M$)': num_to_csv(row_model.tangible),
                'Intangible (M$)': num_to_csv(row_model.intangible),
                'Criteria': csv_criteria,
                'From Schedule': from_schedule,
                'From Headers': from_headers,
                'Value': value_csv,
                'CAPEX or Expense': row_model.capex_expense or '',
                'Appear After Econ Limit': formats.yes_no(row_model.after_econ_limit),
                'Calculation': row_model.calculation or '',
                'Escalation': escalation_to_csv(row_model.escalation_model, title=True),
                'Escalation Start Criteria': esc_start_criteria,
                'Escalation Start Value (Days/Date)': esc_start_value,
                'Depreciation': escalation_to_csv(row_model.depreciation_model, title=True),
                'Paying WI / Earning WI': num_to_csv(row_model.deal_terms),
            }
        )
        return {c: row.get(c, '') for c in self.columns}

    def from_row_dicts(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        name, unique = model_identity(rows)
        other_capex_rows: List[Dict[str, Any]] = []
        drilling: Optional[Dict[str, Any]] = None
        completion: Optional[Dict[str, Any]] = None
        for row in rows:
            if drilling is None:
                drilling = _perfoot_from_json(row.get(_DRILLING_COST_COL, ''))
            if completion is None:
                completion = _perfoot_from_json(row.get(_COMPLETION_COST_COL, ''))
            # A row with no line-item Criteria is a per-foot carrier row (see to_row_dicts),
            # not an otherCapex line item: harvest its JSON above but do not parse it as a
            # row. Real otherCapex rows always carry a Criteria.
            if not (row.get('Criteria') or '').strip():
                continue
            other_capex_rows.append(self._row_from_csv(row))
        model: Dict[str, Any] = {'name': name, 'unique': unique, 'otherCapex': {'rows': other_capex_rows}}
        if drilling is not None:
            model['drillingCost'] = drilling
        if completion is not None:
            model['completionCost'] = completion
        return model

    @staticmethod
    def _row_from_csv(row: Dict[str, str]) -> Dict[str, Any]:
        row_kwargs: Dict[str, Any] = {
            # `enum_from_csv` maps a blank cell to `None`, but `category` is a required
            # API field that's always a (possibly-empty) string on the raw dict form --
            # the `or ''` guard preserves that, matching the original
            # `_category_from_csv` fallback exactly.
            'category': enum_from_csv(row.get('Category', '')) or '',
            'description': row.get('Description') or '',
            'tangible': csv_to_num(row.get('Tangible (M$)') or '0'),
            'intangible': csv_to_num(row.get('Intangible (M$)') or '0'),
            'capex_expense': row.get('CAPEX or Expense') or '',
            'after_econ_limit': formats.parse_yes_no(row.get('Appear After Econ Limit', '')),
            'calculation': row.get('Calculation') or '',
            'escalation_model': escalation_from_csv(row.get('Escalation') or '', title=True),
            'depreciation_model': escalation_from_csv(row.get('Depreciation') or '', title=True),
            'deal_terms': csv_to_num(row.get('Paying WI / Earning WI') or '1'),
        }
        row_kwargs['escalation_start'] = (
            _escalation_start_from_csv(
                row.get('Escalation Start Criteria', ''), row.get('Escalation Start Value (Days/Date)', '')
            )
            or None
        )
        row_kwargs.update(_criterion_from_csv(row))
        row_kwargs.update(_PROBABILISTIC_DEFAULTS)

        row_model = CapexOtherRow(**row_kwargs)
        dumped = row_model.model_dump(by_alias=True, exclude_none=True)
        # escalationModel/depreciationModel must stay present even when None -- see
        # CapexOtherRow docstring.
        dumped['escalationModel'] = row_model.escalation_model
        dumped['depreciationModel'] = row_model.depreciation_model
        return dumped
