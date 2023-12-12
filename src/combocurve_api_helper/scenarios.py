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


    def get_scenario_combos_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url for combos for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        return f'{base_url}/combos'


    def get_scenario_qualifiers_url(self, project_id: str, scenario_id: str, econ_name: Optional[str] = None) -> str:
        """
        Returns the API url for qualifiers for a specific project id,
        scenario id, and optionally, econ name.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        url = f'{base_url}/qualifiers'

        if econ_name is None:
            return url
        elif econ_name.casefold() not in (n.casefold() for n in self.econ_model_types):
            warnings.warn(f'`econ_name` is not in list of valid names:\n{self.econ_model_types}')

        return f'{url}?econName={econ_name}'


    def get_scenario_wells_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url for well assignments for a specific project id and
        scenario id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        return f'{self.API_BASE_URL}/projects/{project_id}/scenarios/{scenario_id}/well-assignments'


    ###########
    # API calls
    ###########


    def get_scenarios(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of project scenarios scoped from the project's id.
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


    def get_scenario_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific project scenario from its scenario id.
        """
        url = self.get_scenario_by_id_url(project_id, id)
        scenarios = self._get_items(url)

        return scenarios[0]


    def get_scenario_combos(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns a list of combos for a specific project id and scenario id.
        """
        url = self.get_scenario_combos_url(project_id, scenario_id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_scenario_qualifiers(self, project_id: str, scenario_id: str, econ_name: Optional[str]) -> ItemList:
        """
        Returns a list of qualifiers for a specific project id, scenario id and
        econ name.
        """
        url = self.get_scenario_qualifiers_url(project_id, scenario_id, econ_name)
        return self._get_items(url)


    def get_scenario_wells(self, project_id: str, scenario_id: str) -> ItemList:
        """
        Returns a list of well assignments for a specific project id and
        scenario id.
        """
        url = self.get_scenario_wells_url(project_id, scenario_id)
        return self._get_items(url)
