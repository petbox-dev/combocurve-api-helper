from typing import Dict, Optional

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class ForecastConfigurations(APIBase):
    ######
    # URLs
    ######

    def get_forecast_configurations_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for forecast configurations.
        """
        url = f'{self.API_BASE_URL}/forecast-configurations'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_forecast_configuration_by_id_url(self, forecast_configuration_id: str) -> str:
        """
        Returns the API url for a specific forecast configuration from its id.
        """
        base_url = self.get_forecast_configurations_url()
        return f'{base_url}/{forecast_configuration_id}'

    ###########
    # API calls
    ###########

    def get_forecast_configurations(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of forecast configurations. These are the reusable
        forecast-run presets referenced by `post_forecast_run`.

        https://docs.api.combocurve.com/api/get-forecast-configurations

        The example response is large; see it on the docs page linked above.
        """
        url = self.get_forecast_configurations_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_forecast_configuration_by_id(self, forecast_configuration_id: str) -> Item:
        """
        Returns a specific forecast configuration from its id.

        https://docs.api.combocurve.com/api/get-forecast-configuration-by-id

        The example response is large; see it on the docs page linked above.
        """
        url = self.get_forecast_configuration_by_id_url(forecast_configuration_id)
        return self._get_items(url)[0]

    def post_forecast_configurations(self, data: ItemList) -> ItemList:
        """
        Creates one or more forecast configurations.

        https://docs.api.combocurve.com/api/post-forecast-configurations

        The example request and response are large; see them on the docs page linked above.
        """
        url = self.get_forecast_configurations_url()
        return self._post_items(url, data)

    def put_forecast_configurations(self, data: ItemList) -> ItemList:
        """
        Upserts one or more forecast configurations.

        https://docs.api.combocurve.com/api/put-forecast-configurations

        The example request and response are large; see them on the docs page linked above.
        """
        url = self.get_forecast_configurations_url()
        return self._put_items(url, data)

    def patch_forecast_configurations(self, data: ItemList) -> ItemList:
        """
        Partially updates one or more forecast configurations.

        https://docs.api.combocurve.com/api/patch-forecast-configurations

        The example request and response are large; see them on the docs page linked above.
        """
        url = self.get_forecast_configurations_url()
        return self._patch_items(url, data)

    def delete_forecast_configuration_by_id(self, forecast_configuration_id: str) -> ItemList:
        """
        Deletes a specific forecast configuration from its id.

        https://docs.api.combocurve.com/api/delete-forecast-configuration-by-id

        Example response:
        {
            "name": "Example",
            "message": "string",
            "details": {
                "location": "string"
            }
        }
        """
        url = self.get_forecast_configuration_by_id_url(forecast_configuration_id)
        return self._delete_items(url, data=[])
