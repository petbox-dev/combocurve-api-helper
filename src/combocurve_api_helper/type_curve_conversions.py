"""Pure conversions between ComboCurve's v1 and v2 type-curve payloads, and helpers that make a v2
read body safe to write back. No network.

Every function returns a new object and never changes its input. Behavior verified live on
2026-11-05 is stated per function.
"""

from __future__ import annotations

import copy
from datetime import date
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
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
