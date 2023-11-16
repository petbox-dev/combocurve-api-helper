from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class TypeCurves(APIBase):
    ######
    # URLs
    ######

    def get_type_curves_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of type curves for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/type-curves'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_type_curve_by_id_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for a specific type curve from its type curve id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/type-curves/{type_curve_id}'


    def get_type_curve_representative_wells_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for representative wells for a specific project id and type curve id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/type-curves/{type_curve_id}/representative-wells'


    def get_type_curve_daily_fits_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for daily fits for a specific project id and type curve id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/type-curves/{type_curve_id}/daily-fits'


    def get_type_curve_monthly_fits_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for monthly fits for a specific project id and type curve id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/type-curves/{type_curve_id}/monthly-fits'


    ###########
    # API calls
    ###########


    def get_type_curves(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of type curves for a specific project id.
        """
        url = self.get_type_curves_url(project_id, filters)
        params = {'take': GET_LIMIT}
        type_curves = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(type_curves, order)


    def get_type_curve_by_id(self, project_id: str, type_curve_id: str) -> Item:
        """
        Returns a specific type curve from its type curve id.
        """
        url = self.get_type_curve_by_id_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        type_curves = self._get_items(url, params)

        return type_curves[0]


    def get_type_curve_representative_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Returns a list of representative wells for a specific project id and type curve id.
        """
        url = self.get_type_curve_representative_wells_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        representative_wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 1,
        }
        return self._keysort(representative_wells, order)


    def get_type_curve_daily_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Returns a list of daily fits for a specific project id and type curve id.
        """
        url = self.get_type_curve_daily_fits_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        daily_fits = self._get_items(url, params)
        return daily_fits


    def get_type_curve_monthly_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Returns a list of monthly fits for a specific project id and type curve id.
        """
        url = self.get_type_curve_monthly_fits_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        monthly_fits = self._get_items(url, params)
        return monthly_fits
