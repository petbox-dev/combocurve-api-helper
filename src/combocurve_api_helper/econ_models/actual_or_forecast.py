from typing import Annotated, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .base import Context, common_columns, model_identity
from .csv_columns import COLUMNS

# CC always emits exactly 3 rows per model, in this order (verified live, project Sample Project A: 18/18 models each render as exactly 3 rows, Key=oil/gas/water).
_PHASES: Tuple[str, str, str] = ('oil', 'gas', 'water')

# The econ-model type's two fixed, non-deletable built-in model names (every project
# has exactly one of each) -- ported from cc-afe-sync's
# `models/actual_or_forecast.py` ACTUAL_OR_FORECAST_ASSIGNMENTS, which hardcodes these
# same two names as the only valid qualifier-slot assignments for this type.
_MODEL_NAME_ACTUAL = 'Actual'
_MODEL_NAME_FORECAST_AS_OF = 'Forecast As Of'

_CRITERIA_DATE = 'Date'
_CRITERIA_NEVER = 'Never'
_CRITERIA_AS_OF_DATE = 'As of Date'


class PhaseSwitchData(BaseModel):
    """One `replaceActualWithForecast[phase]` node of the real ActualOrForecast API
    shape.

    Verified live (project Sample Project A) and cross-checked against a
    broader scan of ~380 ActualOrForecast models across 80 projects: exactly one of
    `date`/`never`/`as_of_date` is ever populated on an explicit (migrated) node --

    - `{"date": "2026-03-31"}` -- switch on a fixed date (ISO string, passed through
      unchanged -- NOT reformatted to MM/DD/YYYY).
    - `{"never": true}` -- never switch (explicit modern form of the built-in
      'Actual' model's default).
    - `{"asOfDate": true}` -- switch as of the project's Dates-settings "As of Date"
      (explicit modern form of the built-in 'Forecast As Of' model's default).

    A genuinely empty node (`{}`), or the phase key entirely absent from
    `replaceActualWithForecast`, or `replaceActualWithForecast` itself absent (whole
    `actualOrForecast` == `{}` or only carries `ignoreHistoryProd`) is the
    legacy/unset representation and is resolved by `_phase_criteria` via the fixed
    model name instead. `extra='forbid'` so any future/unrecognized key raises
    loudly (converted to `NotImplementedError` by the mapper) rather than being
    silently dropped.
    """

    model_config = ConfigDict(populate_by_name=True, extra='forbid')

    date: Optional[str] = None
    never: Optional[bool] = None
    as_of_date: Annotated[Optional[bool], Field(alias='asOfDate')] = None


def _phase_criteria(data: PhaseSwitchData, model_name: str) -> Tuple[str, str]:
    if data.date is not None:
        return _CRITERIA_DATE, data.date
    if data.never is True:
        return _CRITERIA_NEVER, ''
    if data.as_of_date is True:
        return _CRITERIA_AS_OF_DATE, ''
    # No explicit marker -- legacy `{}`/absent-phase representation (verified live:
    # project Sample Project A' 'Actual' and 'Forecast As Of' models are both
    # still `actualOrForecast: {}` as of this writing, never migrated to the
    # explicit per-phase shape). CC's front end resolves this via the model's fixed,
    # non-deletable built-in name: 'Forecast As Of' always means "replace with
    # forecast as of the project's As Of Date" even when unmigrated/empty; every
    # other model (including the other built-in, 'Actual', and ordinary
    # user-created models such as 'Ignore History' whose `actualOrForecast` carries
    # only `ignoreHistoryProd`) defaults to Never.
    if model_name == _MODEL_NAME_FORECAST_AS_OF:
        return _CRITERIA_AS_OF_DATE, ''
    return _CRITERIA_NEVER, ''


