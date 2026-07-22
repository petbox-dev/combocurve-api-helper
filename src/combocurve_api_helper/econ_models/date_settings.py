import re
from typing import Annotated, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from . import formats
from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS
from .formats import csv_to_num, enum_from_csv, enum_to_csv, num_to_csv

# API cutOff 'criterion key' -> CSV 'Cut Off Criteria' column value. These are the only 6
# criterion keys that appear. NOT a generic camelCase->spaced transform --
# 'maxCumCashFlow'/'lastPositiveCashFlow'/'firstNegativeCashFlow' render as the SHORTER
# 'max cum'/'last positive'/'first negative' (dropping "cash flow"), while
# 'yearsFromAsOf'/'noCutOff'/'date' happen to equal (or, for 'date', trivially equal) their
# camelCase expansion. Unknown criterion keys (CC's UI may support more Cut Off options) raise
# NotImplementedError rather than being guessed at.
_CUTOFF_CRITERION_TO_CSV = {
    'yearsFromAsOf': 'years from as of',
    'noCutOff': 'no cut off',
    'maxCumCashFlow': 'max cum',
    'lastPositiveCashFlow': 'last positive',
    'date': 'date',
    'firstNegativeCashFlow': 'first negative',
}
_CUTOFF_CRITERION_FROM_CSV = {v: k for k, v in _CUTOFF_CRITERION_TO_CSV.items()}

# Criteria whose Cut Off is driven by cash flow (as opposed to a fixed life/date). ONLY for
# these three criteria does CC's CSV export render 'Include CAPEX', 'Econ Limit Delay', and
# 'Trigger ECL CAPEX (Unecon)' -- for 'years from as of' / 'no cut off' / 'date' those three
# columns are blank EVEN THOUGH the underlying API cutOff object still carries real (non-default)
# values for them. See DateSettingsMapper docstring for the full residual writeup.
_CASHFLOW_CRITERIA = {'maxCumCashFlow', 'lastPositiveCashFlow', 'firstNegativeCashFlow'}

# CSV date-string shape used by 'Cut Off Value' / 'Min Life Value' (when their criterion is
# 'date') and by a date-valued FPD source slot -- always a plain ISO `YYYY-MM-DD`, matching
# `_date_anchor_to_csv`. Used to distinguish a date-shaped label from the 4 known fixed FPD
# source labels on the inverse map (see `_fpd_label_from_csv`).
_ISO_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _flag_or_value_to_csv(value: Any) -> str:
    """Render a cutOff/minLife 'criterion value', which is always one of three shapes: the plain
    flag `True` (blank CSV cell), an ISO `YYYY-MM-DD` date string (criteria 'date' for cutOff,
    'date' for minLife -- rendered UNCHANGED, no reformatting), or a plain number (criteria
    'yearsFromAsOf' for cutOff, 'asOf' for minLife). Shared by both cutOff's own criterion value
    and cutOff.minLife's value, which use the identical shape.
    """
    if value is True:
        return ''
    if isinstance(value, str):
        return value
    return num_to_csv(value)


# API cutOff.minLife 'criterion key' -> CSV 'Min Life Criteria' column value. Three keys appear:
# 'none' (either an explicit `{'none': True}` or `minLife` being ABSENT entirely -- see
# `_min_life_csv`), 'asOf', and 'date' (e.g. cutOff.minLife == {'date': '2027-03-31'}).
# 'none'/'asOf' happen to equal camelCase expansion; 'date' trivially does too. Unknown keys
# raise NotImplementedError.
_MIN_LIFE_CRITERION_TO_CSV = {
    'none': 'none',
    'asOf': 'as of',
    'date': 'date',
}
_MIN_LIFE_CRITERION_FROM_CSV = {v: k for k, v in _MIN_LIFE_CRITERION_TO_CSV.items()}

