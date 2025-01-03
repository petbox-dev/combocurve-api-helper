from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, TypedDict, cast

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class Root(APIBase):
    ######
    # URLs
    ######

    def get_custom_columns_url(self, collection: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for custom columns.
        """
        url = f'{self.API_BASE_URL}/custom-columns/{collection}'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_well_identifiers_url(self) -> str:
        """
        Returns the API url for well identifiers.
        """
        return f'{self.API_BASE_URL}/well-identifiers'


    def get_tags_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for tags.
        """
        url = f'{self.API_BASE_URL}/tags'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_root_econ_runs_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for econ runs.
        """
        url = f'{self.API_BASE_URL}/econ-runs'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_root_econ_run_by_id_url(self, econrun_id: str) -> str:
        """
        Returns the API url for a specific econ run from its econ run id.
        """
        return f'{self.API_BASE_URL}/econ-runs/{econrun_id}'


    def get_root_forecast_daily_volumes_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for daily volumes.
        """
        url = f'{self.API_BASE_URL}/forecasts/daily-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_root_forecast_monthly_volumes_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for monthly volumes.
        """
        url = f'{self.API_BASE_URL}/forecasts/monthly-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    ###########
    # API calls
    ###########


    def get_custom_columns(self, collection: str, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns. See other convenience methods for specific collections.

        https://docs.api.combocurve.com/#3c047d2a-db2c-419f-9187-1a4db81215eb
        """
        url = self.get_custom_columns_url(collection, filters)
        columns = self._get_items(url)
        return columns[0]


    def get_custom_columns_wells(self, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Wells.

        https://docs.api.combocurve.com/#3c047d2a-db2c-419f-9187-1a4db81215eb
        """
        return self.get_custom_columns('wells', filters)


    def get_custom_columns_daily_production(self, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Daily Production.

        https://docs.api.combocurve.com/#3c047d2a-db2c-419f-9187-1a4db81215eb
        """
        return self.get_custom_columns('daily-productions', filters)


    def get_custom_columns_monthly_production(self, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Monthly Production.

        https://docs.api.combocurve.com/#3c047d2a-db2c-419f-9187-1a4db81215eb
        """
        return self.get_custom_columns('monthly-productions', filters)


    def patch_well_identifiers(self, data: ItemList) -> ItemList:
        """
        Update well identifiers.

        https://docs.api.combocurve.com/#7d7f9a19-e693-4b59-9769-71efd58cba31

        Structure of data:
        [
            ...,
            {
                "wellId": "5e272d39b78210dd2a1bd8fe", // required
                        "newInfo": { // at least one of them.
                            "chosenKeyID": "api14",
                            "companyScope": true,
                            "dataSource": "internal"
                        }
            },
            ...
        ]
        """
        url = self.get_well_identifiers_url()
        return self._patch_items(url, data)


    def get_tags(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of tags.

        https://docs.api.combocurve.com/#17a1bfdc-e23e-4b4a-a033-4dc31fb4e35a

        Example response:
        [
            {
                "createdAt": "2021-07-27T17:52:28.791Z",
                "name": "Test tag",
                "description": "Test tag description",
                "updatedAt": "2021-07-27T17:52:28.791Z"
            },
            {
                "createdAt": "2021-07-27T17:52:28.791Z",
                "name": "Test tag 2",
                "description": "Test tag 2 description",
                "updatedAt": "2021-07-27T17:52:28.791Z"
            }
        ]
        """
        url = self.get_tags_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_root_econ_runs(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ runs.

        https://docs.api.combocurve.com/#489ddb62-4cdd-4470-a572-00dc0e10e73b
        """
        url = self.get_root_econ_runs_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_root_econ_run_by_id(self, id: str) -> Item:
        """
        Returns a specific econ run from its econ run id.

        https://docs.api.combocurve.com/#bba4ff40-fd07-4ce2-a2c7-368a97e99e93
        """
        url = self.get_root_econ_run_by_id_url(id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)[0]


    def get_root_forecast_daily_volumes(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily volumes.

        https://docs.api.combocurve.com/#351629d8-78f0-459c-9463-ba4ffb9675d3
        """
        url = self.get_root_forecast_daily_volumes_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)


    def get_root_forecast_monthly_volumes(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly volumes.

        https://docs.api.combocurve.com/#26cc17ce-3c64-44f0-82c8-e3fe9243e191
        """
        url = self.get_root_forecast_monthly_volumes_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)
