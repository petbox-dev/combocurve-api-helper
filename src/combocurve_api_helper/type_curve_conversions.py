"""Pure conversions between ComboCurve's v1 and v2 type-curve payloads, and helpers that make a v2
read body safe to write back. No network.

Every function returns a new object and never changes its input. Behavior verified live on
2026-11-05 is stated per function.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import date
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .base import Item, ItemList

PHASES: tuple[str, str, str] = ('oil', 'gas', 'water')
SERIES: tuple[str, str, str, str] = ('best', 'p10', 'p50', 'p90')

# v1 fit-phase fields with no v2 source. v2 rejects `regressionType` on a fit phase
# (`400 FieldNameError`, live 2026-11-05), although its schema lists it as required.
_V1_ONLY_FIT_FIELDS = ('resolution', 'align', 'normalize', 'normalizations', 'regressionType')


def _as_item(value: object) -> Item | None:
    """`value` as an object, or None when it is not one."""
    return cast('Item', value) if isinstance(value, dict) else None


def _as_item_list(value: object) -> ItemList:
    """The objects in `value` when it is a list, else an empty list."""
    if not isinstance(value, list):
        return []
    return [cast('Item', element) for element in value if isinstance(element, dict)]


def _series_segment_lists(phase_fit: Item) -> list[ItemList]:
    """Every `segments` list of a phase fit: the rate series, then the ratio series."""
    holders = [_as_item(phase_fit.get(series)) for series in SERIES]
    ratio = _as_item(phase_fit.get('ratio'))
    if ratio is not None:
        holders += [_as_item(ratio.get(series)) for series in SERIES]
    return [_as_item_list(holder.get('segments')) for holder in holders if holder is not None]


def _linear_slope_value(segment: Item) -> float | None:
    """`(qEnd - qStart) / days` for a segment that carries both rates and both dates, else None."""
    rate_start, rate_end = segment.get('qStart'), segment.get('qEnd')
    start_date, end_date = segment.get('startDate'), segment.get('endDate')
    if not isinstance(rate_start, (int, float)) or not isinstance(rate_end, (int, float)):
        return None
    if not isinstance(start_date, str) or not isinstance(end_date, str):
        return None
    days = (date.fromisoformat(end_date[:10]) - date.fromisoformat(start_date[:10])).days
    if days <= 0:
        return None
    return (rate_end - rate_start) / days


def fits_for_put(fits: Item) -> Item:
    """A v2 `GET /fits` body made safe for `PUT /fits`.

    v2 returns a `linear` segment's `slope` as its sign (-1/0/1) but reads `slope` on write as
    the value and ignores `qEnd`, so a read-back segment written verbatim stores a different
    curve (live 2026-11-05: `qStart 500`, `qEnd 400`, 364 days, `slope -1` stored `qEnd 136`).
    This recomputes `slope = (qEnd - qStart) / days` on every `linear` segment that has both
    rates and both dates, and drops the read-only `updatedAt` of each phase. Other segments pass
    unchanged.
    """
    writable = copy.deepcopy(fits)
    for phase in PHASES:
        phase_fit = _as_item(writable.get(phase))
        if phase_fit is None:
            continue
        phase_fit.pop('updatedAt', None)
        for segments in _series_segment_lists(phase_fit):
            for segment in segments:
                if segment.get('segmentType') != 'linear':
                    continue
                slope_value = _linear_slope_value(segment)
                if slope_value is not None:
                    segment['slope'] = slope_value
    return writable


def normalization_for_put(normalization: Item) -> Item:
    """A v2 `GET /normalization` body made acceptable to `PUT /normalization`.

    Drops `aValue`/`bValue` on `1_to_1` segments (GET returns `aValue 1, bValue 0` on migrated
    curves; PUT refuses them, live 2026-11-05) and drops `xAxis` when `customBasisKey` is set
    (documented: GET returns a composite ratio there that PUT refuses).
    """
    writable = copy.deepcopy(normalization)
    for phase in PHASES:
        phase_configuration = _as_item(writable.get(phase))
        if phase_configuration is None:
            continue
        if phase_configuration.get('customBasisKey'):
            phase_configuration.pop('xAxis', None)
        for factor in ('eur', 'peak'):
            factor_configuration = _as_item(phase_configuration.get(factor))
            if factor_configuration is None:
                continue
            for segment in _as_item_list(factor_configuration.get('segments')):
                if segment.get('fitType') == '1_to_1':
                    segment.pop('aValue', None)
                    segment.pop('bValue', None)
    return writable


def _ratio_fit_from_v1(phase: str, phase_fit_v1: Item) -> Item | None:
    """A v1 ratio phase fit as a v2 phase fit, or None when it has no series."""
    ratio_v1 = _as_item(phase_fit_v1.get('ratio')) or {}
    series_v1 = {series: holder for series in SERIES if (holder := _as_item(ratio_v1.get(series))) is not None}
    if not series_v1:
        return None
    base_phases = sorted({str(holder.get('basePhase')) for holder in series_v1.values() if holder.get('basePhase')})
    if len(base_phases) != 1:
        raise ValueError(f'{phase}: the v1 ratio series name base phases {base_phases}; v2 takes one `ratio.basePhase`')
    ratio_v2: Item = {'basePhase': base_phases[0]}
    for series, holder in series_v1.items():
        ratio_v2[series] = {'segments': copy.deepcopy(_as_item_list(holder.get('segments')))}
    return {'fitType': 'ratio', 'eurPercentileMatched': False, 'ratio': ratio_v2}


def _rate_fit_from_v1(phase_fit_v1: Item) -> Item | None:
    """A v1 rate phase fit as a v2 phase fit, or None for v1's unfitted-phase stub."""
    phase_fit_v2: Item = {'fitType': 'rate', 'eurPercentileMatched': False}
    for series in SERIES:
        holder = _as_item(phase_fit_v1.get(series))
        segments = _as_item_list(holder.get('segments')) if holder is not None else []
        if segments:
            phase_fit_v2[series] = {'segments': copy.deepcopy(segments)}
    return phase_fit_v2 if len(phase_fit_v2) > 2 else None


