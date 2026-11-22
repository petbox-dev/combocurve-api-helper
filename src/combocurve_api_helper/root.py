import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, cast, overload

from typing_extensions import deprecated

from .base import APIBase, Item, ItemList, QueryFilters, WriteResponse

GET_LIMIT = 200


def _custom_column_argument(custom_column: Optional[str], collection: Optional[str]) -> str:
    """The project custom-columns path segment, from `custom_column` or its deprecated alias.

    2.2.2 renamed the keyword `collection` to `custom_column`, which broke keyword callers.
    `collection=` is accepted again with a `DeprecationWarning`; passing both, or neither, raises.
    """
    if collection is not None:
        if custom_column is not None:
            raise TypeError('pass custom_column or its deprecated alias collection, not both')
        warnings.warn('the collection argument is deprecated; pass custom_column', DeprecationWarning, stacklevel=3)
        return collection
    if custom_column is None:
        raise TypeError("missing required argument: 'custom_column'")
    return custom_column


# The root volume routes reject any request that does not scope itself to one of these.
# Enforced locally so the mistake is a ValueError at the call site rather than a round
# trip that always 400s. `well` is not a scope on its own: see `_require_volume_scope`.
_VOLUME_SCOPE_FILTERS = ('project', 'forecast')


def _require_volume_scope(filters: Optional[QueryFilters]) -> QueryFilters:
    """Return `filters` unchanged, or raise if it does not scope the volume query.

    The scope is `project` or `forecast`. A `well` filter also needs `forecast`: verified live
    2026-11-20 on dev, the API returns 400 for `well` alone and for `project` with `well`, and accepts
    `well` with `forecast`. The list methods read `project` without `forecast` one forecast at a time and
    do not call this for that scope, so there `well` with `project` is accepted.
    """
    if filters and filters.get('well') and not filters.get('forecast'):
        raise ValueError(
            "a 'well' filter on the root volume routes must come with 'forecast'; the API rejects "
            "'well' alone and 'well' with 'project' (the get_root_forecast_*_volumes list methods also take "
            "'well' with 'project', read one forecast at a time)"
        )

    if not filters or not any(filters.get(key) for key in _VOLUME_SCOPE_FILTERS):
        raise ValueError(
            "filters must include at least one of 'project' or 'forecast' ('well' only together with "
            "'forecast'); the API rejects an unscoped forecast-volumes request"
        )

    return filters


# The filters that leave the per-forecast fallback's rows comparable with the project count: `project` itself,
# `forecast` when it is empty (no forecast scope), `take`, which sets the page size, not the rows returned, and
# `skip`, which can only be 0 there (any other value is refused). Any other filter with a value (`well`,
# `startDate`, `endDate`, ...) skips the count check.
_COUNT_COMPARABLE_VOLUME_FILTERS = frozenset({'project', 'forecast', 'take', 'skip'})


def _reads_one_forecast_at_a_time(filters: Optional[QueryFilters]) -> bool:
    """True when `filters` scopes a root volume listing to `project` and not to `forecast`: the scope whose
    server listing repeats and drops rows, which the getters replace with one listing per forecast."""
    if not filters or not filters.get('project'):
        return False
    return not filters.get('forecast')


