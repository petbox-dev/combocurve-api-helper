from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional, cast

from requests.structures import CaseInsensitiveDict

from .base import APIBase, ItemList, WriteResponse

GET_LIMIT = 20_000
POST_LIMIT = 20_000
PUT_LIMIT = 20_000
PATCH_LIMIT = 20_000


def _delete_filters(
    well_id: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict[str, str]:
    """Build the query string for a production DELETE.

    The production delete endpoints take `well`, `startDate` and `endDate` as
    **query parameters**, not as a request body -- sending them as a body returns
    `400 Bad Request` (verified live 2026-08-06 against a project monthly delete).

    At least one filter is required. An unfiltered delete would remove every
    production record in scope, which no caller can plausibly want by accident,
    so it is refused here rather than sent. This mirrors `delete_company_wells`.

    Note that omitting `well_id` applies the date range to **every** well in
    scope, which is documented API behaviour and is why the guard demands only
    that *some* filter be present rather than requiring the well.
    """
    if well_id is None and start_date is None and end_date is None:
        raise ValueError('Must provide at least one of well_id, start_date, or end_date')

    filters: dict[str, str] = {}
    if well_id is not None:
        filters['well'] = well_id

    if start_date is not None:
        filters['startDate'] = start_date

    if end_date is not None:
        filters['endDate'] = end_date

    return filters


# Production rows are identified by well then date.
_PRODUCTION_SORT_ORDER: Mapping[str, int] = MappingProxyType({'well': 0, 'date': 1})


class Production(APIBase):
    ######
    # URLs
    ######

    def get_company_monthly_productions_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for company monthly production.
        """
        url = f'{self.API_BASE_URL}/monthly-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_company_daily_productions_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for company daily production.
        """
        url = f'{self.API_BASE_URL}/daily-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_project_monthly_productions_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's monthly production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/monthly-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_project_daily_productions_url(self, project_id: str, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's daily production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/daily-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    ###########
    # API calls
    ###########

    def get_company_monthly_productions(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company monthly production items.

        https://docs.api.combocurve.com/api/get-monthly-productions
        """
        url = self.get_company_monthly_productions_url(filters)
        params = {'take': GET_LIMIT}
        monthly_production = self._get_items(url, params)

        return self._keysort(monthly_production, _PRODUCTION_SORT_ORDER)

    def post_company_monthly_productions(self, data: ItemList) -> list[WriteResponse]:
        """
        Creates monthly production items.

        https://docs.api.combocurve.com/api/post-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = cast('list[WriteResponse]', self._post_items(url, data))

        return monthly_production

    def put_company_monthly_productions(self, data: ItemList) -> list[WriteResponse]:
        """
        Upserts monthly production items.

        https://docs.api.combocurve.com/api/put-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = cast('list[WriteResponse]', self._put_items(url, data))

        return monthly_production

    def patch_company_monthly_productions(self, data: ItemList) -> list[WriteResponse]:
        """
        Updates monthly production items.

        https://docs.api.combocurve.com/api/patch-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = cast('list[WriteResponse]', self._patch_items(url, data))

        return monthly_production

    def delete_company_monthly_productions(
        self,
        well_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes company monthly production records.

        https://docs.api.combocurve.com/api/delete-monthly-productions

        Filters are query parameters; see `_delete_filters` for why, and for the
        at-least-one-filter requirement.

        Returns the delete response headers, where 'X-Delete-Count' is the number
        of production records deleted.
        """
        url = self.get_company_monthly_productions_url(_delete_filters(well_id, start_date, end_date))
        responses = self._delete_responses(url, data=[])

        return responses[0].headers

    def get_company_daily_productions(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company monthly production items.

        https://docs.api.combocurve.com/api/get-daily-productions
        """
        url = self.get_company_daily_productions_url(filters)
        params = {'take': GET_LIMIT}
        dailiy_production = self._get_items(url, params)

        return self._keysort(dailiy_production, _PRODUCTION_SORT_ORDER)

    def post_company_daily_productions(self, data: ItemList) -> list[WriteResponse]:
        """
        Creates daily production items.

        https://docs.api.combocurve.com/api/post-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = cast('list[WriteResponse]', self._post_items(url, data))

        return daily_production

    def put_company_daily_productions(self, data: ItemList) -> list[WriteResponse]:
        """
        Upserts daily production items.

        https://docs.api.combocurve.com/api/put-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = cast('list[WriteResponse]', self._put_items(url, data))

        return daily_production

    def patch_company_daily_productions(self, data: ItemList) -> list[WriteResponse]:
        """
        Updates daily production items.

        https://docs.api.combocurve.com/api/patch-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = cast('list[WriteResponse]', self._patch_items(url, data))

        return daily_production

    def delete_company_daily_productions(
        self,
        well_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes company daily production records.

        https://docs.api.combocurve.com/api/delete-daily-productions

        Filters are query parameters; see `_delete_filters` for why, and for the
        at-least-one-filter requirement.

        Returns the delete response headers, where 'X-Delete-Count' is the number
        of production records deleted.
        """
        url = self.get_company_daily_productions_url(_delete_filters(well_id, start_date, end_date))
        responses = self._delete_responses(url, data=[])

        return responses[0].headers

    def get_project_monthly_productions(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly production items for a specific project id.

        https://docs.api.combocurve.com/api/get-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        monthly_production = self._get_items(url, params)

        return self._keysort(monthly_production, _PRODUCTION_SORT_ORDER)

    def post_project_monthly_productions(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates project monthly production items.

        https://docs.api.combocurve.com/api/post-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = cast('list[WriteResponse]', self._post_items(url, data))

        return monthly_production

    def put_project_monthly_productions(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts project monthly production items.

        https://docs.api.combocurve.com/api/put-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = cast('list[WriteResponse]', self._put_items(url, data))

        return monthly_production

    def patch_project_monthly_productions(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Updates project monthly production items.

        https://docs.api.combocurve.com/api/patch-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = cast('list[WriteResponse]', self._patch_items(url, data))

        return monthly_production

    def delete_project_monthly_productions(
        self,
        project_id: str,
        well_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes a project's monthly production records.

        https://docs.api.combocurve.com/api/delete-project-monthly-productions

        Filters are query parameters; see `_delete_filters` for why, and for the
        at-least-one-filter requirement.

        Returns the delete response headers, where 'X-Delete-Count' is the number
        of production records deleted.
        """
        url = self.get_project_monthly_productions_url(project_id, _delete_filters(well_id, start_date, end_date))
        responses = self._delete_responses(url, data=[])

        return responses[0].headers

    def get_project_daily_productions(self, project_id: str, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily production items for a specific project id.

        https://docs.api.combocurve.com/api/get-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        daily_production = self._get_items(url, params)

        return self._keysort(daily_production, _PRODUCTION_SORT_ORDER)

    def post_project_daily_productions(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Creates project daily production items.

        https://docs.api.combocurve.com/api/post-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = cast('list[WriteResponse]', self._post_items(url, data))

        return daily_production

    def put_project_daily_productions(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Upserts project daily production items.

        https://docs.api.combocurve.com/api/put-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = cast('list[WriteResponse]', self._put_items(url, data))

        return daily_production

    def patch_project_daily_productions(self, project_id: str, data: ItemList) -> list[WriteResponse]:
        """
        Updates project daily production items.

        https://docs.api.combocurve.com/api/patch-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = cast('list[WriteResponse]', self._patch_items(url, data))

        return daily_production

    def delete_project_daily_productions(
        self,
        project_id: str,
        well_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> CaseInsensitiveDict[str]:
        """
        Deletes a project's daily production records.

        https://docs.api.combocurve.com/api/delete-project-daily-productions

        Filters are query parameters; see `_delete_filters` for why, and for the
        at-least-one-filter requirement.

        Returns the delete response headers, where 'X-Delete-Count' is the number
        of production records deleted.
        """
        url = self.get_project_daily_productions_url(project_id, _delete_filters(well_id, start_date, end_date))
        responses = self._delete_responses(url, data=[])

        return responses[0].headers


monthly_production_response = """
        Example response:
        [
            {
                "date": "2020-01-01",
                "choke": 123.45,
                "co2Injection": 123.45,
                "createdAt": "2020-01-01",
                "customNumber0": 123.45,
                "customNumber1": 123.45,
                "customNumber2": 123.45,
                "customNumber3": 123.45,
                "customNumber4": 123.45,
                "customNumber5": 123.45,
                "customNumber6": 123.45,
                "customNumber7": 123.45,
                "customNumber8": 123.45,
                "customNumber9": 123.45,
                "customNumber10": 123.45,
                "customNumber11": 123.45,
                "customNumber12": 123.45,
                "customNumber13": 123.45,
                "customNumber14": 123.45,
                "customNumber15": 123.45,
                "customNumber16": 123.45,
                "customNumber17": 123.45,
                "customNumber18": 123.45,
                "customNumber19": 123.45,
                "daysOn": 123.45,
                "gas": 123.45,
                "gasInjection": 123.45,
                "ngl": 123.45,
                "oil": 123.45,
                "operationalTag": "string",
                "steamInjection": 123.45,
                "updatedAt": "2020-01-01",
                "water": 123.45,
                "waterInjection": 123.45,
                "well": "string"
            }
        ]
"""

monthly_post_put_patch_response = """
        Example data:
        [
            {
                "date": "2020-01-01",
                "choke": 123.45,
                "chosenID": "string",
                "co2Injection": 123.45,
                "customNumber0": 123.45,
                "customNumber1": 123.45,
                "customNumber2": 123.45,
                "customNumber3": 123.45,
                "customNumber4": 123.45,
                "customNumber5": 123.45,
                "customNumber6": 123.45,
                "customNumber7": 123.45,
                "customNumber8": 123.45,
                "customNumber9": 123.45,
                "customNumber10": 123.45,
                "customNumber11": 123.45,
                "customNumber12": 123.45,
                "customNumber13": 123.45,
                "customNumber14": 123.45,
                "customNumber15": 123.45,
                "customNumber16": 123.45,
                "customNumber17": 123.45,
                "customNumber18": 123.45,
                "customNumber19": 123.45,
                "dataSource": "string",
                "daysOn": 123.45,
                "gas": 123.45,
                "gasInjection": 123.45,
                "ngl": 123.45,
                "oil": 123.45,
                "operationalTag": "string",
                "steamInjection": 123.45,
                "water": 123.45,
                "waterInjection": 123.45,
                "well": "string"
            }
        ]

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
                    "well": "string",
                    "date": "2020-01-01",
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

daily_production_response = """
        Example data:
        [
            {
                "date": "<date>",
                "bottomHolePressure": "<number>",
                "casingHeadPressure": "<number>",
                "choke": "<number>",
                "chosenID": "<string>",
                "co2Injection": "<number>",
                "customNumber0": "<number>",
                "customNumber1": "<number>",
                "customNumber2": "<number>",
                "customNumber3": "<number>",
                "customNumber4": "<number>",
                "dataSource": "<string>",
                "flowlinePressure": "<number>",
                "gas": "<number>",
                "gasInjection": "<number>",
                "gasLiftInjectionPressure": "<number>",
                "hoursOn": "<number>",
                "ngl": "<number>",
                "oil": "<number>",
                "operationalTag": "<string>",
                "steamInjection": "<number>",
                "tubingHeadPressure": "<number>",
                "vesselSeparatorPressure": "<number>",
                "water": "<number>",
                "waterInjection": "<number>",
                "well": "<string>"
            },
            {
                "date": "<date>",
                "bottomHolePressure": "<number>",
                "casingHeadPressure": "<number>",
                "choke": "<number>",
                "chosenID": "<string>",
                "co2Injection": "<number>",
                "customNumber0": "<number>",
                "customNumber1": "<number>",
                "customNumber2": "<number>",
                "customNumber3": "<number>",
                "customNumber4": "<number>",
                "dataSource": "<string>",
                "flowlinePressure": "<number>",
                "gas": "<number>",
                "gasInjection": "<number>",
                "gasLiftInjectionPressure": "<number>",
                "hoursOn": "<number>",
                "ngl": "<number>",
                "oil": "<number>",
                "operationalTag": "<string>",
                "steamInjection": "<number>",
                "tubingHeadPressure": "<number>",
                "vesselSeparatorPressure": "<number>",
                "water": "<number>",
                "waterInjection": "<number>",
                "well": "<string>"
            }
        ]

        Example response:
        [
            {
                "date": "2020-01-01",
                "bottomHolePressure": 123.45,
                "casingHeadPressure": 123.45,
                "choke": 123.45,
                "co2Injection": 123.45,
                "createdAt": "2020-01-01",
                "customNumber0": 123.45,
                "customNumber1": 123.45,
                "customNumber2": 123.45,
                "customNumber3": 123.45,
                "customNumber4": 123.45,
                "customNumber5": 123.45,
                "customNumber6": 123.45,
                "customNumber7": 123.45,
                "customNumber8": 123.45,
                "customNumber9": 123.45,
                "customNumber10": 123.45,
                "customNumber11": 123.45,
                "customNumber12": 123.45,
                "customNumber13": 123.45,
                "customNumber14": 123.45,
                "customNumber15": 123.45,
                "customNumber16": 123.45,
                "customNumber17": 123.45,
                "customNumber18": 123.45,
                "customNumber19": 123.45,
                "flowlinePressure": 123.45,
                "gas": 123.45,
                "gasInjection": 123.45,
                "gasLiftInjectionPressure": 123.45,
                "hoursOn": 123.45,
                "ngl": 123.45,
                "oil": 123.45,
                "operationalTag": "string",
                "steamInjection": 123.45,
                "tubingHeadPressure": 123.45,
                "updatedAt": "2020-01-01",
                "vesselSeparatorPressure": 123.45,
                "water": 123.45,
                "waterInjection": 123.45,
                "well": "string"
            }
        ]
"""

daily_post_put_patch_response = """
        Example data:
        [
            {
                "date": "2020-01-01",
                "bottomHolePressure": 123.45,
                "casingHeadPressure": 123.45,
                "choke": 123.45,
                "chosenID": "string",
                "co2Injection": 123.45,
                "customNumber0": 123.45,
                "customNumber1": 123.45,
                "customNumber2": 123.45,
                "customNumber3": 123.45,
                "customNumber4": 123.45,
                "customNumber5": 123.45,
                "customNumber6": 123.45,
                "customNumber7": 123.45,
                "customNumber8": 123.45,
                "customNumber9": 123.45,
                "customNumber10": 123.45,
                "customNumber11": 123.45,
                "customNumber12": 123.45,
                "customNumber13": 123.45,
                "customNumber14": 123.45,
                "customNumber15": 123.45,
                "customNumber16": 123.45,
                "customNumber17": 123.45,
                "customNumber18": 123.45,
                "customNumber19": 123.45,
                "dataSource": "string",
                "flowlinePressure": 123.45,
                "gas": 123.45,
                "gasInjection": 123.45,
                "gasLiftInjectionPressure": 123.45,
                "hoursOn": 123.45,
                "ngl": 123.45,
                "oil": 123.45,
                "operationalTag": "string",
                "steamInjection": 123.45,
                "tubingHeadPressure": 123.45,
                "vesselSeparatorPressure": 123.45,
                "water": 123.45,
                "waterInjection": 123.45,
                "well": "string"
            }
        ]

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
                    "well": "string",
                    "date": "2020-01-01",
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


Production.get_company_monthly_productions.__doc__ += monthly_production_response  # type: ignore [operator]
Production.get_project_monthly_productions.__doc__ += monthly_production_response  # type: ignore [operator]

Production.get_company_daily_productions.__doc__ += daily_production_response  # type: ignore [operator]
Production.get_project_daily_productions.__doc__ += daily_production_response  # type: ignore [operator]

Production.post_company_monthly_productions.__doc__ += monthly_post_put_patch_response  # type: ignore [operator]
Production.put_company_monthly_productions.__doc__ += monthly_post_put_patch_response  # type: ignore [operator]
Production.patch_company_monthly_productions.__doc__ += monthly_post_put_patch_response  # type: ignore [operator]

Production.post_company_daily_productions.__doc__ += daily_post_put_patch_response  # type: ignore [operator]
Production.put_company_daily_productions.__doc__ += daily_post_put_patch_response  # type: ignore [operator]
Production.patch_company_daily_productions.__doc__ += daily_post_put_patch_response  # type: ignore [operator]
