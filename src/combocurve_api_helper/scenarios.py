import requests
import warnings

from requests.structures import CaseInsensitiveDict

from combocurve_api_v1.pagination import get_next_page_url

from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList, WriteResponse


GET_LIMIT = 200


class Scenarios(APIBase):
    ######
    # URLs
    ######

    def get_scenarios_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
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
        self, project_id: str, scenario_id: str, filters: Optional[Dict[str, str]] = None
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
        filters: Optional[Dict[str, str]] = None,
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
                    f'`econ_name` is not in list of valid names:\n{model_names}. All qualifiers will be returned.'
                )

        url += self._build_params_string(filters)
        return url

    def get_scenario_wells_url(
        self, project_id: str, scenario_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for well assignments for a specific project id and
        scenario id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{self.API_BASE_URL}/projects/{project_id}/scenarios/{scenario_id}/well-assignments'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_scenario_econ_model_assignments_url(
        self, project_id: str, scenario_id: str, filters: Optional[Dict[str, str]] = None
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

    ###########
    # API calls
    ###########

    # Scenarios

    def get_scenarios(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of scenarios scoped from the project's id.

        https://docs.api.combocurve.com/api/get-scenarios
        """
        url = self.get_scenarios_url(project_id, filters)
        params = {'take': GET_LIMIT}
        scenarios = self._get_items(url, params=params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(scenarios, order)

    def post_scenarios(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates scenarios for a specific project id.

        https://docs.api.combocurve.com/api/post-project-scenarios
        """
        url = self.get_scenarios_url(project_id)
        scenarios = cast(List[WriteResponse], self._post_items(url, data))

        return scenarios

    def put_scenarios(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts scenarios for a specific project id.

        https://docs.api.combocurve.com/api/put-project-scenarios
        """
        url = self.get_scenarios_url(project_id)
        scenarios = cast(List[WriteResponse], self._put_items(url, data))

        return scenarios

    def delete_scenarios(
        self, project_id: str, scenario_name: Optional[str], scenario_id: Optional[str]
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes scenarios for a specific project id.

        https://docs.api.combocurve.com/api/delete-project-scenarios

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        if (scenario_name or scenario_id) is None:
            raise ValueError('Must provide at least one of scenario_name or scenario_id')

        filters: Dict[str, str] = {}
        if scenario_name is not None:
            filters['name'] = scenario_name

        if scenario_id is not None:
            filters['id'] = scenario_id

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

    def post_scenario_combos(self, project_id: str, scenario_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/post-scenario-combos-upsert
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        scenarios = cast(List[WriteResponse], self._post_items(url, data))

        return scenarios

    def put_scenario_combos(self, project_id: str, scenario_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/put-scenario-combos-upsert
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        scenarios = cast(List[WriteResponse], self._put_items(url, data))

        return scenarios

    def delete_scenario_combo(self, project_id: str, scenario_id: str, saved_name: str) -> CaseInsensitiveDict[str]:
        """
        Deletes scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/delete-scenario-combos-delete

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters: Dict[str, str] = {}
        filters['savedName'] = saved_name

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

    def post_scenario_qualifiers(self, project_id: str, scenario_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/post-qualifiers-upsert
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id)
        scenarios = cast(List[WriteResponse], self._post_items(url, data))

        return scenarios

    def put_scenario_qualifiers(self, project_id: str, scenario_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/put-qualifiers-upsert
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id)
        scenarios = cast(List[WriteResponse], self._put_items(url, data))

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
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        filters: Dict[str, str] = {'econNames': econ_names, 'qualifierNames': qualifier_names}
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

    def post_scenario_wells(self, project_id: str, scenario_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/post-scenario-wells-upsert
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        scenarios = cast(List[WriteResponse], self._post_items(url, data))

        return scenarios

    def put_scenario_wells(self, project_id: str, scenario_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/put-scenario-wells-upsert
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        scenarios = cast(List[WriteResponse], self._put_items(url, data))

        return scenarios

    def delete_scenario_wells(self, project_id: str, scenario_id: str, wells: str) -> CaseInsensitiveDict[str]:
        """
        Deletes scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/api/delete-scenario-wells-delete

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters: Dict[str, str] = {}
        filters['wells'] = wells

        url = self.get_scenario_wells_url(project_id, scenario_id, filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers

    # Scenario lookup-tables (project-scoped: /scenarios/lookup-tables)

    def get_scenario_lookup_tables_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
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
        self, project_id: str, lookup_table_id: str, filters: Optional[Dict[str, str]] = None
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

    def get_scenario_lookup_tables(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of scenario lookup-tables for a specific project id.
        """
        url = self.get_scenario_lookup_tables_url(project_id, filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_scenario_lookup_table_by_id(self, project_id: str, lookup_table_id: str) -> Item:
        """
        Returns a specific scenario lookup-table from its id.
        """
        url = self.get_scenario_lookup_table_by_id_url(project_id, lookup_table_id)
        lookup_tables = self._get_items(url)
        return lookup_tables[0]

    def post_scenario_lookup_tables(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates scenario lookup-tables for a specific project id.
        """
        url = self.get_scenario_lookup_tables_url(project_id)
        return cast(List[WriteResponse], self._post_items(url, data))

    def put_scenario_lookup_tables(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts scenario lookup-tables for a specific project id.
        """
        url = self.get_scenario_lookup_tables_url(project_id)
        return cast(List[WriteResponse], self._put_items(url, data))

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
        self, project_id: str, scenario_id: str, filters: Optional[Dict[str, str]] = None
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
        self, project_id: str, scenario_id: str, lookup_table_id: str, filters: Optional[Dict[str, str]] = None
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
    ) -> List[WriteResponse]:
        """
        Upserts the lookup-table assignments for a specific scenario.
        """
        url = self.get_scenario_lookup_table_assignments_url(project_id, scenario_id)
        return cast(List[WriteResponse], self._put_items(url, data))

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
                        "selected": true
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
