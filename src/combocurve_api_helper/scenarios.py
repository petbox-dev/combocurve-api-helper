import requests  # type: ignore
import warnings

from combocurve_api_v1.pagination import get_next_page_url  # type: ignore

from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList


GET_LIMIT = 200
GET_LIMIT_MONTHLY_EXPORTS = 100
CONCURRENCY_MONTHLY_EXPORTS = 10


def flatten_outputs(result: Item) -> Optional[Item]:
    if 'output' not in result:
        return None

    output = result.pop('output')

    if not isinstance(output, dict):
        raise TypeError(f'Expected output to be a dict, got {type(output)}')

    out = {k: v for k, v in output.items()}
    return {**result, **out}


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

        VALID_ECON_NAMES = (
            'capex',
            'dates',
            'depreciations',
            'escalation',
            'expenses',
            'forecast',
            'pSeries',
            'network',
            'ownershipReversion',
            'pricing',
            'differentials',
            'productionTaxes',
            'actualOrForecast',
            'reservesCategory',
            'risking',
            'schedule',
            'streamProperties',
            'emission'
        )

        if econ_name is None:
            return url
        elif econ_name.casefold() not in (n.casefold() for n in VALID_ECON_NAMES):
            warnings.warn(f'Econ name is not in list of valid econ names:\n{VALID_ECON_NAMES}')

        return f'{url}?econName={econ_name}'


    def get_scenario_wells_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url for well assignments for a specific project id and
        scenario id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        return f'{self.API_BASE_URL}/projects/{project_id}/scenarios/{scenario_id}/well-assignments'


    def get_econ_runs_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url of econ runs for a specific project id and
        scenario id.
        """
        base_url = self.get_scenario_by_id_url(project_id, scenario_id)
        return f'{base_url}/econ-runs'


    def get_econ_run_by_id_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for a specific econ run from its econ run id.
        """
        base_url = self.get_econ_runs_url(project_id, scenario_id)
        return f'{base_url}/{econ_run_id}'


    def get_econ_run_onelines_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for onelines for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/one-liners'


    def get_econ_run_combo_names_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for onelines for a specific project id, scenario id,
        and econ run id.
        """
        base_url = self.get_econ_run_onelines_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/combo-names'


    def get_econ_run_monthly_export_id_url(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Returns the API url for monthly exports for a specific project id,
        scenario id, and econ run id.
        """
        base_url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/monthly-exports'


    def get_econ_run_monthly_export_url(self, project_id: str, scenario_id: str, econ_run_id: str,
                                        monthly_export_id: str) -> str:
        """
        Returns the API url for monthly exports for a specific project id,
        scenario id, econ run id,
        and monthly export id.
        """
        base_url = self.get_econ_run_monthly_export_id_url(project_id, scenario_id, econ_run_id)
        return f'{base_url}/{monthly_export_id}'


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


    def get_econ_runs(self, project_id: str, scenario_id: str, add_combo_names: bool = True) -> ItemList:
        """
        Returns a list of econ runs for a specific project id and scenario id.

        `add_combo_names` will add the list of combo names to each econ run.
        """
        url = self.get_econ_runs_url(project_id, scenario_id)
        params = {'take': GET_LIMIT}
        econruns = self._get_items(url, params)

        if add_combo_names:
            self.update_econ_run_combo_names(econruns, project_id, scenario_id)

        order = {
            'id': 2,
            'status': 1,
            'runDate': 0,
        }
        return self._keysort(econruns, order, reverse=True)


    def get_econ_run_by_id(self, project_id: str, scenario_id: str, econ_run_id: str,
                           add_combo_names: bool = True) -> Item:
        """
        Returns a specific econ run from its econ run id.

        `add_combo_names` will add the list of combo names to the econ run.
        """
        url = self.get_econ_run_by_id_url(project_id, scenario_id, econ_run_id)
        params = {'take': GET_LIMIT}
        econruns = self._get_items(url, params)

        if add_combo_names:
            self.update_econ_run_combo_names(econruns, project_id, scenario_id)

        order = {
            'id': 2,
            'status': 1,
            'runDate': 0,
        }
        return self._keysort(econruns, order, reverse=True)[0]


    def get_econ_run_combo_names(self, project_id: str, scenario_id: str, econ_run_id: str) -> List[str]:
        """
        Returns a list of combo names for a specific project id, scenario id,
        and econ run id.
        """
        url = self.get_econ_run_combo_names_url(project_id, scenario_id, econ_run_id)
        params = {'take': GET_LIMIT}
        data = self._get_items(url, params)

        return cast(List[str], sorted(set(data)))


    def get_econ_run_onelines(self, project_id: str, scenario_id: str, econ_run_id: str) -> ItemList:
        """
        Returns a list of onelines for a specific project id, scenario id,
        and econ run id.
        """
        url = self.get_econ_run_onelines_url(project_id, scenario_id, econ_run_id)

        # in this specific case we do some post-processing to "flatten" the results
        # into the expected type of: ItemList
        params = {'take': GET_LIMIT}
        items = self._get_items(url, params)

        onelines = [
            item for item in
            (flatten_outputs(item) for item in items)
            if item is not None
        ]

        return onelines


    def update_econ_run_combo_names(self, econruns: ItemList, project_id: str, scenario_id: str) -> None:
        """
        Add combo names to the econ run data.
        """
        for i, run in enumerate(econruns):
            econ_run_id = str(run['id'])
            combo_names = self.get_econ_run_combo_names(project_id, scenario_id, econ_run_id)
            run['comboNames'] = combo_names
            # _ = run.pop('outputParams')
            econruns[i] = run

        return


    def post_econ_run_monthly_export(self, project_id: str, scenario_id: str, econ_run_id: str) -> str:
        """
        Create a monthly export for a specific project id, scenario id,
        econ run id, and returns a monthly export id to get the results.
        """
        url = self.get_econ_run_monthly_export_id_url(project_id, scenario_id, econ_run_id)

        items = self._post_items(url, data=[])
        id_ = str(items[0]['id'])

        return id_


    def get_econ_run_monthly_export(
            self, project_id: str, scenario_id: str, econ_run_id: str, monthly_export_id: str) -> ItemList:
        """
        Returns a list of monthly exports for a specific project id,
        scenario id, econ run id, and monthly export id.
        """
        url = self.get_econ_run_monthly_export_url(project_id, scenario_id, econ_run_id, monthly_export_id)

        params = {
            'take': GET_LIMIT_MONTHLY_EXPORTS,
            'concurrency': CONCURRENCY_MONTHLY_EXPORTS,
        }
        items = self._get_items(url, params)

        results = cast(ItemList, items[0]['results'])

        results_flat = [
            result for result in
            (flatten_outputs(result) for result in results)
            if result is not None
        ]
        return results_flat


    def get_stream_econ_run_monthly_export(
            self, project_id: str, scenario_id: str, econ_run_id: str, monthly_export_id: str) -> Iterator[ItemList]:
        """
        Similar to `get_econ_run_monthly_export` but instead streams the data
        yielding chunks of 100 items at a time, where each item is a list of
        monthly exports for a specific project id, scenario id, econ run id,
        and monthly export id.
        """
        url = self.get_econ_run_monthly_export_url(project_id, scenario_id, econ_run_id, monthly_export_id)

        params = {
            'take': GET_LIMIT_MONTHLY_EXPORTS,
            'concurrency': CONCURRENCY_MONTHLY_EXPORTS,
        }
        iter_items = self._get_items_iterator(url, params)

        for items in iter_items:
            for item in items:
                results = cast(ItemList, item['results'])

                results_flat = [
                    result for result in
                    (flatten_outputs(result) for result in results)
                    if result is not None
                ]
                yield results_flat