def fits_from_v1(type_curve_v1: Item) -> Item:
    """The `fits` of a v1 type curve as a v2 `PUT /fits` body.

    v1 `type` becomes `fitType`; `eurPercentileMatched` is `false` (CC's migration wrote `false`,
    live 2026-11-05); `resolution`, `align`, `normalize`, `normalizations` and `regressionType` are
    dropped (no v2 field; v2 rejects `regressionType`). A v1 ratio carries `basePhase` in each
    series, v2 one `ratio.basePhase`: the same value everywhere becomes that value, different values
    raise `ValueError`. A phase with no series (v1's stub for an unfitted phase) is left out. Accepts
    the v1 read form and write form of a segment; `linear` slopes go through `fits_for_put`.
    """
    fits_v1 = _as_item(type_curve_v1.get('fits')) or {}
    fits_v2: Item = {}
    for phase in PHASES:
        phase_fit_v1 = _as_item(fits_v1.get(phase))
        if phase_fit_v1 is None:
            continue
        fit_type = phase_fit_v1.get('type', phase_fit_v1.get('fitType', 'rate'))
        if fit_type == 'ratio':
            phase_fit_v2 = _ratio_fit_from_v1(phase, phase_fit_v1)
        else:
            phase_fit_v2 = _rate_fit_from_v1(phase_fit_v1)
        if phase_fit_v2 is not None:
            fits_v2[phase] = phase_fit_v2
    return fits_for_put(fits_v2)


def fits_to_v1(fits_v2: Item) -> Item:
    """A v2 `GET /fits` body in the v1 `fits` shape.

    `fitType` becomes `type`; the single `ratio.basePhase` is copied into each ratio series. v1's
    `resolution`, `align`, `normalize`, `normalizations` and its top-level `regressionType` have no
    v2 source and are left out. `slope` is copied unchanged: v1 also returned the sign on read.
    """
    fits_v1: Item = {}
    for phase in PHASES:
        phase_fit_v2 = _as_item(fits_v2.get(phase))
        if phase_fit_v2 is None:
            continue
        phase_fit_v1: Item = {'type': phase_fit_v2.get('fitType', 'rate')}
        for series in SERIES:
            if series in phase_fit_v2:
                phase_fit_v1[series] = copy.deepcopy(phase_fit_v2[series])
        ratio_v2 = _as_item(phase_fit_v2.get('ratio'))
        if ratio_v2 is not None:
            ratio_v1: Item = {}
            for series in SERIES:
                holder = _as_item(ratio_v2.get(series))
                if holder is not None:
                    ratio_v1[series] = {
                        'segments': copy.deepcopy(_as_item_list(holder.get('segments'))),
                        'basePhase': ratio_v2.get('basePhase'),
                    }
            phase_fit_v1['ratio'] = ratio_v1
        fits_v1[phase] = phase_fit_v1
    return fits_v1


