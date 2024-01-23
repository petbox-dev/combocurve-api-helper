from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200
GET_LIMIT_OUTPUTS_ARIES = 1000


class Forecasts(APIBase):
    ######
    # URLs
    ######

    def get_forecasts_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of forecasts for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_forecast_by_id_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url for a specific forecast from its forecast id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}'


    def get_forecast_aries_url(self, project_id: str, forecast_id: str,
                               filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific forecast's ARIES parameters from its forecast id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}/aries'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_forecast_outputs_url(self, project_id: str, forecast_id: str,
                                 filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific forecast outputs from its forecast id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}/outputs'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_forecast_output_by_id_url(self, project_id: str, forecast_id: str, output_id: str) -> str:
        """
        Returns the API url for a specific forecast output from its forecast id and output id.
        """
        return f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}/outputs/{output_id}'


    def get_forecast_daily_volumes_url(self, project_id: str, forecast_id: str,
                                       filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for daily volumes for a specific project id and forecast id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}/daily-volumes'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_forecast_monthly_volumes_url(self, project_id: str, forecast_id: str,
                                         filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for monthly volumes for a specific project id and forecast id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/forecasts/{forecast_id}/monthly-volumes'
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


    def get_forecasts(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of forecasts for a specific project id.
        """
        url = self.get_forecasts_url(project_id, filters)
        params = {'take': GET_LIMIT}
        forecasts = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(forecasts, order)


    def get_forecast_by_id(self, project_id: str, forecast_id: str) -> Item:
        """
        Returns a specific forecast from its forecast id.
        """
        url = self.get_forecast_by_id_url(project_id, forecast_id)
        params = {'take': GET_LIMIT}
        forecasts = self._get_items(url, params)

        return forecasts[0]


    def get_forecast_aries(self, project_id: str, forecast_id: str,
                           filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of ARIES parameters for a specific project id and forecast id.
        """
        url = self.get_forecast_aries_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)


    def get_forecast_outputs(self, project_id: str, forecast_id: str,
                             filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of outputs for a specific project id and forecast id.
        """
        url = self.get_forecast_outputs_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)


    def get_forecast_output_by_id(self, project_id: str, forecast_id: str, output_id: str) -> Item:
        """
        Returns a specific forecast output from its forecast id and output id.
        """
        url = self.get_forecast_output_by_id_url(project_id, forecast_id, output_id)
        params = {'take': GET_LIMIT}
        outputs = self._get_items(url, params)

        return outputs[0]


    def get_forecast_daily_volumes(self, project_id: str, forecast_id: str,
                                   filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily volumes for a specific project id and forecast id.
        """
        url = self.get_forecast_daily_volumes_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        daily_volumes = self._get_items(url, params)

        order = {
            'well': 0,
        }
        return self._keysort(daily_volumes, order)


    def get_forecast_monthly_volumes(self, project_id: str, forecast_id: str,
                                     filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly volumes for a specific project id and forecast id.
        """
        url = self.get_forecast_monthly_volumes_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        monthly_volumes = self._get_items(url, params)

        order = {
            'well': 0,
        }
        return self._keysort(monthly_volumes, order)
