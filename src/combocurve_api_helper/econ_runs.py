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

    # this happens is a well has no economic output, i.e. no forecast or
    # ownership model. In this case some basic header information exists,
    # but the 'output' key is None. We return only the header data.
    if output is None:
        return {**result}  # type: ignore[unreachable]

    if not isinstance(output, dict):
        raise TypeError(f'Expected output to be a dict, got {type(output)}')

    out = {k: v for k, v in output.items()}
    return {**result, **out}


class EconRuns(APIBase):
    ######
    # URLs
    ######

    def get_econ_runs_url(self, project_id: str, scenario_id: str) -> str:
        """
        Returns the API url of econ runs for a specific project id and
        scenario id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/scenarios/{scenario_id}/econ-runs'


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
        econruns = self._get_items(url)

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
            # if item is not None
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
