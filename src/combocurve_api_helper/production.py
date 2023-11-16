from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 20_000
POST_LIMIT = 20_000
PUT_LIMIT = 20_000
PATCH_LIMIT = 20_000


class Forecasts(APIBase):
    ######
    # URLs
    ######

    def get_project_monthly_productions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's monthly production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/monthly-productions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_daily_productions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's daily production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/daily-productions'
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


    def get_project_monthly_productions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly production items for a specific project id.
        """
        url = self.get_project_monthly_productions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_project_daily_productions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily production items for a specific project id.
        """
        url = self.get_project_daily_productions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)
