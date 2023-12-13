import requests  # type: ignore
import warnings

from combocurve_api_v1.pagination import get_next_page_url  # type: ignore

from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList


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

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_scenario_by_id_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url for a specific project scenario from its
        scenario id.
        """
        base_url = self.get_scenarios_url(project_id)
        return f'{base_url}/{scenario_id}'


    def get_scenario_combos_url(
            self, project_id: str, scenario_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for combos for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/combos'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url



    def get_scenario_qualifiers_url(
            self, project_id: str, scenario_id: str, econ_name: Optional[str] = None,
            filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for qualifiers for a specific project id,
        scenario id, and optionally, econ name.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/qualifiers'

        if filters is None:
            filters = {}

        if econ_name is not None:
            if econ_name.casefold() not in (n.casefold() for n in self.econ_model_types):
                warnings.warn(f'`econ_name` is not in list of valid names:\n{self.econ_model_types}')

            filters['econName'] = econ_name

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_scenario_wells_url(
            self, project_id: str, scenario_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for well assignments for a specific project id and
        scenario id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{self.API_BASE_URL}/projects/{project_id}/scenarios/{scenario_id}/well-assignments'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    ###########
    # API calls
    ###########


    # Scenarios


    def get_scenarios(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of scenarios scoped from the project's id.

        https://docs.api.combocurve.com/#e7de7ef5-228b-4de6-bd67-89c8ef14a4bc
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


    def post_scenarios(self, project_id: str, data: ItemList) -> ItemList:
        """
        Creates scenarios for a specific project id.

        https://docs.api.combocurve.com/#52df57aa-af96-4e86-976c-8d4aff3125f7
        """
        url = self.get_scenarios_url(project_id)
        scenarios = self._post_items(url, data)

        return scenarios


    def put_scenarios(self, project_id: str, data: ItemList) -> ItemList:
        """
        Upserts scenarios for a specific project id.

        https://docs.api.combocurve.com/#94b372d8-6696-4f65-b1b7-6c0576b3f75b
        """
        url = self.get_scenarios_url(project_id)
        scenarios = self._put_items(url, data)

        return scenarios


    def delete_scenarios(self, project_id: str, scenario_name: Optional[str], scenario_id: Optional[str]) -> ItemList:
        """
        Deletes scenarios for a specific project id.

        https://docs.api.combocurve.com/#7429717e-51f2-48de-ad22-6c4bc5bf1bb1

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

        https://docs.api.combocurve.com/#e7de7ef5-228b-4de6-bd67-89c8ef14a4bc

        Example response:
        [
            {
                "createdAt": "2020-01-21T16:58:08.986Z",
                "id": "5e5981b9e23dae0012624d72",
                "name": "Test scenario",
                "updatedAt": "2020-01-21T17:58:08.986Z"
            }
        ]
        """
        url = self.get_scenario_by_id_url(project_id, scenario_id)
        scenarios = self._get_items(url)

        return scenarios[0]


    # Combos


    def get_scenario_combos(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns a list of combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/#844e5b66-d20f-48ab-a186-380a1cc49630
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def post_scenario_combos(self, project_id: str, scenario_id: str, data: ItemList) -> ItemList:
        """
        Creates scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/#e14969da-bd78-4747-9f19-e0277836dfee
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        scenarios = self._post_items(url, data)

        return scenarios


    def put_scenario_combos(self, project_id: str, scenario_id: str, data: ItemList) -> ItemList:
        """
        Upserts scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/#2e47dad1-c176-4628-b97f-8ace00c6ad0d
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        scenarios = self._put_items(url, data)

        return scenarios


    def delete_scenario_combo(self, project_id: str, scenario_id: str, saved_name: str) -> ItemList:
        """
        Deletes scenario combos for a specific project id and scenario id.

        https://docs.api.combocurve.com/#881f45fd-287f-4f6c-a805-2e690d675a7a

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

        https://docs.api.combocurve.com/#76132581-aefd-4efa-ae82-2af8596340de
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id, econ_name)
        qualifiers = self._get_items(url)

        return qualifiers[0]


    def post_scenario_qualifiers(self, project_id: str, scenario_id: str, data: ItemList) -> ItemList:
        """
        Creates scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/#b917f0ea-9bf2-4fea-8c16-d780ade2ac2d
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id)
        scenarios = self._post_items(url, data)

        return scenarios


    def put_scenario_qualifiers(self, project_id: str, scenario_id: str, data: ItemList) -> ItemList:
        """
        Upserts scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/#f2d33571-1d1b-4f7b-b8a7-02d437dd4f02
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id)
        scenarios = self._put_items(url, data)

        return scenarios


    def delete_scenario_qualifiers(
            self, project_id: str, scenario_id: str,
            econ_names: str, qualifier_names: str) -> ItemList:
        """
        Deletes scenario qualifiers for a specific project id and scenario id.

        https://docs.api.combocurve.com/#75353547-a52c-444d-953f-219a0a006a51

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters: Dict[str, str] = {'qualifierNames': qualifier_names}

        url = self.get_scenario_qualifiers_url(project_id, scenario_id, econ_names, filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers

    # Scenario Wells


    def get_scenario_wells(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns a list of well assignments for a specific project id and
        scenario id.

        https://docs.api.combocurve.com/#7849574f-3530-4751-a21a-485e694609e6
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        return self._get_items(url)


    def post_scenario_wells(self, project_id: str, scenario_id: str, data: ItemList) -> ItemList:
        """
        Creates scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/#538885a6-3b78-44aa-9852-5b5574bd60f3
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        scenarios = self._post_items(url, data)

        return scenarios


    def put_scenario_wells(self, project_id: str, scenario_id: str, data: ItemList) -> ItemList:
        """
        Upserts scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/#b4f4a676-b3aa-4207-ae06-69b282da36fd
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        scenarios = self._put_items(url, data)

        return scenarios


    def delete_scenario_wells(self, project_id: str, scenario_id: str, wells: str) -> ItemList:
        """
        Deletes scenario well assignments for a specific project id and scenario id.

        https://docs.api.combocurve.com/#96bc7d64-831c-44ff-a707-4f0b31bb6c34

        Returns the headers from the delete response where 'X-Delete-Count' is
        the number of wells deleted.
        """
        filters: Dict[str, str] = {}
        filters['wells'] = wells

        url = self.get_scenario_wells_url(project_id, scenario_id, filters)
        scenarios = self._delete_responses(url, data=[])

        headers = scenarios[0].headers

        return headers


post_put_scenarios_response = """
        Example data:
        [
            {
                "id": "<string>",
                "name": "<string>"
            },
            {
                "id": "<string>",
                "name": "<string>"
            }
        ]

        Example response:
        [
            {
                "generalErrors": [
                    {
                        "name": "ValidationError",
                        "message": "The field 'name' is required.",
                        "location": "[0]"
                    },
                    {
                        "name": "ValidationError",
                        "message": "The field 'unique' is required.",
                        "location": "[2]"
                    }
                ],
                "results": [
                    {
                        "status": "Success",
                        "code": 200,
                        "chosenID": "5e5981b9e23dae0012624d72"
                    }
                ],
                "failedCount": 2,
                "successCount": 2
            }
        ]
