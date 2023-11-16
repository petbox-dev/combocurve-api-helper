from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList


GET_LIMIT = 1000


class Directional(APIBase):
    ######
    # URLs
    ######

    def get_directional_surveys_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of directional surveys for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/directional-surveys'
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


    def get_directional_surveys(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of directional survey items for a specific project id.
        """
        url = self.get_directional_surveys_url(project_id, filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)