class ActualOrForecastMapper:
    econ_model_type = 'ActualOrForecast'
    columns = COLUMNS['ActualOrForecast']

    def to_csv_rows(self, model: Dict[str, Any], context: Optional[Context] = None) -> List[Dict[str, str]]:
        common = common_columns(model, context)
        model_name = model.get('name', '') or ''
        aof = model.get('actualOrForecast') or {}
        rwf = aof.get('replaceActualWithForecast') or {}

        rows: List[Dict[str, str]] = []
        for phase in _PHASES:
            try:
                data = PhaseSwitchData.model_validate(rwf.get(phase) or {})
            except ValidationError as e:
                raise NotImplementedError(
                    f'Unknown ActualOrForecast replaceActualWithForecast[{phase!r}] shape: {rwf.get(phase)!r}'
                ) from e
            criteria, value = _phase_criteria(data, model_name)
            row = dict(common)
            row.update(
                {
                    'Key': phase,
                    'Category': '',
                    'Criteria': criteria,
                    'Value': value,
                }
            )
            rows.append({c: row.get(c, '') for c in self.columns})
        return rows

    def from_csv_rows(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        if len(rows) != 3:
            raise NotImplementedError(
                f'ActualOrForecast is 3-rows-per-model (oil/gas/water); expected exactly 3 CSV rows, got {len(rows)}'
            )
        by_phase = {row['Key']: row for row in rows}
        missing = [p for p in _PHASES if p not in by_phase]
        if missing:
            raise NotImplementedError(f'ActualOrForecast missing required phase row(s): {missing}')

        # Only rows[0] feeds identity -- not all `rows` -- matching this type's original
        # exact behavior (every row of a real model carries the identical 'Model Name'/
        # 'Model Type', but `from_csv_rows` has never depended on that for the other two
        # rows).
        name, unique = model_identity([rows[0]])

        phase_shapes: Dict[str, Dict[str, Any]] = {}
        for phase in _PHASES:
            criteria = by_phase[phase]['Criteria']
            if criteria == _CRITERIA_DATE:
                phase_shapes[phase] = {'date': by_phase[phase]['Value']}
            elif criteria == _CRITERIA_NEVER:
                phase_shapes[phase] = {'never': True}
            elif criteria == _CRITERIA_AS_OF_DATE:
                phase_shapes[phase] = {'asOfDate': True}
            else:
                raise NotImplementedError(f'Unknown ActualOrForecast Criteria: {criteria!r}')

        all_never = all(by_phase[p]['Criteria'] == _CRITERIA_NEVER for p in _PHASES)
        # `ignoreHistoryProd` has NO CSV column: it is dropped on the forward
        # (API->CSV) pass and is NOT recoverable here -- documented limitation. Two
        # real models differing only by `ignoreHistoryProd` (e.g. `{}` vs
        # `{"ignoreHistoryProd": true}`) render identical CSV rows and reconstruct
        # to the same shape below.
        #
        # When every phase is Never AND the model is not the built-in
        # 'Forecast As Of', reproduce CC's real legacy/default empty shape
        # (`actualOrForecast: {}`) exactly -- verified live on project Sample Project A ('Actual' and ordinary Never-only models alike are `{}`-shaped or
        # carry only `ignoreHistoryProd`, never an explicit per-phase `never` node).
        # Collapsing to `{}` for a model literally named 'Forecast As Of' would
        # silently flip back to 'As of Date' on the next `to_csv_rows` pass (see
        # `_phase_criteria`'s name-based fallback) -- a round-trip break -- so that
        # one case keeps the explicit modern per-phase shape instead.
        if all_never and name != _MODEL_NAME_FORECAST_AS_OF:
            actual_or_forecast: Dict[str, Any] = {}
        else:
            actual_or_forecast = {
                'ignoreHistoryProd': False,
                'replaceActualWithForecast': phase_shapes,
            }

        return {
            'name': name,
            'unique': unique,
            'actualOrForecast': actual_or_forecast,
        }


# Re-exported for tests/documentation of the two fixed built-in model names.
BUILTIN_MODEL_NAMES: Tuple[str, str] = (_MODEL_NAME_ACTUAL, _MODEL_NAME_FORECAST_AS_OF)