# API FPD-source key (one of `{firstFpdSource,secondFpdSource,thirdFpdSource,fourthFpdSource}`'s
# single truthy key) -> CSV label. These 4 keys cover the normal case; a slot may instead carry
# a DATE: `{'date': '2021-09-01'}`, rendered on the CSV as the raw date string itself -- see
# `_fpd_label_to_csv`/`_fpd_label_from_csv`. Unknown (non-date-shaped) labels raise
# NotImplementedError.
_FPD_SOURCE_TO_CSV = {
    'wellHeader': 'well header',
    'productionData': 'production data',
    'forecast': 'forecast',
    'notUsed': 'not used',
}
_FPD_SOURCE_FROM_CSV = {v: k for k, v in _FPD_SOURCE_TO_CSV.items()}

# The fixed (non-criterion) keys of a real `cutOff` object -- everything else is the single
# criterion key (see _extract_cutoff_criterion).
_CUTOFF_FIXED_KEYS = {
    'minLife',
    'triggerEclCapex',
    'includeCapex',
    'discount',
    'econLimitDelay',
    'alignDependentPhases',
    'tolerateNegativeCF',
}


def _single_key(d: Dict[str, Any]) -> str:
    keys = list(d)
    if len(keys) != 1:
        raise NotImplementedError(f'Expected exactly one key, got: {keys}')
    return keys[0]


def _extract_cutoff_criterion(cutoff: Dict[str, Any]) -> Tuple[str, Any]:
    crit_keys = [k for k in cutoff if k not in _CUTOFF_FIXED_KEYS]
    if len(crit_keys) != 1:
        raise NotImplementedError(f'Expected exactly one cutOff criterion key, got: {crit_keys}')
    key = crit_keys[0]
    return key, cutoff[key]


def _date_anchor_to_csv(anchor: Dict[str, Any]) -> str:
    """`asOfDate`/`discountDate` shape: the single key `date` holding a plain `YYYY-MM-DD`
    string, rendered on the CSV UNCHANGED (no MM/DD/YYYY reformatting, unlike 'Created At'/'Last
    Update'). CC's schema may support other anchor kinds (e.g. keyed off FPD or a dynamic
    expression), which are not handled here.
    """
    key = _single_key(anchor)
    if key != 'date':
        raise NotImplementedError(f'Unknown DateSettings date-anchor key: {key!r}')
    return str(anchor['date'])


def _date_anchor_from_csv(s: str) -> Dict[str, str]:
    return {'date': s}


def _fpd_label_to_csv(source: Dict[str, Any]) -> str:
    """A source slot is normally a single-key `{<fixed-key>: True}` flag dict (see
    `_FPD_SOURCE_TO_CSV`); the exception is a single-key `{'date': 'YYYY-MM-DD'}` dict, rendered
    as the raw date string itself.
    """
    key = _single_key(source)
    if key == 'date':
        return str(source['date'])
    if key not in _FPD_SOURCE_TO_CSV:
        raise NotImplementedError(f'Unknown DateSettings FPD source key: {key!r}')
    return _FPD_SOURCE_TO_CSV[key]


def _fpd_label_from_csv(label: str) -> Dict[str, Any]:
    if label in _FPD_SOURCE_FROM_CSV:
        return {_FPD_SOURCE_FROM_CSV[label]: True}
    if _ISO_DATE_RE.match(label):
        return {'date': label}
    raise NotImplementedError(f'Unknown DateSettings FPD source label: {label!r}')


class FpdSourceHierarchyData(BaseModel):
    """The `dateSetting.fpdSourceHierarchy` object: four ranked FPD-source slots, each a
    single-key dict, plus a sibling bool. Each slot is normally `{<key>: True}` for one of the 4
    fixed keys in `_FPD_SOURCE_TO_CSV`; a slot may instead be date-valued `{'date': 'YYYY-MM-DD'}`
    (see `_fpd_label_to_csv`) -- hence `Dict[str, Any]` rather than `Dict[str, bool]`.
    """

    model_config = ConfigDict(populate_by_name=True)

    first_fpd_source: Annotated[Dict[str, Any], Field(alias='firstFpdSource')]
    second_fpd_source: Annotated[Dict[str, Any], Field(alias='secondFpdSource')]
    third_fpd_source: Annotated[Dict[str, Any], Field(alias='thirdFpdSource')]
    fourth_fpd_source: Annotated[Dict[str, Any], Field(alias='fourthFpdSource')]
    use_forecast_schedule: Annotated[bool, Field(alias='useForecastSchedule')]


