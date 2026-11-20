from collections.abc import Sequence
from typing import Optional, cast

from .base import APIBase, Item, ItemList, WellFilters, WriteResponse

GET_LIMIT = 200


class ForecastConfigurations(APIBase):
    ######
    # URLs
    ######

    def get_forecast_configurations_url(self, filters: Optional[WellFilters] = None) -> str:
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

    def get_forecast_configurations(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of forecast configurations. These are the reusable
        forecast-run presets referenced by `post_forecast_run`.

        https://docs.api.combocurve.com/api/get-forecast-configurations

        The example response is large; see it on the docs page linked above.
        """
        url = self.get_forecast_configurations_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def count_forecast_configurations(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of forecast configurations matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-forecast-configurations
        """
        return self._count_items(self.get_forecast_configurations_url(filters))

    def get_forecast_configuration_by_id(self, forecast_configuration_id: str) -> Item:
        """
        Returns a specific forecast configuration from its id.

        https://docs.api.combocurve.com/api/get-forecast-configuration-by-id

        The example response is large; see it on the docs page linked above.
        """
        url = self.get_forecast_configuration_by_id_url(forecast_configuration_id)
        return self._get_items(url)[0]

    def post_forecast_configurations(self, data: ItemList) -> list[WriteResponse]:
        """
        Creates one or more forecast configurations.

        https://docs.api.combocurve.com/api/post-forecast-configurations

        The example request and response are large; see them on the docs page linked above.
        """
        url = self.get_forecast_configurations_url()
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_forecast_configurations(self, data: ItemList) -> list[WriteResponse]:
        """
        Upserts one or more forecast configurations.

        https://docs.api.combocurve.com/api/put-forecast-configurations

        The example request and response are large; see them on the docs page linked above.
        """
        url = self.get_forecast_configurations_url()
        return cast('list[WriteResponse]', self._put_items(url, data))

    def patch_forecast_configurations(self, data: ItemList) -> list[WriteResponse]:
        """
        Partially updates one or more forecast configurations.

        https://docs.api.combocurve.com/api/patch-forecast-configurations

        The example request and response are large; see them on the docs page linked above.
        """
        url = self.get_forecast_configurations_url()
        return cast('list[WriteResponse]', self._patch_items(url, data))

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

    def delete_forecast_configurations(self, ids: Sequence[str]) -> list[WriteResponse]:
        """
        Deletes forecast configurations by id in one request: each id is sent as a repeated `id` query
        parameter. A configuration owned by another user is a per-record 403, and an unknown id is a
        per-record 404; the response reports each record.

        https://docs.api.combocurve.com/api/delete-forecast-configurations
        """
        url = self.get_forecast_configurations_url({'id': self._require_id_sequence(ids, 'ids')})
        return cast('list[WriteResponse]', self._delete_items(url, data=[]))
