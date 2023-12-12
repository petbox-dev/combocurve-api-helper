from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class Projects(APIBase):
    ######
    # URLs
    ######

    def get_projects_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for projects.
        """
        url = f'{self.API_BASE_URL}/projects'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_by_id_url(self, project_id: str) -> str:
        """
        Returns the API url for a specific project from its project id.
        """
        base_url = self.get_projects_url()
        return f'{base_url}/{project_id}'


    ###########
    # API calls
    ###########


    def get_projects(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of projects.
        """
        url = self.get_projects_url(filters)
        params = {'take': GET_LIMIT}
        projects = self._get_items(url, params=params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(projects, order)


    def get_project_by_id(self, id: str) -> Item:
        """
        Returns a specific project from its project id.
        """
        url = self.get_project_by_id_url(id)
        projects = self._get_items(url)

        return projects[0]
