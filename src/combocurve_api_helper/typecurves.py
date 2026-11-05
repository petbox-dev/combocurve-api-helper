"""ComboCurve Type Curve 2.0: `/v2/projects/{projectId}/type-curves` and its lookup tables.

ComboCurve turned the v1 type-curve routes off on 2026-11-07. Behavior verified live on
2026-11-05 is noted per method. The deprecated v1 methods and v1-shaped inputs are handled in
`type_curves_v1_compatibility.py`; payload conversions are in `type_curve_conversions.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import requests
from requests.structures import CaseInsensitiveDict

from .base import LIST_SORT_ORDER, WELL_LIST_SORT_ORDER, APIBase, Item, ItemList, WriteResponse

if TYPE_CHECKING:
    from collections.abc import Sequence

Phase = Literal['oil', 'gas', 'water']
Resolution = Literal['daily', 'monthly']

# `take` limits enforced by the server (live 2026-11-05): lookup tables 200, wells 1,000; the
# type-curve list and volumes accept 2,500 although their schemas say 200.
GET_LIMIT = 200
WELLS_GET_LIMIT = 1000
VOLUMES_GET_LIMIT = 2500
# Batch routes: at most 100 type curves, 500 lookup tables per request.
TYPE_CURVE_BATCH_LIMIT = 100
LOOKUP_TABLE_BATCH_LIMIT = 500


def _error_name(response: requests.Response | None) -> str | None:
    """The `name` field of a JSON error body, or None."""
    if response is None:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    name = payload.get('name') if isinstance(payload, dict) else None
    return name if isinstance(name, str) else None


class TypeCurves(APIBase):
    ######
    # URLs
    ######

    def get_type_curves_url(self, project_id: str, filters: dict[str, str] | None = None) -> str:
        """Returns the v2 API url of the type curves of a project."""
        return f'{self.API_BASE_URL_V2}/projects/{project_id}/type-curves' + self._build_params_string(filters)

    def get_type_curves_batch_url(self, project_id: str) -> str:
        """Returns the v2 API url of the type-curve batch route of a project."""
        return f'{self.get_type_curves_url(project_id)}/batch'

    def get_type_curve_by_id_url(self, project_id: str, type_curve_id: str) -> str:
        """Returns the v2 API url of one type curve."""
        return f'{self.get_type_curves_url(project_id)}/{type_curve_id}'

    def get_type_curve_fits_url(
        self, project_id: str, type_curve_id: str, phases: Sequence[Phase] | None = None
    ) -> str:
        """Returns the v2 API url of a type curve's fits; `phases` repeats `?phase=`."""
        url = f'{self.get_type_curve_by_id_url(project_id, type_curve_id)}/fits'
        return url + self._build_params_string({'phase': list(phases)} if phases else None)

    def get_type_curve_normalization_url(
        self, project_id: str, type_curve_id: str, phases: Sequence[Phase] | None = None
    ) -> str:
        """Returns the v2 API url of a type curve's normalization; `phases` repeats `?phase=`."""
        url = f'{self.get_type_curve_by_id_url(project_id, type_curve_id)}/normalization'
        return url + self._build_params_string({'phase': list(phases)} if phases else None)

    def get_type_curve_volumes_url(self, project_id: str, type_curve_id: str) -> str:
        """Returns the v2 API url of a type curve's volumes (`resolution` is sent as a param)."""
        return f'{self.get_type_curve_by_id_url(project_id, type_curve_id)}/volumes'

    def get_type_curve_wells_url(
        self, project_id: str, type_curve_id: str, filters: dict[str, str] | None = None
    ) -> str:
        """Returns the v2 API url of the wells assigned to a type curve."""
        url = f'{self.get_type_curve_by_id_url(project_id, type_curve_id)}/wells'
        return url + self._build_params_string(filters)

    ##########
    # Plumbing
    ##########

    def _request_one_item(self, method: str, url: str, body: Item | None = None) -> Item:
        """Send one request whose response body is one JSON object; `{}` for an empty body."""
        response = self._request_with_retry(method, url, json_body=body)
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError:
            return {}
        return cast('Item', payload) if isinstance(payload, dict) else {}

    ###########
    # API calls
    ###########

    def get_type_curves(self, project_id: str, filters: dict[str, str] | None = None) -> ItemList:
        """
        Returns the type curves of a project. Fits and normalization are not embedded (v1
        embedded `fits`); read them with `get_type_curve_fits` / `get_type_curve_normalization`.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curves
        """
        type_curves = self._get_items(self.get_type_curves_url(project_id, filters), {'take': GET_LIMIT})
        return self._keysort(type_curves, LIST_SORT_ORDER)

    def count_type_curves(self, project_id: str, filters: dict[str, str] | None = None) -> int:
        """
        Returns the number of type curves matching `filters`, from the HEAD route's `X-Query-Count`.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/head-v2-type-curves
        """
        return self._count_items(self.get_type_curves_url(project_id, filters))

    def get_type_curve_by_id(self, project_id: str, type_curve_id: str) -> Item:
        """
        Returns one type curve. Type-curve ids did not change in the v1 -> v2 migration.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-by-id
        """
        return self._request_one_item('get', self.get_type_curve_by_id_url(project_id, type_curve_id))

    def post_type_curve(self, project_id: str, data: Item) -> Item:
        """
        Creates one type curve and returns it as stored (201). A used name is a 409. Write fits
        afterwards with `put_type_curve_fits`.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/post-v2-type-curve
        """
        return self._request_one_item('post', self.get_type_curves_url(project_id), data)

    def post_type_curves(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates type curves through the batch route, at most 100 per request; one 207 envelope per
        request. A failed record reads `status: "Error"` with its own `code` (409 for a used name).

        https://docs.api.combocurve.com/api/type-curves-v2-preview/post-v2-type-curves-batch
        """
        url = self.get_type_curves_batch_url(project_id)
        return cast('list[WriteResponse]', self._post_items(url, data, chunksize=TYPE_CURVE_BATCH_LIMIT))

    def patch_type_curve(self, project_id: str, type_curve_id: str, data: Item) -> Item:
        """
        Merges `data` into one type curve and returns it as stored. Omitted fields stay; `null` is
        ignored, so a field cannot be cleared.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/patch-v2-type-curve
        """
        return self._request_one_item('patch', self.get_type_curve_by_id_url(project_id, type_curve_id), data)

    def patch_type_curves(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Merges each record into the type curve its `id` names, at most 100 per request. Does not
        create: an unknown `id` is a per-record 404.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/patch-v2-type-curves-batch
        """
        url = self.get_type_curves_batch_url(project_id)
        return cast('list[WriteResponse]', self._patch_items(url, data, chunksize=TYPE_CURVE_BATCH_LIMIT))

    def delete_type_curves(
        self, project_id: str, name: str | None = None, id: str | None = None
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes the type curves matching `name` or `id` (at least one is required), with their fits
        and normalization. Returns the response headers; 'X-Delete-Count' is the number deleted.
        v2 answers `404 TypeCurveV2NotFoundError` when nothing matches (live 2026-11-05); that
        returns `X-Delete-Count: 0` here, as v1 did, rather than raising.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/delete-v2-type-curves
        """
        filters = self._require_any_filter({'name': name, 'id': id}, 'name or id')
        try:
            responses = self._delete_responses(self.get_type_curves_url(project_id, filters), data=[])
        except requests.HTTPError as error:
            if (
                error.response is not None
                and error.response.status_code == 404
                and _error_name(error.response) == 'TypeCurveV2NotFoundError'
            ):
                return CaseInsensitiveDict({'X-Delete-Count': '0'})
            raise
        return responses[0].headers

    def delete_type_curve_by_id(self, project_id: str, type_curve_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes one type curve with its fits and normalization; lookup-table rules that pointed at
        it lose their type curve. Returns the response headers.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/delete-v2-type-curve
        """
        response = self._request_with_retry('delete', self.get_type_curve_by_id_url(project_id, type_curve_id))
        response.raise_for_status()
        return response.headers

    def get_type_curve_fits(self, project_id: str, type_curve_id: str, phases: Sequence[Phase] | None = None) -> Item:
        """
        Returns a type curve's fits keyed by phase; `{}` when never fitted. `linear` segments read
        `slope` as the sign: pass the body through `type_curve_conversions.fits_for_put` before
        writing it back.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-fits
        """
        return self._request_one_item('get', self.get_type_curve_fits_url(project_id, type_curve_id, phases))

    def put_type_curve_fits(self, project_id: str, type_curve_id: str, data: Item) -> Item:
        """
        Replaces a type curve's fits with `data` and returns them as stored. A stored phase left
        out of `data` is DELETED (live 2026-11-05). `regressionType` is rejected on a phase. A GET
        body is not safe verbatim: use `type_curve_conversions.fits_for_put` first, or a `linear`
        segment is stored with a different `qEnd`. The body is sent unchanged.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/put-v2-type-curve-fits
        """
        return self._request_one_item('put', self.get_type_curve_fits_url(project_id, type_curve_id), data)

    def get_type_curve_normalization(
        self, project_id: str, type_curve_id: str, phases: Sequence[Phase] | None = None
    ) -> Item:
        """
        Returns a type curve's normalization configuration, keyed by phase.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-normalization
        """
        url = self.get_type_curve_normalization_url(project_id, type_curve_id, phases)
        return self._request_one_item('get', url)

    def put_type_curve_normalization(self, project_id: str, type_curve_id: str, data: Item) -> Item:
        """
        Replaces a type curve's normalization configuration; all three phases are required. A GET
        body is not accepted verbatim (`1_to_1` coefficients, `xAxis` with `customBasisKey`): use
        `type_curve_conversions.normalization_for_put` first. Does not recompute per-well
        multipliers. The body is sent unchanged.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/put-v2-type-curve-normalization
        """
        url = self.get_type_curve_normalization_url(project_id, type_curve_id)
        return self._request_one_item('put', url, data)

    def get_type_curve_volumes(self, project_id: str, type_curve_id: str, resolution: Resolution) -> ItemList:
        """
        Returns a type curve's volumes at `resolution` ('daily' or 'monthly'), one row per period
        from 1 January of the current year, in date order. A series with no fit, and a phase with
        no fitted series, is left out of the rows (v1 gave `null`); see
        `type_curve_conversions.volumes_to_v1`.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-volumes
        """
        url = self.get_type_curve_volumes_url(project_id, type_curve_id)
        return self._get_items(url, {'resolution': resolution, 'take': VOLUMES_GET_LIMIT})

    def get_type_curve_wells(
        self, project_id: str, type_curve_id: str, filters: dict[str, str] | None = None
    ) -> ItemList:
        """
        Returns the wells assigned to a type curve as full project-well objects, each with an
        `excluded` flag. Filter with `{'excluded': 'true'}` or the project-well filters.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/get-v2-type-curve-wells
        """
        url = self.get_type_curve_wells_url(project_id, type_curve_id, filters)
        wells = self._get_items(url, {'take': WELLS_GET_LIMIT})
        return self._keysort(wells, WELL_LIST_SORT_ORDER)

    def count_type_curve_wells(self, project_id: str, type_curve_id: str, filters: dict[str, str] | None = None) -> int:
        """
        Returns the number of wells assigned to a type curve, from the HEAD route's `X-Query-Count`.

        https://docs.api.combocurve.com/api/type-curves-v2-preview/head-v2-type-curve-wells
        """
        return self._count_items(self.get_type_curve_wells_url(project_id, type_curve_id, filters))
