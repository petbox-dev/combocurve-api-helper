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

    def get_users_roles_url(self) -> str:
        """
        Returns the API url for company users and their roles.
        """
        return f'{self.API_BASE_URL}/users/roles'

    def get_project_custom_columns_url(
        self, project_id: str, collection: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Returns the API url for a project's custom columns for a given collection.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/custom-columns/{collection}'
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

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        url = self.get_custom_columns_url(collection, filters)
        columns = self._get_items(url)
        return columns[0]

    def get_custom_columns_wells(self, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Wells.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        return self.get_custom_columns('wells', filters)

    def get_custom_columns_daily_production(self, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Daily Production.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        return self.get_custom_columns('daily-productions', filters)

    def get_custom_columns_monthly_production(self, filters: Optional[Dict[str, str]] = None) -> Item:
        """
        Returns a list of custom columns for Monthly Production.

        https://docs.api.combocurve.com/api/get-custom-columns
        """
        return self.get_custom_columns('monthly-productions', filters)

    def patch_well_identifiers(self, data: ItemList) -> ItemList:
        """
        Update well identifiers.

        https://docs.api.combocurve.com/api/patch-wells-identifiers

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

        https://docs.api.combocurve.com/api/get-tags

        Example response:
        [
            {
                "createdAt": "2020-01-01",
                "description": "string",
                "name": "Example",
                "updatedAt": "2020-01-01"
            }
        ]
        """
        url = self.get_tags_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_root_econ_runs(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of econ runs.

        https://docs.api.combocurve.com/api/get-root-econ-runs
        """
        url = self.get_root_econ_runs_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_root_econ_run_by_id(self, id: str) -> Item:
        """
        Returns a specific econ run from its econ run id.

        https://docs.api.combocurve.com/api/get-root-econ-run-by-id
        """
        url = self.get_root_econ_run_by_id_url(id)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)[0]

    def get_root_forecast_daily_volumes(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily volumes.

        https://docs.api.combocurve.com/api/get-root-forecast-daily-volumes
        """
        url = self.get_root_forecast_daily_volumes_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_root_forecast_monthly_volumes(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly volumes.

        https://docs.api.combocurve.com/api/get-root-forecast-monthly-volumes
        """
        url = self.get_root_forecast_monthly_volumes_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_users_roles(self) -> ItemList:
        """
        Returns a list of company users and their roles.

        https://docs.api.combocurve.com/api/get-users-roles

        Example response:
        [
            {
                "userId": "5e272d38b78910dd2a1bd691",
                "firstName": "string",
                "lastName": "string",
                "email": "string",
                "resourceRoles": [
                    {
                        "resourceId": "5e272d38b78910dd2a1bd691",
                        "resourceType": "string",
                        "roles": [
                            "string"
                        ]
                    }
                ]
            }
        ]
        """
        url = self.get_users_roles_url()
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_project_custom_columns(
        self, project_id: str, collection: str, filters: Optional[Dict[str, str]] = None
    ) -> Item:
        """
        Returns a project's custom columns for a given collection (e.g. 'wells',
        'daily-productions', 'monthly-productions'). The project-scoped counterpart
        to `get_custom_columns`.

        https://docs.api.combocurve.com/api/get-project-custom-columns

        Example response:
        [
            {
                "headerName": "string",
                "headerType": "string",
                "headerLabel": "string"
            }
        ]
        """
        url = self.get_project_custom_columns_url(project_id, collection, filters)
        columns = self._get_items(url)
        return columns[0]
