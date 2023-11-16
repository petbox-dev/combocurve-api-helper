from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class Root(APIBase):
    ######
    # URLs
    ######

    def get_custom_columns_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for custom columns.
        """
        url = f'{self.API_BASE_URL}/custom-columns'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_tags_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for tags.
        """
        url = f'{self.API_BASE_URL}/tags'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_root_econ_runs_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for econ runs.
        """
        url = f'{self.API_BASE_URL}/econ-runs'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_root_econ_run_by_id_url(self, id: str) -> str:
        """
        Returns the API url for a specific econ run from its econ run id.
        """
        return f'{self.API_BASE_URL}/econ-runs/{id}'


    def get_root_forecast_daily_volumes_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for daily volumes.
        """
        url = f'{self.API_BASE_URL}/forecasts/daily-volumes'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_root_forecast_monthly_volumes_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for monthly volumes.
        """
        url = f'{self.API_BASE_URL}/forecasts/monthly-volumes'
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


    def get_tags(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of tags.
        """
        url = self.get_tags_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_root_econ_runs(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ runs.
        """
        url = self.get_root_econ_runs_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_root_econ_run_by_id(self, id: str) -> Item:
        """
        Returns a specific econ run from its econ run id.
        """
        url = self.get_root_econ_run_by_id_url(id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)[0]


    def get_root_forecast_daily_volumes(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily volumes.
        """
        url = self.get_root_forecast_daily_volumes_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_root_forecast_monthly_volumes(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly volumes.
        """
        url = self.get_root_forecast_monthly_volumes_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)
