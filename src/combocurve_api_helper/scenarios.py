import warnings
from typing import Optional, cast

from requests.structures import CaseInsensitiveDict

from .base import LIST_SORT_ORDER, APIBase, Item, ItemList, WriteResponse

GET_LIMIT = 200
GET_LIMIT_MODEL_ASSIGNMENTS = 500  # the documented maximum of `take` on the model-assignments route


def _require_assignment_records(data: ItemList) -> None:
    """An empty list would reach the transport's no-body branch, so refuse it before any request."""
    if not data:
        raise ValueError('data must hold at least one assignment record')


class Scenarios(APIBase):
    ######
    # URLs
    ######

    def get_scenarios_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for project scenarios scoped from the project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/scenarios'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_by_id_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url for a specific project scenario from its
        scenario id.
        """
        base_url = self.get_scenarios_url(project_id)
        return f'{base_url}/{scenario_id}'

    def get_scenario_combos_url(
        self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for combos for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/combos'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_qualifiers_url(
        self,
        project_id: str,
        scenario_id: str,
        econ_name: Optional[str] = None,
        filters: Optional[dict[str, str]] = None,
    ) -> str:
        """
        Returns the API url for qualifiers for a specific project id,
        scenario id, and optionally, econ name.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/qualifiers'

        if filters is None:
            filters = {}

        if econ_name is not None:
            for model in self.ECON_MODELS:
                if econ_name.casefold() == model['econModelType'].casefold():
                    filters['econName'] = econ_name
                    break

            else:
                model_names = [m['econModelType'] for m in self.ECON_MODELS]
                warnings.warn(
                    f'`econ_name` is not in list of valid names:\n{model_names}. All qualifiers will be returned.',
                    stacklevel=2,
                )

        url += self._build_params_string(filters)
        return url

    def get_scenario_wells_url(
        self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for well assignments for a specific project id and
        scenario id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/well-assignments'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_econ_model_assignments_url(
        self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for the scenario's econ-model assignment grid
        (per-well assignments across every econ column / qualifier).
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/assignments/econ-models'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_run_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url to run a specific scenario.
        Route: /v1/projects/{projectId}/scenarios/{scenarioId}/run
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        return f'{base_url}/run'

    def get_scenario_run_by_job_id_url(self, project_id: str, scenario_id: str, job_id: str) -> str:
        """
        Returns the API url for the status of a specific scenario run job.
        Route: /v1/projects/{projectId}/scenarios/{scenarioId}/run/{jobId}
        """
        base_url = self.get_scenario_run_url(project_id, scenario_id)
        return f'{base_url}/{job_id}'

    def get_scenario_model_assignments_url(
        self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for the scenario's model assignments (per-well assignments of
        models to qualifiers, one row per well and incremental index).
        Route: /v1/projects/{projectId}/scenarios/{scenarioId}/assignments/models
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/assignments/models'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    ###########
    # API calls
    ###########

    # Scenarios

    def get_scenarios(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of scenarios scoped from the project's id.

        https://docs.api.combocurve.com/api/get-scenarios
        """
        url = self.get_scenarios_url(project_id, filters)
        params = {'take': GET_LIMIT}
        scenarios = self._get_items(url, params=params)

        return self._keysort(scenarios, LIST_SORT_ORDER)

    def count_scenarios(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of scenarios in a project matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-scenarios
        """
        return self._count_items(self.get_scenarios_url(project_id, filters))

    def post_scenarios(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates scenarios for a specific project id.

        https://docs.api.combocurve.com/api/post-project-scenarios
        """
        url = self.get_scenarios_url(project_id)
        scenarios = cast('list[WriteResponse]', self._post_items(url, data))

        return scenarios

    def put_scenarios(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts scenarios for a specific project id.

        https://docs.api.combocurve.com/api/put-project-scenarios
        """
        url = self.get_scenarios_url(project_id)
        scenarios = cast('list[WriteResponse]', self._put_items(url, data))

        return scenarios

    def delete_scenarios(
        self,
        project_id: str,
        scenario_name: Optional[str] = None,
        scenario_id: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes scenarios for a specific project id.

        https://docs.api.combocurve.com/api/delete-project-scenarios

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters = self._require_any_filter(
            {'name': scenario_name, 'id': scenario_id},
            'scenario_name or scenario_id',
        )

        url = self.get_scenarios_url(project_id, filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers

    def get_scenario_by_id(self, project_id: str, scenario_id: str) -> Item:
        """
        Returns a specific scenario from its scenario id.

        https://docs.api.combocurve.com/api/get-scenario-by-id

        Example response:
        {
            "createdAt": "2020-01-01",
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "updatedAt": "2020-01-01"
        }
        """
        url = self.get_scenario_by_id_url(project_id, scenario_id)
        scenarios = self._get_items(url)

        return scenarios[0]

    # Combos

    def get_scenario_combos(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns a list of combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/get-scenario-combos-read
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def count_scenario_combos(self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of combos in a scenario matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-scenario-combos-count
        """
        return self._count_items(self.get_scenario_combos_url(project_id, scenario_id, filters))

    def post_scenario_combos(self, project_id: str, scenario_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/post-scenario-combos-upsert
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        scenarios = cast('list[WriteResponse]', self._post_items(url, data))

        return scenarios

    def put_scenario_combos(self, project_id: str, scenario_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/put-scenario-combos-upsert
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        scenarios = cast('list[WriteResponse]', self._put_items(url, data))

        return scenarios

    def delete_scenario_combo(self, project_id: str, scenario_id: str, saved_name: str) -> CaseInsensitiveDict[str]:
        """
        Deletes scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/delete-scenario-combos-delete

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters = self._require_any_filter({'savedName': saved_name}, 'saved_name')

        url = self.get_scenario_combos_url(project_id, scenario_id, filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers

    # Qualifiers

    def get_scenario_qualifiers(self, project_id: str, scenario_id: str, econ_name: Optional[str] = None) -> Item:
        """
        Returns a list of qualifiers for a specific project id, scenario id and
        econ name.

        https://docs.api.combocurve.com/api/get-qualifiers-read
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id, econ_name)
        qualifiers = self._get_items(url)

        return qualifiers[0]

    def post_scenario_qualifiers(self, project_id: str, scenario_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/post-qualifiers-upsert
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id)
        scenarios = cast('list[WriteResponse]', self._post_items(url, data))

        return scenarios

    def put_scenario_qualifiers(self, project_id: str, scenario_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/put-qualifiers-upsert
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id)
        scenarios = cast('list[WriteResponse]', self._put_items(url, data))

        return scenarios

    def delete_scenario_qualifiers(
        self, project_id: str, scenario_id: str, econ_names: str, qualifier_names: str
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/delete-qualifiers-delete

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        # Both filters are required by the API and always sent together, so refuse if
        # EITHER is empty rather than only when both are. An unresolved lookup yielding ''
        # in one field would otherwise forward `?econNames=&qualifierNames=P50` (or the
        # mirror), and a blank filter the API may read as "unfiltered" widens the delete
        # past what the caller named -- the same ARIES-empty-lookup hazard the well
        # deletes guard against, applied per-field because both must be present.
        if not econ_names or not qualifier_names:
            raise ValueError('Must provide both econ_names and qualifier_names')

        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        filters: dict[str, str] = {'econNames': econ_names, 'qualifierNames': qualifier_names}
        url = f'{base_url}/qualifiers' + self._build_params_string(filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers

    # Scenario Wells

    def get_scenario_wells(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns a list of well assignments for a specific project id and
        scenario id.

        https://docs.api.combocurve.com/api/get-scenario-wells-read
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        return self._get_items(url)

    def get_scenario_econ_model_assignments(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns the scenario's econ-model assignment grid: one entry per well,
        each listing its assumption columns and, per column, the
        qualifierName -> assigned econModelId mapping.

        Distinct from `get_scenario_wells` (well *membership*, the
        `/well-assignments` route) and from
        `get_econ_model_assignments_by_type_by_id` (assignments *of one* econ
        model, the `/econ-models/{type}/{id}/assignments` route). This is the
        scenario-wide grid at `/scenarios/{id}/assignments/econ-models`. Uses
        cursor pagination (skip/take are ignored by this route).
        """
        url = self.get_scenario_econ_model_assignments_url(project_id, scenario_id)
        return self._get_items(url)

    def post_scenario_wells(self, project_id: str, scenario_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/post-scenario-wells-upsert
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        scenarios = cast('list[WriteResponse]', self._post_items(url, data))

        return scenarios

    def put_scenario_wells(self, project_id: str, scenario_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/put-scenario-wells-upsert
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        scenarios = cast('list[WriteResponse]', self._put_items(url, data))

        return scenarios

    def delete_scenario_wells(self, project_id: str, scenario_id: str, wells: str) -> CaseInsensitiveDict[str]:
        """
        Deletes scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/delete-scenario-wells-delete

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters = self._require_any_filter({'wells': wells}, 'wells')

        url = self.get_scenario_wells_url(project_id, scenario_id, filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers

    # Scenario run

    def post_scenario_run(self, project_id: str, scenario_id: str, data: Optional[Item] = None) -> Item:
        """
        Starts an (async) run of a specific scenario. All fields of `data` are optional
        (`wellIds`, `incrementalIndex`, `econSettingId`, `econReportSettingId`, `comboSettingId`,
        `runModels`, `runMode`, `suggestedHeaders`, `prodAnalyticsType`, `timeZone`). The route does
        not accept `scenarioWellAssignmentIds`.

        ComboCurve answers 202 with the job id. Poll `get_scenario_run_by_job_id` for the status.

        https://docs.api.combocurve.com/api/post-scenario-run

        Example data:
        {
            "wellIds": [
                "string"
            ],
            "incrementalIndex": 123,
            "econSettingId": "5e272d38b78910dd2a1bd691",
            "econReportSettingId": "5e272d38b78910dd2a1bd691",
            "comboSettingId": "5e272d38b78910dd2a1bd691",
            "runModels": "economics_only",
            "runMode": "fast",
            "suggestedHeaders": true,
            "prodAnalyticsType": "daysOn",
            "timeZone": "string"
        }

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691"
        }
        """
        # The run endpoint receives a single object body, not a list, so `self._post_items`
        # (which chunks a list) does not apply.
        url = self.get_scenario_run_url(project_id, scenario_id)
        response = self._request_with_retry('post', url, json_body={} if data is None else data)
        response.raise_for_status()

        return self._extract_json(response)[0]

    def get_scenario_run_by_job_id(self, project_id: str, scenario_id: str, job_id: str) -> Item:
        """
        Returns the status of a specific scenario run job from its job id.

        https://docs.api.combocurve.com/api/get-scenario-run-status

        Example response:
        {
            "jobId": "5e272d38b78910dd2a1bd691",
            "status": "pending",
            "progress": 123,
            "createdAt": "2020-01-01T00:00:00.000Z",
            "startedAt": "2020-01-01T00:00:00.000Z",
            "completedAt": "2020-01-01T00:00:00.000Z",
            "result": {
                "runModels": "economics_only",
                "project": "string",
                "scenario": "string",
                "econRunId": "5e272d38b78910dd2a1bd691"
            },
            "error": "string"
        }
        """
        url = self.get_scenario_run_by_job_id_url(project_id, scenario_id, job_id)
        jobs = self._get_items(url)

        return jobs[0]

    # Scenario model assignments

    def get_scenario_model_assignments(
        self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None
    ) -> ItemList:
        """
        Returns the scenario's model assignments: one row per well and incremental index, each
        listing its models and, per model, the qualifier name -> model id assignments.

        `filters` take `model`, `qualifierName`, `wellId` (up to 100 values), `incrementalIndex`.
        The rows are returned in the order received. `incrementalIndex` can be absent from a row
        (seen live 2026-11-05; Postman shows it).

        https://docs.api.combocurve.com/api/get-scenario-model-assignments

        Example response:
        [
            {
                "wellId": "5e272d38b78910dd2a1bd691",
                "incrementalIndex": 123,
                "models": [
                    {
                        "model": "forecast",
                        "assignments": [
                            {
                                "qualifierName": "string",
                                "modelId": "5e272d38b78910dd2a1bd691",
                                "series": "P50"
                            }
                        ]
                    }
                ]
            }
        ]
        """
        url = self.get_scenario_model_assignments_url(project_id, scenario_id, filters)
        params = {'take': GET_LIMIT_MODEL_ASSIGNMENTS}
        return self._get_items(url, params=params)

    def put_scenario_model_assignments(
        self, project_id: str, scenario_id: str, data: ItemList, add_wells_to_forecast: bool = False
    ) -> list[WriteResponse]:
        """
        Upserts scenario model assignments. Each entry of `data` has `model`, `qualifierName`,
        `incrementalIndex`, `wellIds` or `allWells`, `modelId` and `series`.

        **With `add_wells_to_forecast=True` this also changes the forecast: ComboCurve adds the
        targeted wells to it.**

        https://docs.api.combocurve.com/api/put-scenario-model-assignments

        Example data:
        [
            {
                "model": "forecast",
                "qualifierName": "string",
                "incrementalIndex": 123,
                "wellIds": [
                    "string"
                ],
                "allWells": true,
                "modelId": "5e272d38b78910dd2a1bd691",
                "series": "P50"
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "wellsUpdated": 123,
                    "wellsFailed": 123,
                    "wellsAddedToForecast": 123,
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
        """
        _require_assignment_records(data)
        filters: Optional[dict[str, str]] = {'addWellsToForecast': 'true'} if add_wells_to_forecast else None
        url = self.get_scenario_model_assignments_url(project_id, scenario_id, filters)
        assignments = cast('list[WriteResponse]', self._put_items(url, data))

        return assignments

    def delete_scenario_model_assignments(
        self, project_id: str, scenario_id: str, data: ItemList
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes scenario model assignments. Each entry of `data` has `model`, `qualifierName`,
        `incrementalIndex`, `wellIds` or `allWells`, and `modelId`.

        https://docs.api.combocurve.com/api/delete-scenario-model-assignments

        Returns the headers from the delete response.
        """
        _require_assignment_records(data)
        url = self.get_scenario_model_assignments_url(project_id, scenario_id)
        responses = self._delete_responses(url, data)

        return responses[0].headers

    # Scenario lookup-tables (project-scoped: /scenarios/lookup-tables)

    def get_scenario_lookup_tables_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url of scenario lookup-tables for a specific project id.
        Route: /v1/projects/{projectId}/scenarios/lookup-tables
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/scenarios/lookup-tables'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_lookup_table_by_id_url(
        self, project_id: str, lookup_table_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a specific scenario lookup-table from its id.
        """
        base_url = self.get_scenario_lookup_tables_url(project_id)
        url = f'{base_url}/{lookup_table_id}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_lookup_tables(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of scenario lookup-tables for a specific project id.
        """
        url = self.get_scenario_lookup_tables_url(project_id, filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def count_scenario_lookup_tables(self, project_id: str, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of scenario lookup tables matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-scenario-lookup-tables
        """
        return self._count_items(self.get_scenario_lookup_tables_url(project_id, filters))

    def get_scenario_lookup_table_by_id(self, project_id: str, lookup_table_id: str) -> Item:
        """
        Returns a specific scenario lookup-table from its id.
        """
        url = self.get_scenario_lookup_table_by_id_url(project_id, lookup_table_id)
        lookup_tables = self._get_items(url)
        return lookup_tables[0]

    def post_scenario_lookup_tables(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates scenario lookup-tables for a specific project id.
        """
        url = self.get_scenario_lookup_tables_url(project_id)
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_scenario_lookup_tables(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts scenario lookup-tables for a specific project id.
        """
        url = self.get_scenario_lookup_tables_url(project_id)
        return cast('list[WriteResponse]', self._put_items(url, data))

    def delete_scenario_lookup_table_by_id(self, project_id: str, lookup_table_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific scenario lookup-table from its id.

        Returns the headers from the delete response.
        """
        url = self.get_scenario_lookup_table_by_id_url(project_id, lookup_table_id)
        lookup_tables = self._delete_responses(url, data=[])
        return lookup_tables[0].headers

    # Scenario lookup-table assignments (/scenarios/{id}/assignments/lookup-tables)

    def get_scenario_lookup_table_assignments_url(
        self, project_id: str, scenario_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a scenario's lookup-table assignments.
        Route: /v1/projects/{projectId}/scenarios/{scenarioId}/assignments/lookup-tables
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/assignments/lookup-tables'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_lookup_table_assignment_by_id_url(
        self, project_id: str, scenario_id: str, lookup_table_id: str, filters: Optional[dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a specific scenario lookup-table assignment from its id.
        """
        base_url = self.get_scenario_lookup_table_assignments_url(project_id, scenario_id)
        url = f'{base_url}/{lookup_table_id}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_lookup_table_assignments(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns the lookup-table assignments for a specific scenario.
        """
        url = self.get_scenario_lookup_table_assignments_url(project_id, scenario_id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def put_scenario_lookup_table_assignments(
        self, project_id: str, scenario_id: str, data: ItemList
    ) -> list[WriteResponse]:
        """
        Upserts the lookup-table assignments for a specific scenario.
        """
        url = self.get_scenario_lookup_table_assignments_url(project_id, scenario_id)
        return cast('list[WriteResponse]', self._put_items(url, data))

    def get_scenario_lookup_table_assignment_by_id(
        self, project_id: str, scenario_id: str, lookup_table_id: str
    ) -> Item:
        """
        Returns a specific scenario lookup-table assignment from its id.
        """
        url = self.get_scenario_lookup_table_assignment_by_id_url(project_id, scenario_id, lookup_table_id)
        assignments = self._get_items(url)
        return assignments[0]

    def delete_scenario_lookup_table_assignment_by_id(
        self, project_id: str, scenario_id: str, lookup_table_id: str
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific scenario lookup-table assignment from its id.

        Returns the headers from the delete response.
        """
        url = self.get_scenario_lookup_table_assignment_by_id_url(project_id, scenario_id, lookup_table_id)
        assignments = self._delete_responses(url, data=[])
        return assignments[0].headers


post_put_scenarios_response = """
        Example data:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example"
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "id": "5e272d38b78910dd2a1bd691",
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
"""

post_put_scenario_combos_response = """
        Example data:
        [
            {
                "savedName": "string",
                "combos": [
                    {
                        "comboName": "string",
                        "qualifiers": [
                            {
                                "assumption": "string",
                                "qualifierName": "string"
                            }
                        ],
                        "selected": true,
                        "facilityNetworkName": "string"
                    }
                ]
            }
        ]

        Example response:
        {
            "failedCount": 123,
            "generalErrors": [
                {
                    "chosenID": "string",
                    "location": "string",
                    "message": "string",
                    "name": "Example"
                }
            ],
            "results": [
                {
                    "chosenID": "string",
                    "code": 123,
                    "status": "string"
                }
            ],
            "successCount": 123
        }
"""

post_put_scenario_qualifiers_response = """
        Example data:
        [
            {
                "econModel": "string",
                "name": "Example",
                "newName": "string"
            }
        ]

        Example response:
        {
            "failedCount": 123,
            "generalErrors": [
                {
                    "chosenID": "string",
                    "location": "string",
                    "message": "string",
                    "name": "Example"
                }
            ],
            "results": [
                {
                    "chosenID": "string",
                    "code": 123,
                    "status": "string"
                }
            ],
            "successCount": 123
        }
"""

post_put_scenario_wells_response = """
        Example data:
        [
            "string"
        ]

        Example response:
        {
            "failedCount": 123,
            "generalErrors": [
                {
                    "chosenID": "string",
                    "location": "string",
                    "message": "string",
                    "name": "Example"
                }
            ],
            "results": [
                {
                    "chosenID": "string",
                    "code": 123,
                    "status": "string"
                }
            ],
            "successCount": 123
        }
"""

Scenarios.post_scenarios.__doc__ += post_put_scenarios_response  # type: ignore [operator]
Scenarios.put_scenarios.__doc__ += post_put_scenarios_response  # type: ignore [operator]

Scenarios.post_scenario_combos.__doc__ += post_put_scenario_combos_response  # type: ignore [operator]
Scenarios.put_scenario_combos.__doc__ += post_put_scenario_combos_response  # type: ignore [operator]

Scenarios.post_scenario_qualifiers.__doc__ += post_put_scenario_qualifiers_response  # type: ignore [operator]
Scenarios.put_scenario_qualifiers.__doc__ += post_put_scenario_qualifiers_response  # type: ignore [operator]

Scenarios.post_scenario_wells.__doc__ += post_put_scenario_wells_response  # type: ignore [operator]
Scenarios.put_scenario_wells.__doc__ += post_put_scenario_wells_response  # type: ignore [operator]
