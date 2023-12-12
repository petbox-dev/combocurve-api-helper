from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 1000
PATCH_LIMIT = 1000


class Wells(APIBase):
    ######
    # URLs
    ######

    def get_company_wells_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for company wells.
        """
        url = f'{self.API_BASE_URL}/wells'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_company_well_by_id_url(self, id: str) -> str:
        """
        Returns the API url for a specific company well from its well id.
        """
        return f'{self.API_BASE_URL}/wells/{id}'


    def get_project_company_wells_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for project company wells scoped from the
        project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/company-wells'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_company_well_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url for a specific project company well from its
        well id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/company-wells/{id}'


    def get_project_wells_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for project wells scoped from the project's id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/wells'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_well_by_id_url(self, project_id: str, id: str) -> str:
        """
        Returns the API url for a specific project well from its well id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/wells/{id}'


    def get_well_comments_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for well comments.
        """
        url = f'{self.API_BASE_URL}/well-comments'
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

    def get_company_wells(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company wells.
        """
        url = self.get_company_wells_url(filters)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(wells, order)


    def get_company_well_by_id(self, id: str) -> Item:
        """
        Returns a specific company well from its well id.
        """
        url = self.get_company_well_by_id_url(id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]


    def get_project_company_wells(self, project_id: str,
                                  filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of project company wells scoped from the project's id.
        """
        url = self.get_project_company_wells_url(project_id, filters)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(wells, order)


    def get_project_company_well_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific project company well from its well id.
        """
        url = self.get_project_company_well_by_id_url(project_id, id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]


    def get_project_wells(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of project wells scoped from the project's id.
        """
        url = self.get_project_wells_url(project_id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(wells, order)


    def get_project_well_by_id(self, project_id: str, id: str) -> Item:
        """
        Returns a specific project well from its well id.
        """
        url = self.get_project_well_by_id_url(project_id, id)
        params = {'take': GET_LIMIT}
        wells = self._get_items(url, params)

        return wells[0]


    def patch_company_wells(self, data: ItemList) -> ItemList:
        """
        Updates a list of company wells.
        """
        url = self.get_company_wells_url()
        wells = self._patch_items(url, data, PATCH_LIMIT)

        return wells


    def patch_company_well_by_id(self, id: str, data: Item) -> ItemList:
        """
        Updates a specific company well from its well id.
        """
        url = self.get_company_well_by_id_url(id)
        wells = self._patch_items(url, [data])

        return wells


    def patch_project_company_wells(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates a list of project company wells scoped from the project's id.
        """
        url = self.get_project_company_wells_url(project_id)
        wells = self._patch_items(url, data, PATCH_LIMIT)

        return wells


    def patch_project_company_well_by_id(self, project_id: str, id: str, data: Item) -> ItemList:
        """
        Updates a specific project company well from its well id.
        """
        url = self.get_project_company_well_by_id_url(project_id, id)
        wells = self._patch_items(url, [data])

        return wells


    def patch_project_wells(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates a list of project wells scoped from the project's id.
        """
        url = self.get_project_wells_url(project_id)
        wells = self._patch_items(url, data, PATCH_LIMIT)

        return wells


    def patch_project_well_by_id(self, project_id: str, id: str, data: Item) -> ItemList:
        """
        Updates a specific project well from its well id.
        """
        url = self.get_project_well_by_id_url(project_id, id)
        wells = self._patch_items(url, [data])

        return wells