_V1_TYPE_CURVE_FIELDS = ('id', 'name', 'forecast', 'wells', 'createdAt', 'updatedAt')


def type_curve_to_v1(type_curve_v2: Item, fits_v2: Item) -> Item:
    """A v2 type curve and its v2 fits in the v1 `get_type_curves` row shape (fits embedded).

    v1's top-level `regressionType` has no v2 source and is left out.
    """
    type_curve_v1: Item = {
        field: copy.deepcopy(type_curve_v2[field]) for field in _V1_TYPE_CURVE_FIELDS if field in type_curve_v2
    }
    type_curve_v1['fits'] = fits_to_v1(fits_v2)
    return type_curve_v1


def volumes_to_v1(volume_rows: ItemList) -> ItemList:
    """v2 volume rows in the v1 daily/monthly fit row shape.

    v2 leaves out a series with no fit and a phase with no fitted series; v1 returned `null` for
    each. Values and dates are otherwise identical (live 2026-11-05: 200 monthly rows, 0 differences).
    """
    rows_v1: ItemList = []
    for row in volume_rows:
        row_v1: Item = {'date': row.get('date')}
        for phase in PHASES:
            values = _as_item(row.get(phase)) or {}
            row_v1[phase] = {series: values.get(series) for series in SERIES}
        rows_v1.append(row_v1)
    return rows_v1


_V1_RISK_FACTOR_FIELDS = {
    'riskFactorOil': 'riskFactorPeakOil',
    'riskFactorGas': 'riskFactorPeakGas',
    'riskFactorWater': 'riskFactorPeakWater',
}
_V1_ONLY_RULE_FIELDS = (*_V1_RISK_FACTOR_FIELDS, 'applyNormalization', 'phase', 'resolution')
_OBJECT_ID = re.compile(r'^[0-9a-f]{24}$')


def lookup_table_uses_v1_fields(table: Item) -> bool:
    """True when any rule of `table` carries a field that v2 removed or renamed."""
    return any(field in rule for rule in _as_item_list(table.get('rules')) for field in _V1_ONLY_RULE_FIELDS)


def _rule_from_v1(rule: Item) -> Item:
    """One v1 rule with v2 field names; `phase` and `resolution` dropped."""
    if rule.get('fpdSource') == 'schedule':
        raise ValueError("fpdSource 'schedule' has no v2 equivalent; use another source, or 'fixed' with fixedDate")
    converted: Item = {
        field: copy.deepcopy(value) for field, value in rule.items() if field not in _V1_ONLY_RULE_FIELDS
    }
    for v1_field, v2_field in _V1_RISK_FACTOR_FIELDS.items():
        if v1_field in rule:
            converted[v2_field] = copy.deepcopy(rule[v1_field])
    if rule.get('applyNormalization') is True:
        converted['normalization'] = {'source': 'own'}
    return converted


def lookup_table_from_v1(table: Item) -> Item:
    """A v1 lookup table with v2 rule fields.

    `riskFactorOil/Gas/Water` become `riskFactorPeak*`; `applyNormalization: true` becomes
    `normalization: {'source': 'own'}` (false or absent: no `normalization`); `resolution` is
    dropped. v2 rules apply to every phase, so rules with the same filter that differ only by
    `phase` collapse to the first; rules with the same filter that differ in anything else raise
    `ValueError` naming the filter, because merging them would change which type curve a well gets.
    `fpdSource: 'schedule'` raises `ValueError` (no v2 equivalent).
    """
    rules_v2: ItemList = []
    rule_by_phased_filter: dict[str, Item] = {}
    for rule in _as_item_list(table.get('rules')):
        converted = _rule_from_v1(rule)
        if 'phase' not in rule:
            rules_v2.append(converted)
            continue
        filter_key = json.dumps(rule.get('filter'), sort_keys=True)
        earlier = rule_by_phased_filter.get(filter_key)
        if earlier is None:
            rule_by_phased_filter[filter_key] = converted
            rules_v2.append(converted)
        elif earlier != converted:
            raise ValueError(
                f'rules for filter {filter_key} differ by phase; v2 rules apply to every phase, '
                'so they cannot be merged without changing which type curve a well gets'
            )
    table_v2: Item = {field: copy.deepcopy(value) for field, value in table.items() if field != 'rules'}
    table_v2['rules'] = rules_v2
    return table_v2