class Root(APIBase):
    if TYPE_CHECKING:
        # Provided at runtime by `Forecasts`, which follows this class in `ComboCurveAPI`'s bases; declared
        # here for the type checker only, with the same signature.
        def get_forecasts(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList: ...

    ######
    # URLs
    ######

    def get_custom_columns_url(self, collection: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for custom columns.
        """
        url = f'{self.API_BASE_URL}/custom-columns/{collection}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_well_identifiers_url(self) -> str:
        """
        Returns the API url for well identifiers.
        """
        # `wells-identifiers`, plural `wells` -- the route is spelled that way in both
        # the Postman collection and the OpenAPI spec (`operationId: patch-wells-identifiers`,
        # which is also this method's docs slug). The singular `well-identifiers` shipped
        # here through 2.1.0 and 404s.
        return f'{self.API_BASE_URL}/wells-identifiers'

    def get_tags_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for tags.
        """
        url = f'{self.API_BASE_URL}/tags'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_root_econ_runs_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for econ runs.
        """
        url = f'{self.API_BASE_URL}/econ-runs'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_root_econ_run_by_id_url(self, econrun_id: str) -> str:
        """
        Returns the API url for a specific econ run from its econ run id.
        """
        return f'{self.API_BASE_URL}/econ-runs/{econrun_id}'

    def get_root_forecast_daily_volumes_url(self, filters: Optional[QueryFilters] = None) -> str:
        """
        Returns the API url for daily volumes.
        """
        # The ROOT volume routes are flat and hyphenated -- `forecast-daily-volumes`, not
        # `forecasts/daily-volumes`. Only the project-scoped pair nests under `forecasts/`
        # (`projects/{id}/forecasts/{id}/daily-volumes`, see forecasts.py). The nested
        # spelling shipped here through 2.1.0 and 404s ("Method does not exist").
        url = f'{self.API_BASE_URL}/forecast-daily-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_root_forecast_monthly_volumes_url(self, filters: Optional[QueryFilters] = None) -> str:
        """
        Returns the API url for monthly volumes.
        """
        # Flat and hyphenated, as with the daily route above.
        url = f'{self.API_BASE_URL}/forecast-monthly-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_users_roles_url(self) -> str:
        """
        Returns the API url for company users and their roles.
        """
        return f'{self.API_BASE_URL}/users/roles'

    @overload
    def get_project_custom_columns_url(
        self, project_id: str, custom_column: str, filters: Optional[dict[str, str]] = None
    ) -> str: ...

    @overload
    @deprecated('the collection argument is deprecated; pass custom_column')
    def get_project_custom_columns_url(
        self,
        project_id: str,
        custom_column: None = None,
        filters: Optional[dict[str, str]] = None,
        *,
        collection: str,
    ) -> str: ...

    def get_project_custom_columns_url(
        self,
        project_id: str,
        custom_column: Optional[str] = None,
        filters: Optional[dict[str, str]] = None,
        *,
        collection: Optional[str] = None,
    ) -> str:
        """
        Returns the API url for a project's custom columns. `custom_column` -- "Currently
        only `headers` is supported" per the docs. `custom_column` is required; `collection`
        is its deprecated keyword alias (the name before 2.2.2).

        The overloads make a type checker refuse a call with neither argument, and flag a
        `collection=` call as deprecated. At run time a call with neither, or with both, raises
        `TypeError` before the url is built, and `collection=` warns with `DeprecationWarning`.
        """
        segment = _custom_column_argument(custom_column, collection)
        url = f'{self.API_BASE_URL}/projects/{project_id}/custom-columns/{segment}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    ###########
    # API calls
    ###########

    def get_custom_columns(self, collection: str, filters: Optional[dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns. See other convenience methods for specific collections.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        url = self.get_custom_columns_url(collection, filters)
        columns = self._get_items(url)
        return columns[0]

    def get_custom_columns_wells(self, filters: Optional[dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Wells.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        return self.get_custom_columns('wells', filters)

    def get_custom_columns_daily_production(self, filters: Optional[dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Daily Production.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        return self.get_custom_columns('daily-productions', filters)

    def get_custom_columns_monthly_production(self, filters: Optional[dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Monthly Production.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        return self.get_custom_columns('monthly-productions', filters)

    def patch_well_identifiers(self, data: ItemList) -> list[WriteResponse]:
        """
        Update well identifiers.

        https://docs.api.combocurve.com/api/patch-wells-identifiers

        Structure of data:
        [
            ...,
            {
                "wellId": "5e272d39b78210dd2a1bd8fe", // required
                        "newInfo": { // at least one of them.
                            "chosenKeyID": "api14",
                            "companyScope": true,
                            "dataSource": "internal"
                        }
            },
            ...
        ]
        """
        url = self.get_well_identifiers_url()
        return cast('list[WriteResponse]', self._patch_items(url, data))

    def get_tags(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of tags.

        https://docs.api.combocurve.com/api/get-tags

        Example response:
        [
            {
                "createdAt": "2020-01-01",
                "description": "string",
                "name": "Example",
                "updatedAt": "2020-01-01"
            }
        ]
        """
        url = self.get_tags_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def count_tags(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of tags matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-tags
        """
        return self._count_items(self.get_tags_url(filters))

    def get_root_econ_runs(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ runs.

        https://docs.api.combocurve.com/api/get-root-econ-runs
        """
        url = self.get_root_econ_runs_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def count_root_econ_runs(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of econ runs across the company matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-root-econ-runs
        """
        return self._count_items(self.get_root_econ_runs_url(filters))

    def get_root_econ_run_by_id(self, id: str) -> Item:
        """
        Returns a specific econ run from its econ run id.

        https://docs.api.combocurve.com/api/get-root-econ-run-by-id
        """
        url = self.get_root_econ_run_by_id_url(id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)[0]

    def _get_root_forecast_volumes(
        self,
        build_url: Callable[[Optional[QueryFilters]], str],
        count: Callable[[Optional[QueryFilters]], int],
        filters: Optional[QueryFilters],
    ) -> ItemList:
        """The rows of a root volume listing (`build_url` is the daily or monthly url builder, `count` its count
        method). A `forecast` scope is read as sent. A `project` scope without `forecast` is read one forecast at
        a time, because the server's project-scoped listing repeats and drops rows (see the public getters)."""
        if not _reads_one_forecast_at_a_time(filters):
            return self._get_items_in_value_batches(
                build_url, _require_volume_scope(filters), 'well', {'take': GET_LIMIT}
            )

        assert filters is not None  # `_reads_one_forecast_at_a_time` is False for None
        project_id = filters['project']
        if not isinstance(project_id, str):
            raise ValueError(f"filters['project'] must be one project id string, not {project_id!r}")
        paging_keys = self._paging_filters_in(filters)
        if paging_keys:
            raise ValueError(
                f'{paging_keys[0]!r} cannot be combined with a project-scoped root volume read: it is read one '
                f'forecast at a time, and every forecast request would apply {paging_keys[0]!r} on its own. '
                f"Pass 'forecast' to page through one forecast."
            )

        narrowed = any(
            value is not None and key not in _COUNT_COMPARABLE_VOLUME_FILTERS for key, value in filters.items()
        )
        expected_count = None if narrowed else count({'project': project_id})

        rows: ItemList = []
        for forecast in self.get_forecasts(project_id):
            forecast_filters = {key: value for key, value in filters.items() if key != 'project'}
            forecast_filters['forecast'] = str(forecast['id'])
            rows.extend(self._get_items_in_value_batches(build_url, forecast_filters, 'well', {'take': GET_LIMIT}))

        if expected_count is not None and len(rows) != expected_count:
            raise RuntimeError(
                f'the per-forecast read of project {project_id} returned {len(rows)} volume rows, but the project '
                f'count is {expected_count}: the rows are incomplete or repeated (or the project changed during '
                'the read)'
            )

        return rows

    def get_root_forecast_daily_volumes(self, filters: Optional[QueryFilters] = None) -> ItemList:
        """
        Returns a list of daily volumes, one row per (forecast, well); each row's `forecast` field
        names its forecast.

        Scope: `filters` is REQUIRED here, unlike the other root list methods, and must carry `project`
        or `forecast`. The API rejects any other request with a ValidationError, so it is refused
        locally rather than sent. Accepted keys are `project`, `forecast`, `well`, `startDate`,
        `endDate`, `skip` and `take`; `sort` is not accepted (400 `Unrecognized filter`, dev 2026-11-21).

        `filters['well']` is accepted with `forecast`, and with `project` (read per forecast, below); the API
        returns 400 for `well` alone and for `project` with `well` (verified live 2026-11-20 on dev), so `well`
        alone is refused locally. It may be a list of well ids, sent as repeated `well` keys. The API accepts at
        most 100 per request, so a longer list is split into requests of 100 wells and the volumes are combined
        into one list.

        `project` without `forecast` is read one forecast at a time. The server's own project-scoped listing
        returns wrong rows above one page of 200: it repeats some (forecast, well) rows and leaves others out,
        or ends early on a short page with no next link, while the count stays right (dev 2026-11-21: a
        3,983-row project came back with 348 pairs twice and 348 missing; projects of 216 to 1,107 rows came
        back as one short page). The `forecast` scope was exact on every dev forecast (up to 6,890 rows). So
        this method sends one HEAD `count_root_forecast_daily_volumes({'project': P})`, lists the project's
        forecasts with `Forecasts.get_forecasts(P)`, then one listing per forecast with the caller's filters,
        `project` replaced by `forecast` (so a `well` filter is valid here). Cost: one count, one forecast
        list and one listing (paged by 200) per forecast. The rows come grouped by forecast, in the order
        `get_forecasts` returns the forecasts, and in server order within a forecast. If the row total differs
        from the count, `RuntimeError` names both numbers; a mismatch means the rows are still wrong (or the
        project changed during the read). The check is skipped, and the count not sent, when any filter other
        than `project`, `take` and a `skip` of 0 has a value (`well`, `startDate`, `endDate`), because the
        project count does not apply to the narrowed rows. `skip` (other than 0) and `cursor` are refused with
        `ValueError` with this scope, because each forecast request would apply them on its own.

        https://docs.api.combocurve.com/api/get-root-forecast-daily-volumes

        Example response:
        [
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "deterministic",
                "well": "string",
                "resolution": "monthly",
                "phases": [
                    {
                        "phase": "customNumber5",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "best",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "oil",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    }
                ]
            }
        ]
        """
        return self._get_root_forecast_volumes(
            self.get_root_forecast_daily_volumes_url, self.count_root_forecast_daily_volumes, filters
        )

    def count_root_forecast_daily_volumes(self, filters: Optional[QueryFilters] = None) -> int:
        """
        Returns the number of forecast daily-volume documents matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched). `filters` must carry
        `project` or `forecast`, as for `get_root_forecast_daily_volumes`; `well` only together with
        `forecast`. A `well` list longer than 100 is counted in batches of 100 and the counts are summed.
        For the count of one forecast by its path, use `Forecasts.count_forecast_daily_volumes`.

        With `project` alone the count is right and is not affected by the listing defect described in
        `get_root_forecast_daily_volumes` (it equals the sum of the per-forecast counts on every dev project,
        2026-11-21); that method sends this count to check its per-forecast read.

        https://docs.api.combocurve.com/api/head-root-forecast-daily-volumes
        """
        return self._count_items_in_value_batches(
            self.get_root_forecast_daily_volumes_url, _require_volume_scope(filters), 'well'
        )

    def get_root_forecast_monthly_volumes(self, filters: Optional[QueryFilters] = None) -> ItemList:
        """
        Returns a list of monthly volumes, one row per (forecast, well); each row's `forecast` field
        names its forecast.

        Scope: `filters` is REQUIRED here, unlike the other root list methods, and must carry `project`
        or `forecast`. The API rejects any other request with a ValidationError, so it is refused
        locally rather than sent. Accepted keys are `project`, `forecast`, `well`, `startDate`,
        `endDate`, `skip` and `take`; `sort` is not accepted (400 `Unrecognized filter`, dev 2026-11-21).

        `filters['well']` is accepted with `forecast`, and with `project` (read per forecast, below); the API
        returns 400 for `well` alone and for `project` with `well` (verified live 2026-11-20 on dev), so `well`
        alone is refused locally. It may be a list of well ids, sent as repeated `well` keys. The API accepts at
        most 100 per request, so a longer list is split into requests of 100 wells and the volumes are combined
        into one list.

        `project` without `forecast` is read one forecast at a time. The server's own project-scoped listing
        returns wrong rows above one page of 200: it repeats some (forecast, well) rows and leaves others out,
        or ends early on a short page with no next link, while the count stays right (dev 2026-11-21: a
        3,983-row project came back with 348 pairs twice and 348 missing; projects of 216 to 1,107 rows came
        back as one short page). The `forecast` scope was exact on every dev forecast (up to 6,890 rows). So
        this method sends one HEAD `count_root_forecast_monthly_volumes({'project': P})`, lists the project's
        forecasts with `Forecasts.get_forecasts(P)`, then one listing per forecast with the caller's filters,
        `project` replaced by `forecast` (so a `well` filter is valid here). Cost: one count, one forecast
        list and one listing (paged by 200) per forecast. The rows come grouped by forecast, in the order
        `get_forecasts` returns the forecasts, and in server order within a forecast. If the row total differs
        from the count, `RuntimeError` names both numbers; a mismatch means the rows are still wrong (or the
        project changed during the read). The check is skipped, and the count not sent, when any filter other
        than `project`, `take` and a `skip` of 0 has a value (`well`, `startDate`, `endDate`), because the
        project count does not apply to the narrowed rows. `skip` (other than 0) and `cursor` are refused with
        `ValueError` with this scope, because each forecast request would apply them on its own.

        https://docs.api.combocurve.com/api/get-root-forecast-monthly-volumes

        Example response:
        [
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "deterministic",
                "well": "string",
                "resolution": "monthly",
                "phases": [
                    {
                        "phase": "customNumber5",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "best",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "oil",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    }
                ]
            }
        ]
        """
        return self._get_root_forecast_volumes(
            self.get_root_forecast_monthly_volumes_url, self.count_root_forecast_monthly_volumes, filters
        )

    def count_root_forecast_monthly_volumes(self, filters: Optional[QueryFilters] = None) -> int:
        """
        Returns the number of forecast monthly-volume documents matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched). `filters` must carry
        `project` or `forecast`, as for `get_root_forecast_monthly_volumes`; `well` only together with
        `forecast`. A `well` list longer than 100 is counted in batches of 100 and the counts are summed.
        For the count of one forecast by its path, use `Forecasts.count_forecast_monthly_volumes`.

        With `project` alone the count is right and is not affected by the listing defect described in
        `get_root_forecast_monthly_volumes` (it equals the sum of the per-forecast counts on every dev project,
        2026-11-21); that method sends this count to check its per-forecast read.

        https://docs.api.combocurve.com/api/head-root-forecast-monthly-volumes
        """
        return self._count_items_in_value_batches(
            self.get_root_forecast_monthly_volumes_url, _require_volume_scope(filters), 'well'
        )

    def get_users_roles(self) -> ItemList:
        """
        Returns a list of company users and their roles.

        https://docs.api.combocurve.com/api/get-users-roles

        Example response:
        [
            {
                "userId": "5e272d38b78910dd2a1bd691",
                "firstName": "string",
                "lastName": "string",
                "email": "string",
                "resourceRoles": [
                    {
                        "resourceId": "5e272d38b78910dd2a1bd691",
                        "resourceType": "string",
                        "roles": [
                            "string"
                        ]
                    }
                ]
            }
        ]
        """
        url = self.get_users_roles_url()
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    @overload
    def get_project_custom_columns(
        self, project_id: str, custom_column: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList: ...

    @overload
    @deprecated('the collection argument is deprecated; pass custom_column')
    def get_project_custom_columns(
        self,
        project_id: str,
        custom_column: None = None,
        filters: Optional[dict[str, str]] = None,
        *,
        collection: str,
    ) -> ItemList: ...

    def get_project_custom_columns(
        self,
        project_id: str,
        custom_column: Optional[str] = None,
        filters: Optional[dict[str, str]] = None,
        *,
        collection: Optional[str] = None,
    ) -> ItemList:
        """
        Returns a project's custom well-header definitions. `custom_column` is
        "Currently only `headers` is supported" per the docs -- unlike the sibling
        `get_custom_columns`, whose `collection` argument is a collection name
        ('wells', 'daily-productions', ...), this one is not. The project-scoped
        counterpart to `get_custom_columns`. `custom_column` is required; `collection`
        is its deprecated keyword alias (the name before 2.2.2) and warns.

        The overloads make a type checker refuse a call with neither argument, and flag a
        `collection=` call as deprecated. At run time a call with neither, or with both, raises
        `TypeError` before anything is sent, and `collection=` warns with `DeprecationWarning`.

        The response is a list with one entry per project custom header -- 0 if the
        project has none defined, or several for a project with multiple. Verified
        live: a project with no custom headers returns `[]`; a project with several
        returns one dict per header.

        https://docs.api.combocurve.com/api/get-project-custom-columns

        Example response:
        [
            {
                "headerName": "string",
                "headerType": "string",
                "headerLabel": "string"
            }
        ]
        """
        segment = _custom_column_argument(custom_column, collection)
        url = self.get_project_custom_columns_url(project_id, segment, filters)
        return self._get_items(url)