class DateSettingData(BaseModel):
    """The `dateSetting` object on a DateSettings ('Dates') econ model.

    `productionDataResolution` is genuinely ABSENT (not null) on legacy models that pre-date
    the field. Optional + None default reproduces that on `model_dump(exclude_none=True)` and
    lets the forward mapper render those models instead of raising a ValidationError.
    """

    model_config = ConfigDict(populate_by_name=True)

    max_well_life: Annotated[float, Field(alias='maxWellLife')]
    as_of_date: Annotated[Dict[str, Any], Field(alias='asOfDate')]
    discount_date: Annotated[Dict[str, Any], Field(alias='discountDate')]
    cash_flow_prior_as_of_date: Annotated[bool, Field(alias='cashFlowPriorAsOfDate')]
    production_data_resolution: Annotated[Optional[str], Field(alias='productionDataResolution')] = None
    fpd_source_hierarchy: Annotated[FpdSourceHierarchyData, Field(alias='fpdSourceHierarchy')]


class CutOffFixedData(BaseModel):
    """The FIXED (non-criterion) keys of a `cutOff` object. The criterion key itself
    (`yearsFromAsOf`, `noCutOff`, `maxCumCashFlow`, `lastPositiveCashFlow`, `date`,
    `firstNegativeCashFlow`) is extracted separately by `_extract_cutoff_criterion` -- pydantic
    has no clean way to model "exactly one of these N field names is present", and pydantic's
    default (ignore unknown keys) makes validating the full `cutOff` dict directly against this
    model harmless.

    Several fixed keys are genuinely ABSENT (not null) on some legacy models -- schemas that
    pre-date the key, scoped to specific criteria:
      - `minLife`/`triggerEclCapex`/`tolerateNegativeCF`: absent on legacy models across several
        criteria.
      - `discount`: absent on some 'last positive' (lastPositiveCashFlow) models. Never absent
        for any other criterion.
      - `alignDependentPhases`: absent on some 'date' models. Never absent for any other
        criterion.
    `includeCapex`/`econLimitDelay` were not observed absent for any criterion and remain
    required. Optional + None default reproduces the absence on `model_dump(exclude_none=True)`.
    """

    model_config = ConfigDict(populate_by_name=True)

    min_life: Annotated[Optional[Dict[str, Any]], Field(alias='minLife')] = None
    trigger_ecl_capex: Annotated[Optional[bool], Field(alias='triggerEclCapex')] = None
    include_capex: Annotated[bool, Field(alias='includeCapex')]
    discount: Optional[float] = None
    econ_limit_delay: Annotated[float, Field(alias='econLimitDelay')]
    align_dependent_phases: Annotated[Optional[bool], Field(alias='alignDependentPhases')] = None
    tolerate_negative_cf: Annotated[Optional[float], Field(alias='tolerateNegativeCF')] = None


