from collections.abc import Sequence
from typing import Optional, cast

from .base import APIBase, Item, ItemList, QueryFilters, WriteResponse

GET_LIMIT = 200


class ForecastConfigurations(APIBase):
    ######
    # URLs
    ######

    def get_forecast_configurations_url(self, filters: Optional[QueryFilters] = None) -> str:
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
        Deletes forecast configurations by id: each id is sent as a repeated `id` query parameter. A
        configuration owned by another user is a per-record 403, and an unknown id is a per-record 404;
        the 207 envelope reports each record, so neither raises.

        The route takes at most 100 ids per request, which the API docs do not state: 101 ids answered
        500, and 500 ids answered 431 (the URL is too long) on dev, 2026-11-21. A longer `ids` list is
        de-duplicated and sent in requests of 100, and the list holds one envelope per request. The
        requests are independent: a failed later request leaves the earlier deletes applied. An empty
        `ids`, a bare `str`, or an empty id raises `ValueError` before anything is sent.

        https://docs.api.combocurve.com/api/delete-forecast-configurations

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "id": "5e272d38b78910dd2a1bd691",
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
        """
        envelopes: ItemList = []
        for batch_filters in self._filter_value_batches({'id': self._require_id_sequence(ids, 'ids')}, 'id'):
            envelopes.extend(self._delete_items(self.get_forecast_configurations_url(batch_filters), data=[]))
        return cast('list[WriteResponse]', envelopes)