"""

post_put_scenario_combos_response = """
        Example data:
        [
            {
                "savedName": "<string>",
                "combos": [
                    {
                        "comboName": "<string>",
                        "qualifiers": [
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            },
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            }
                        ],
                        "selected": "<boolean>"
                    },
                    {
                        "comboName": "<string>",
                        "qualifiers": [
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            },
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            }
                        ],
                        "selected": "<boolean>"
                    }
                ]
            },
            {
                "savedName": "<string>",
                "combos": [
                    {
                        "comboName": "<string>",
                        "qualifiers": [
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            },
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            }
                        ],
                        "selected": "<boolean>"
                    },
                    {
                        "comboName": "<string>",
                        "qualifiers": [
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            },
                            {
                                "assumption": "<string>",
                                "qualifierName": "<string>"
                            }
                        ],
                        "selected": "<boolean>"
                    }
                ]
            }
        ]

        Example response:
        [
            {
                "failedCount": 1,
                "generalErrors": [
                    {
                        "chosenID": "chosen_id",
                        "location": ".person.name",
                        "message": "The field name is required",
                        "name": "ValidationError"
                    }
                ],
                "results": [
                    {
                        "chosenID": "chosen_id",
                        "code": 201,
                        "status": "created"
                    }
                ],
                "successCount": 1
            }
        ]
"""

post_put_scenario_qualifiers_response = """
        Example data:
        [
            {
                "econModel": "<string>",
                "name": "<string>",
                "newName": "<string>"
            },
            {
                "econModel": "<string>",
                "name": "<string>",
                "newName": "<string>"
            }
        ]

        Example response:
        [
            {
                "failedCount": 1,
                "generalErrors": [
                    {
                        "chosenID": "chosen_id",
                        "location": ".person.name",
                        "message": "The field name is required",
                        "name": "ValidationError"
                    }
                ],
                "results": [
                    {
                        "chosenID": "chosen_id",
                        "code": 201,
                        "status": "created"
                    }
                ],
                "successCount": 1
            }
        ]
"""

post_put_scenario_wells_response = """
        Example data:
        [
            "<string>",
            "<string>"
        ]

        Example response:
        [
            {
                "failedCount": 1,
                "generalErrors": [
                    {
                        "chosenID": "chosen_id",
                        "location": ".person.name",
                        "message": "The field name is required",
                        "name": "ValidationError"
                    }
                ],
                "results": [
                    {
                        "chosenID": "chosen_id",
                        "code": 201,
                        "status": "created"
                    }
                ],
                "successCount": 1
            }
        ]
"""

Scenarios.post_scenarios.__doc__ += post_put_scenarios_response  # type: ignore [operator]
Scenarios.put_scenarios.__doc__ += post_put_scenarios_response  # type: ignore [operator]

Scenarios.post_scenario_combos.__doc__ += post_put_scenario_combos_response  # type: ignore [operator]
Scenarios.put_scenario_combos.__doc__ += post_put_scenario_combos_response  # type: ignore [operator]

Scenarios.post_scenario_qualifiers.__doc__ += post_put_scenario_qualifiers_response  # type: ignore [operator]
Scenarios.put_scenario_qualifiers.__doc__ += post_put_scenario_qualifiers_response  # type: ignore [operator]

Scenarios.post_scenario_wells.__doc__ += post_put_scenario_wells_response  # type: ignore [operator]
Scenarios.put_scenario_wells.__doc__ += post_put_scenario_wells_response  # type: ignore [operator]
