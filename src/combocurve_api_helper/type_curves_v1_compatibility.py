"""Deprecated v1 type-curve behavior kept on the v2 routes for transition.

Kept until at least 2027-01-31, then removed in a 3.x release (docs/todo T1). To remove: delete
this module and put `TypeCurves` back in `ComboCurveAPI`'s bases. Every method here warns once
per call with `_deprecation_message`.
"""

from __future__ import annotations

import copy
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeVar

import requests

from ._deprecation import warn_deprecated
from .base import Item, ItemList, WriteError, WriteResponse
from .type_curve_conversions import (
    PHASES,
    fits_from_v1,
    lookup_table_from_v1,
    lookup_table_id_from_v1,
    lookup_table_uses_v1_fields,
    representative_well_from_v2,
    volumes_to_v1,
)
from .typecurves import TypeCurves

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from requests.structures import CaseInsensitiveDict

# Representative wells carry no timestamps; name then well id. The id key is `wellId`, not `id`.
_REP_WELL_SORT_ORDER: Mapping[str, int] = MappingProxyType({'wellName': 0, 'wellId': 1})
# Forecast outputs take at most 100 `well` values per request (migration guide).
FORECAST_OUTPUTS_WELLS_PER_REQUEST = 100
FORECAST_OUTPUTS_GET_LIMIT = 200
_V1_TYPE_CURVE_ONLY_FIELDS = ('fits', 'regressionType')
_SUCCESS_CODES = (200, 201)
_ResultType = TypeVar('_ResultType')


def _deprecation_message(method_name: str, replacement: str) -> str:
    return (
        f'`{method_name}` is a v1 type-curve method kept for transition; it is removed in a 3.x '
        f'release, not before 2027-01-31. Use {replacement}.'
    )


def _has_v1_type_curve_fields(record: Item) -> bool:
    return any(field in record for field in _V1_TYPE_CURVE_ONLY_FIELDS)


def _error_message(response: requests.Response | None) -> str:
    if response is None:
        return 'no response'
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(payload, dict):
        return str(payload.get('message') or payload)[:500]
    return str(payload)[:500]


def _place_results(
    envelopes: Sequence[WriteResponse],
    positions: Sequence[int],
    results: list[Item | None],
    general_errors: list[WriteError],
) -> None:
    """Put each envelope result back at its input position. A live v2 envelope can lack
    `generalErrors`, hence `.get`."""
    flat_results = [result for envelope in envelopes for result in envelope.get('results', [])]
    for position, result in zip(positions, flat_results):
        results[position] = result
    for envelope in envelopes:
        general_errors.extend(envelope.get('generalErrors', []))