def _cutoff_from_csv(row: Dict[str, str]) -> Dict[str, Any]:
    criteria_csv = row['Cut Off Criteria']
    if criteria_csv not in _CUTOFF_CRITERION_FROM_CSV:
        raise NotImplementedError(f'Unknown DateSettings Cut Off Criteria: {criteria_csv!r}')
    crit_key = _CUTOFF_CRITERION_FROM_CSV[criteria_csv]
    # 'yearsFromAsOf' carries a numeric Cut Off Value; 'date' carries the raw ISO date
    # string unchanged; every other known criterion is a plain flag (True).
    if crit_key == 'yearsFromAsOf':
        crit_value: Any = csv_to_num(row['Cut Off Value'])
    elif crit_key == 'date':
        crit_value = row['Cut Off Value']
    else:
        crit_value = True

    min_life_criteria_csv = row['Min Life Criteria']
    if min_life_criteria_csv not in _MIN_LIFE_CRITERION_FROM_CSV:
        raise NotImplementedError(f'Unknown DateSettings Min Life Criteria: {min_life_criteria_csv!r}')
    min_life_key = _MIN_LIFE_CRITERION_FROM_CSV[min_life_criteria_csv]
    if min_life_key == 'none':
        min_life_value: Any = True
    elif min_life_key == 'date':
        min_life_value = row['Min Life Value']
    else:
        min_life_value = csv_to_num(row['Min Life Value'])

    is_cashflow = crit_key in _CASHFLOW_CRITERIA
    # Documented residual: for non-cash-flow criteria (and Discount under 'last positive' /
    # 'first negative'), CC's CSV never carries these values -- reconstructed as the
    # CC-implied defaults, which do NOT recover the true original API value (see class
    # docstring). 'Tolerant Negative CF' is the one exception: it round-trips exactly for
    # 'first negative' (firstNegativeCashFlow), the only criterion where CC's CSV actually
    # renders it.
    cutoff = CutOffFixedData(
        min_life={min_life_key: min_life_value},
        trigger_ecl_capex=formats.parse_yes_no(row['Trigger ECL CAPEX (Unecon)']) if is_cashflow else False,
        include_capex=formats.parse_yes_no(row['Include CAPEX']) if is_cashflow else False,
        discount=csv_to_num(row['Discount']) if crit_key == 'maxCumCashFlow' else 0,
        econ_limit_delay=csv_to_num(row['Econ Limit Delay']) if is_cashflow else 0,
        align_dependent_phases=formats.parse_yes_no(row['Align Dependent Phases']),
        tolerate_negative_cf=(csv_to_num(row['Tolerant Negative CF']) if crit_key == 'firstNegativeCashFlow' else 0),
    )

    cutoff_dict = cutoff.model_dump(by_alias=True, exclude_none=True)
    cutoff_dict[crit_key] = crit_value
    return cutoff_dict