def lookup_table_to_v1(table: Item) -> Item:
    """A v2 lookup table with v1 rule fields. `normalization.source == 'shared'` has no v1 form:
    `ValueError`."""
    v2_to_v1 = {v2_field: v1_field for v1_field, v2_field in _V1_RISK_FACTOR_FIELDS.items()}
    rules_v1: ItemList = []
    for rule in _as_item_list(table.get('rules')):
        converted: Item = {}
        for field, value in rule.items():
            if field == 'normalization':
                normalization = _as_item(value) or {}
                if normalization.get('source') != 'own':
                    raise ValueError(f'normalization source {normalization.get("source")!r} (shared) has no v1 form')
                converted['applyNormalization'] = True
            else:
                converted[v2_to_v1.get(field, field)] = copy.deepcopy(value)
        rules_v1.append(converted)
    table_v1: Item = {field: copy.deepcopy(value) for field, value in table.items() if field != 'rules'}
    table_v1['rules'] = rules_v1
    return table_v1


def lookup_table_id_from_v1(lookup_table_id: str) -> str:
    """The v2 id CC gave a migrated v1 lookup table: the two 12-hex halves swapped.

    Seen on 2 of 2 tables before the switch-over (2026-11-05); CC does not document it.
    """
    if not _OBJECT_ID.match(lookup_table_id):
        raise ValueError(f'{lookup_table_id!r} is not a 24-character hex ObjectId')
    return lookup_table_id[12:] + lookup_table_id[:12]


def _representative_phase_from_output(output: Item, excluded: bool, length: object, series: str) -> Item:
    """One phase block of a v1 representative-well row from that phase's forecast output."""
    phase_row: Item = {'rep': not excluded, 'hasForecast': True}
    forecast_type = output.get('forecastType')
    ratio = _as_item(output.get('ratio'))
    series_output = ratio if forecast_type == 'ratio' and ratio is not None else _as_item(output.get(series))
    output_eur = series_output.get('eur') if series_output is not None else None
    if isinstance(output_eur, (int, float)):
        phase_row['eur'] = output_eur / 1000
        if isinstance(length, (int, float)) and length:
            phase_row['eurPll'] = output_eur / length
    parts = [forecast_type, output.get('forecastSubType')]
    if forecast_type == 'ratio' and ratio is not None:
        parts.append(ratio.get('basePhase'))
    phase_row['forecastType'] = ';'.join(str(part) for part in parts if part not in (None, ''))
    if 'data_freq' in output:
        phase_row['dataFrequency'] = output['data_freq']
    return phase_row


def representative_well_from_v2(well_row: Item, outputs_by_phase: Mapping[str, Item], forecast_series: str) -> Item:
    """A v1 representative-well row from a v2 `/wells` row and that well's forecast outputs.

    Verified against v1 on 2026-11-05 for `best` (3 wells x 3 phases, exact): `eur` = output
    `<series>.eur / 1000`; `eurPll` = output `<series>.eur / perfLateralLength` (not divided by
    1000; left out when the length is absent or zero); `forecastType` = `forecastType;forecastSubType`,
    plus `;basePhase` for a ratio output (`ratio.eur` is read). A phase with no output reads as v1
    gave it: `eur 0`, `eurPll 0`, `not_forecasted`, `hasForecast false`, `rep false`. `valid`,
    `hasData` and (with no output) `dataFrequency` have no v2 source and are left out.
    """
    excluded = well_row.get('excluded') is True
    length = well_row.get('perfLateralLength')
    series = forecast_series.lower()
    row: Item = {
        'api14': well_row.get('api14'),
        'wellName': well_row.get('wellName'),
        'wellNumber': well_row.get('wellNumber'),
        'wellId': well_row.get('id'),
        'chosenID': well_row.get('chosenID'),
    }
    for phase in PHASES:
        output = outputs_by_phase.get(phase)
        if output is None:
            row[phase] = {'eur': 0, 'eurPll': 0, 'forecastType': 'not_forecasted', 'hasForecast': False, 'rep': False}
        else:
            row[phase] = _representative_phase_from_output(output, excluded, length, series)
    return row