class TypeCurvesV1Compatibility(TypeCurves):
    ###################################
    # Removed v1 reads, kept as wrappers
    ###################################

    def get_type_curve_daily_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Deprecated: the v1 daily fit rows, read from `get_type_curve_volumes(..., 'daily')` and
        given back with `null` for each series v2 leaves out.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-volumes
        """
        warn_deprecated(_deprecation_message('get_type_curve_daily_fits', "get_type_curve_volumes(..., 'daily')"))
        return volumes_to_v1(self.get_type_curve_volumes(project_id, type_curve_id, 'daily'))

    def get_type_curve_monthly_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Deprecated: the v1 monthly fit rows, read from `get_type_curve_volumes(..., 'monthly')`.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-volumes
        """
        warn_deprecated(_deprecation_message('get_type_curve_monthly_fits', "get_type_curve_volumes(..., 'monthly')"))
        return volumes_to_v1(self.get_type_curve_volumes(project_id, type_curve_id, 'monthly'))

    def _forecast_outputs_for_wells(self, project_id: str, forecast_id: str, well_ids: Sequence[str]) -> ItemList:
        """Forecast outputs for `well_ids`, 100 repeated `well` values per request (a comma-joined
        `well` is a 400, live 2026-11-05)."""
        base_url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}/outputs'
        outputs: ItemList = []
        for start in range(0, len(well_ids), FORECAST_OUTPUTS_WELLS_PER_REQUEST):
            chunk = list(well_ids[start : start + FORECAST_OUTPUTS_WELLS_PER_REQUEST])
            url = base_url + self._build_params_string({'well': chunk})
            outputs.extend(self._get_items(url, {'take': FORECAST_OUTPUTS_GET_LIMIT}))
        return outputs

    def get_type_curve_representative_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Deprecated: v1 representative-well rows, built from `get_type_curve_wells` and the type
        curve forecast's outputs (one extra request per 100 wells). `rep` = not excluded and an
        output exists for the phase. `valid` and `hasData` have no v2 source and are left out.
        See `type_curve_conversions.representative_well_from_v2` for the formulas.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-wells
        """
        warn_deprecated(
            _deprecation_message('get_type_curve_representative_fits', 'get_type_curve_wells and forecast outputs')
        )
        type_curve = self.get_type_curve_by_id(project_id, type_curve_id)
        wells = self.get_type_curve_wells(project_id, type_curve_id)
        forecast_id = type_curve.get('forecast')
        outputs = (
            self._forecast_outputs_for_wells(project_id, str(forecast_id), [str(well['id']) for well in wells])
            if forecast_id
            else []
        )
        outputs_by_well_phase = {(str(output.get('well')), str(output.get('phase'))): output for output in outputs}
        forecast_series = str(type_curve.get('forecastSeries') or 'best')
        rows = [
            representative_well_from_v2(
                well,
                {
                    phase: outputs_by_well_phase[(str(well['id']), phase)]
                    for phase in PHASES
                    if (str(well['id']), phase) in outputs_by_well_phase
                },
                forecast_series,
            )
            for well in wells
        ]
        return self._keysort(rows, _REP_WELL_SORT_ORDER)

    ##########################
    # v1-shaped type-curve writes
    ##########################

    def post_type_curves(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates type curves through the v2 batch route. Records with v1 `fits` or `regressionType`
        are deprecated: the type curve is created first, then its fits are written with
        `put_type_curve_fits` (not atomic: a failed fits write leaves the type curve in place and
        reads as a failed result). v1 `normalizations` are not written.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/post-v2-type-curves-batch
        """
        if not any(_has_v1_type_curve_fields(record) for record in data):
            return super().post_type_curves(project_id, data)
        warn_deprecated(
            _deprecation_message('post_type_curves', 'post_type_curves without fits, then put_type_curve_fits')
        )
        return self._write_v1_type_curves(project_id, data, replace_by_name=False)

    def put_type_curves(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Deprecated: v1 upsert by name. Names that exist are merged with `patch_type_curves` (v2
        merges where v1 replaced: a stored field the record leaves out stays); the rest are created.
        v1 `fits` are then written with `put_type_curve_fits`; v1 `normalizations` are not written.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/patch-v2-type-curves-batch
        """
        warn_deprecated(_deprecation_message('put_type_curves', 'patch_type_curves / post_type_curves'))
        return self._write_v1_type_curves(project_id, data, replace_by_name=True)

    def _write_v1_type_curves(self, project_id: str, data: ItemList, replace_by_name: bool) -> list[WriteResponse]:
        fits_bodies = [fits_from_v1(record) if 'fits' in record else None for record in data]
        bodies: ItemList = [
            {field: copy.deepcopy(value) for field, value in record.items() if field not in _V1_TYPE_CURVE_ONLY_FIELDS}
            for record in data
        ]
        update_positions: list[int] = []
        if replace_by_name:
            existing_ids = {
                str(type_curve.get('name')): str(type_curve.get('id'))
                for type_curve in self.get_type_curves(project_id)
            }
            for position, body in enumerate(bodies):
                existing_id = existing_ids.get(str(body.get('name')))
                if existing_id is not None:
                    body['id'] = existing_id
                    update_positions.append(position)
        create_positions = [position for position in range(len(bodies)) if position not in update_positions]

        results: list[Item | None] = [None] * len(bodies)
        general_errors: list[WriteError] = []
        if create_positions:
            envelopes = TypeCurves.post_type_curves(
                self, project_id, [bodies[position] for position in create_positions]
            )
            _place_results(envelopes, create_positions, results, general_errors)
        if update_positions:
            envelopes = self.patch_type_curves(project_id, [bodies[position] for position in update_positions])
            _place_results(envelopes, update_positions, results, general_errors)

        for position, fits in enumerate(fits_bodies):
            result = results[position]
            if fits is None or result is None or result.get('code') not in _SUCCESS_CODES:
                continue
            type_curve_id = str(result.get('id'))
            try:
                self.put_type_curve_fits(project_id, type_curve_id, fits)
            except requests.HTTPError as error:
                status = error.response.status_code if error.response is not None else 0
                results[position] = {
                    'status': 'Error',
                    'code': status,
                    'id': type_curve_id,
                    'errors': [
                        {
                            'name': 'FitsWriteError',
                            'message': _error_message(error.response),
                            'location': f'[{position}].fits',
                        }
                    ],
                }

        present = [result for result in results if result is not None]
        failed_count = sum(1 for result in present if result.get('code') not in _SUCCESS_CODES)
        return [
            WriteResponse(
                successCount=len(present) - failed_count,
                failedCount=failed_count,
                results=present,
                generalErrors=general_errors,
            )
        ]

    ##############################
    # v1-shaped lookup-table input
    ##############################

    def _lookup_tables_in_v2_form(self, method_name: str, tables: Sequence[Item]) -> ItemList:
        if not any(lookup_table_uses_v1_fields(table) for table in tables):
            return list(tables)
        warn_deprecated(
            _deprecation_message(
                method_name,
                'the v2 rule fields (riskFactorPeak*, normalization); v2 rules apply to every phase, '
                'so a v1 rule written for one phase now applies to all phases',
            )
        )
        return [lookup_table_from_v1(table) if lookup_table_uses_v1_fields(table) else table for table in tables]

    def _with_v1_lookup_table_id(
        self, method_name: str, lookup_table_id: str, call: Callable[[str], _ResultType]
    ) -> _ResultType:
        """Call with `lookup_table_id`; on a 404, call once more with the id CC gave the migrated
        v1 table (halves swapped, seen 2 of 2 on 2026-11-05) and warn. A second 404 raises."""
        try:
            return call(lookup_table_id)
        except requests.HTTPError as error:
            if error.response is None or error.response.status_code != 404:
                raise
            try:
                swapped_id = lookup_table_id_from_v1(lookup_table_id)
            except ValueError:
                raise error from None
            result = call(swapped_id)
            warn_deprecated(_deprecation_message(method_name, f'the v2 lookup-table id {swapped_id}'))
            return result

    def post_type_curve_lookup_table(self, project_id: str, data: Item) -> Item:
        """
        Creates one type-curve lookup table; v1 rule fields are translated (deprecated).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/post-v2-type-curve-lookup-table
        """
        table = self._lookup_tables_in_v2_form('post_type_curve_lookup_table', [data])[0]
        return super().post_type_curve_lookup_table(project_id, table)

    def post_type_curve_lookup_tables(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates type-curve lookup tables; v1 rule fields are translated (deprecated).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/post-v2-type-curve-lookup-tables-batch
        """
        tables = self._lookup_tables_in_v2_form('post_type_curve_lookup_tables', data)
        return super().post_type_curve_lookup_tables(project_id, tables)

    def put_type_curve_lookup_tables(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates or replaces type-curve lookup tables by name; v1 rule fields are translated
        (deprecated).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/put-v2-type-curve-lookup-tables-batch
        """
        tables = self._lookup_tables_in_v2_form('put_type_curve_lookup_tables', data)
        return super().put_type_curve_lookup_tables(project_id, tables)

    def get_type_curve_lookup_table_by_id(self, project_id: str, lookup_table_id: str) -> Item:
        """
        Returns one type-curve lookup table. A v1 id falls back to the migrated table's id
        (deprecated).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-lookup-table-by-id
        """
        return self._with_v1_lookup_table_id(
            'get_type_curve_lookup_table_by_id with a v1 lookup-table id',
            lookup_table_id,
            lambda table_id: super(TypeCurvesV1Compatibility, self).get_type_curve_lookup_table_by_id(
                project_id, table_id
            ),
        )

    def put_type_curve_lookup_table_by_id(self, project_id: str, lookup_table_id: str, data: Item) -> Item:
        """
        Replaces one type-curve lookup table. v1 rule fields are translated and a v1 id falls back
        to the migrated table's id (both deprecated).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/put-v2-type-curve-lookup-table-by-id
        """
        table = self._lookup_tables_in_v2_form('put_type_curve_lookup_table_by_id', [data])[0]
        return self._with_v1_lookup_table_id(
            'put_type_curve_lookup_table_by_id with a v1 lookup-table id',
            lookup_table_id,
            lambda table_id: super(TypeCurvesV1Compatibility, self).put_type_curve_lookup_table_by_id(
                project_id, table_id, table
            ),
        )

    def delete_type_curve_lookup_table_by_id(self, project_id: str, lookup_table_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one type-curve lookup table. When nothing matched (`X-Delete-Count: 0`) and the id is
        a v1 id, the migrated table's id is tried once (deprecated).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/delete-v2-type-curve-lookup-table-by-id
        """
        headers = super().delete_type_curve_lookup_table_by_id(project_id, lookup_table_id)
        if headers.get('X-Delete-Count') != '0':
            return headers
        try:
            swapped_id = lookup_table_id_from_v1(lookup_table_id)
        except ValueError:
            return headers
        swapped_headers = super().delete_type_curve_lookup_table_by_id(project_id, swapped_id)
        if swapped_headers.get('X-Delete-Count') not in (None, '0'):
            warn_deprecated(
                _deprecation_message(
                    'delete_type_curve_lookup_table_by_id with a v1 lookup-table id',
                    f'the v2 lookup-table id {swapped_id}',
                )
            )
        return swapped_headers