class DateSettingsMapper:
    """One-row-per-model mapper for the DateSettings ('Dates') econ-model type.

    Like ReservesCategory, there is no `rows[]`/criteria fan-out -- `to_csv_rows` always emits
    exactly ONE row and `from_csv_rows` always consumes exactly ONE row. Unlike ReservesCategory,
    the model has two nested API objects (`dateSetting`, `cutOff`) and THREE independent
    criterion-as-key structures: the `cutOff` criterion itself, `cutOff.minLife`, and each of the
    four `fpdSourceHierarchy` source slots.

    KNOWN RESIDUAL (not a mapper defect): CC's own CSV export renders 'Include CAPEX',
    'Discount', 'Econ Limit Delay', 'Trigger ECL CAPEX (Unecon)', and 'Tolerant Negative CF'
    CONDITIONALLY on the Cut Off Criteria, discarding real underlying values:
      - For 'max cum' (maxCumCashFlow): Include CAPEX/Discount/Econ Limit Delay/Trigger ECL
        CAPEX render; Tolerant Negative CF never does.
      - For 'last positive' (lastPositiveCashFlow): Include CAPEX/Econ Limit Delay/Trigger ECL
        CAPEX render; Discount and Tolerant Negative CF never do (a lastPositiveCashFlow model
        can carry a non-zero `discount`, but the CSV 'Discount' cell is always blank -- and some
        'last positive' models omit `discount` from the API payload entirely, which is why the
        field is Optional on `CutOffFixedData`).
      - For 'first negative' (firstNegativeCashFlow): Include CAPEX/Econ Limit Delay/Trigger ECL
        CAPEX render (same as the other two cash-flow criteria); Discount never renders (like
        'last positive'). UNIQUELY, this is the only criterion where 'Tolerant Negative CF' DOES
        render -- `to_csv_rows`/`from_csv_rows` render/recover this value exactly for this
        criterion only.
      - For 'years from as of' / 'no cut off' / 'date' (non-cash-flow criteria): ALL FIVE render
        blank, even though the API cutOff object may still carry non-default values for some of
        them.
    This means CC's own CSV export is LOSSY for these 5 fields whenever the model's Cut Off
    Criteria is not 'max cum' (Discount) / not 'first negative' (Tolerant Negative CF) / not
    cash-flow-based at all (Include CAPEX/Econ Limit Delay/Trigger ECL CAPEX) -- `from_csv_rows`
    cannot recover the true original values in that case and instead reconstructs the CC-implied
    defaults (False/0). This is a genuine limitation of CC's export, reproduced faithfully rather
    than papered over; see test_date_settings.py for an explicit test documenting it.

    KNOWN RESIDUAL #2 (unexplained, NOT reproduced by this mapper): some 'max cum' models carry
    `cutOff.discount == 10` (a plain Python/JSON int -- no hidden float precision) yet CC's CSV
    renders their 'Discount' cell as `'10.0'` rather than the value-consistent `'10'` that every
    other observed Discount value gets (`0` -> `'0'`, `15` -> `'15'`). No distinguishing signal
    (schema-version key-set, `copiedFrom`, `createdBy`, name pattern) predicts this -- it appears
    tied to the literal value 10 (plausibly a leftover default-value string from an ARIES->CC
    import batch, invisible to this endpoint). This mapper renders all Discount values with plain
    `num_to_csv` rather than special-casing the value `10`, since that would be fitting a
    coincidence, not a derivable rule.

    KNOWN RESIDUAL #3: the 'date' cutOff criterion and the 'date' minLife criterion both carry a
    plain ISO `YYYY-MM-DD` string as their criterion value instead of the flag `True` --
    rendered/parsed as that raw string via `_flag_or_value_to_csv`. Separately, a
    fpdSourceHierarchy slot can be date-valued instead of one of the 4 fixed flag keys; it
    round-trips via `_fpd_label_to_csv`/`_fpd_label_from_csv`, which recognize a bare ISO date
    string as an unambiguous 5th shape (see `_ISO_DATE_RE`).
    """

    econ_model_type = 'DateSettings'
    columns = COLUMNS['DateSettings']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        date_setting = DateSettingData.model_validate(model.get('dateSetting') or {})
        cutoff_raw = model.get('cutOff') or {}
        cutoff = CutOffFixedData.model_validate(cutoff_raw)
        crit_key, crit_value = _extract_cutoff_criterion(cutoff_raw)

        if crit_key not in _CUTOFF_CRITERION_TO_CSV:
            raise NotImplementedError(f'Unknown DateSettings cutOff criterion: {crit_key!r}')
        criteria_csv = _CUTOFF_CRITERION_TO_CSV[crit_key]
        # The criterion's own value is a plain flag (True) for most known criteria, a numeric
        # value for 'yearsFromAsOf', or a raw ISO date string for 'date'.
        cutoff_value_csv = _flag_or_value_to_csv(crit_value)

        min_life_criteria_csv, min_life_value_csv = self._min_life_csv(cutoff.min_life)

        is_cashflow = crit_key in _CASHFLOW_CRITERIA
        include_capex_csv = formats.yes_no(cutoff.include_capex) if is_cashflow else ''
        econ_limit_delay_csv = num_to_csv(cutoff.econ_limit_delay) if is_cashflow else ''
        trigger_ecl_csv = formats.yes_no(cutoff.trigger_ecl_capex or False) if is_cashflow else ''
        # `discount` is Optional (absent on legacy lastPositiveCashFlow models); guard the
        # read so a maxCumCashFlow model that also omits it renders blank instead of
        # crashing in num_to_csv(None) -- mirrors the tolerate_negative_cf guard just below.
        discount_csv = (
            num_to_csv(cutoff.discount) if crit_key == 'maxCumCashFlow' and cutoff.discount is not None else ''
        )
        # 'first negative' (firstNegativeCashFlow) is the ONLY criterion where CC's CSV renders
        # a real 'Tolerant Negative CF' value rather than always leaving it blank (see
        # DateSettingsMapper docstring KNOWN RESIDUAL). Falls back to blank if a future
        # firstNegativeCashFlow model omits tolerateNegativeCF.
        tolerant_negative_csv = (
            num_to_csv(cutoff.tolerate_negative_cf)
            if crit_key == 'firstNegativeCashFlow' and cutoff.tolerate_negative_cf is not None
            else ''
        )

        fh = date_setting.fpd_source_hierarchy
        row = dict(common)
        row.update(
            {
                'Max Econ Life (Years)': num_to_csv(date_setting.max_well_life),
                'As of Date': _date_anchor_to_csv(date_setting.as_of_date),
                'Discount Date': _date_anchor_to_csv(date_setting.discount_date),
                'CF Prior To As Of Date': formats.yes_no(date_setting.cash_flow_prior_as_of_date),
                'Prod Data Resolution': enum_to_csv(date_setting.production_data_resolution),
                '1st FPD Source': _fpd_label_to_csv(fh.first_fpd_source),
                '2nd FPD Source': _fpd_label_to_csv(fh.second_fpd_source),
                '3rd FPD Source': _fpd_label_to_csv(fh.third_fpd_source),
                '4th FPD Source': _fpd_label_to_csv(fh.fourth_fpd_source),
                'Use Forecast/Schedule When No Prod': formats.yes_no(fh.use_forecast_schedule),
                'Cut Off Criteria': criteria_csv,
                'Cut Off Value': cutoff_value_csv,
                'Align Dependent Phases': formats.yes_no(cutoff.align_dependent_phases),
                'Min Life Criteria': min_life_criteria_csv,
                'Min Life Value': min_life_value_csv,
                'Include CAPEX': include_capex_csv,
                'Discount': discount_csv,
                'Econ Limit Delay': econ_limit_delay_csv,
                'Trigger ECL CAPEX (Unecon)': trigger_ecl_csv,
                'Tolerant Negative CF': tolerant_negative_csv,
            }
        )
        return [{c: row.get(c, '') for c in self.columns}]

    @staticmethod
    def _min_life_csv(min_life: Optional[Dict[str, Any]]) -> Tuple[str, str]:
        if min_life is None:
            return 'none', ''
        key = _single_key(min_life)
        if key not in _MIN_LIFE_CRITERION_TO_CSV:
            raise NotImplementedError(f'Unknown DateSettings minLife criterion: {key!r}')
        value = min_life[key]
        return _MIN_LIFE_CRITERION_TO_CSV[key], _flag_or_value_to_csv(value)

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        if len(rows) != 1:
            raise NotImplementedError(f'DateSettings is one-row-per-model; expected exactly 1 CSV row, got {len(rows)}')
        row = rows[0]

        date_setting = DateSettingData(
            max_well_life=csv_to_num(row['Max Econ Life (Years)']),
            as_of_date=_date_anchor_from_csv(row['As of Date']),
            discount_date=_date_anchor_from_csv(row['Discount Date']),
            cash_flow_prior_as_of_date=formats.parse_yes_no(row['CF Prior To As Of Date']),
            production_data_resolution=enum_from_csv(row['Prod Data Resolution']),
            fpd_source_hierarchy=FpdSourceHierarchyData(
                first_fpd_source=_fpd_label_from_csv(row['1st FPD Source']),
                second_fpd_source=_fpd_label_from_csv(row['2nd FPD Source']),
                third_fpd_source=_fpd_label_from_csv(row['3rd FPD Source']),
                fourth_fpd_source=_fpd_label_from_csv(row['4th FPD Source']),
                use_forecast_schedule=formats.parse_yes_no(row['Use Forecast/Schedule When No Prod']),
            ),
        )

        cutoff_dict = _cutoff_from_csv(row)

        name, unique = model_identity(rows)
        return {
            'name': name,
            'unique': unique,
            'dateSetting': date_setting.model_dump(by_alias=True, exclude_none=True),
            'cutOff': cutoff_dict,
        }
