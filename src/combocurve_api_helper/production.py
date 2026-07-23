from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList, WriteResponse


GET_LIMIT = 20_000
POST_LIMIT = 20_000
PUT_LIMIT = 20_000
PATCH_LIMIT = 20_000


class Production(APIBase):
    ######
    # URLs
    ######

    def get_company_monthly_productions_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for company monthly production.
        """
        url = f'{self.API_BASE_URL}/monthly-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_company_daily_productions_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for company daily production.
        """
        url = f'{self.API_BASE_URL}/daily-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_project_monthly_productions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's monthly production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/monthly-productions'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_project_daily_productions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
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

    def get_company_monthly_productions(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company monthly production items.

        https://docs.api.combocurve.com/api/get-monthly-productions
        """
        url = self.get_company_monthly_productions_url(filters)
        params = {'take': GET_LIMIT}
        monthly_production = self._get_items(url, params)

        order = {
            'well': 0,
            'date': 1,
        }
        return self._keysort(monthly_production, order)

    def post_company_monthly_productions(self, data: ItemList) -> List[WriteResponse]:
        """
        Creates monthly production items.

        https://docs.api.combocurve.com/api/post-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = cast(List[WriteResponse], self._post_items(url, data))

        return monthly_production

    def put_company_monthly_productions(self, data: ItemList) -> List[WriteResponse]:
        """
        Upserts monthly production items.

        https://docs.api.combocurve.com/api/put-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = cast(List[WriteResponse], self._put_items(url, data))

        return monthly_production

    def patch_company_monthly_productions(self, data: ItemList) -> List[WriteResponse]:
        """
        Updates monthly production items.

        https://docs.api.combocurve.com/api/patch-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = cast(List[WriteResponse], self._put_items(url, data))

        return monthly_production

    def delete_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Deletes monthly production items.

        https://docs.api.combocurve.com/api/delete-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._delete_items(url, data)

        return monthly_production

    def get_company_daily_productions(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company monthly production items.

        https://docs.api.combocurve.com/api/get-daily-productions
        """
        url = self.get_company_daily_productions_url(filters)
        params = {'take': GET_LIMIT}
        dailiy_production = self._get_items(url, params)

        order = {
            'well': 0,
            'date': 1,
        }
        return self._keysort(dailiy_production, order)

    def post_company_daily_productions(self, data: ItemList) -> List[WriteResponse]:
        """
        Creates daily production items.

        https://docs.api.combocurve.com/api/post-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = cast(List[WriteResponse], self._post_items(url, data))

        return daily_production

    def put_company_daily_productions(self, data: ItemList) -> List[WriteResponse]:
        """
        Upserts daily production items.

        https://docs.api.combocurve.com/api/put-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = cast(List[WriteResponse], self._put_items(url, data))

        return daily_production

    def patch_company_daily_productions(self, data: ItemList) -> List[WriteResponse]:
        """
        Updates daily production items.

        https://docs.api.combocurve.com/api/patch-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = cast(List[WriteResponse], self._patch_items(url, data))

        return daily_production

    def delete_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Delete daily production items.

        https://docs.api.combocurve.com/api/delete-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._delete_items(url, data)

        return daily_production

    def get_project_monthly_productions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly production items for a specific project id.

        https://docs.api.combocurve.com/api/get-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        monthly_production = self._get_items(url, params)

        order = {
            'well': 0,
            'date': 1,
        }
        return self._keysort(monthly_production, order)

    def post_project_monthly_productions(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates project monthly production items.

        https://docs.api.combocurve.com/api/post-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = cast(List[WriteResponse], self._post_items(url, data))

        return monthly_production

    def put_project_monthly_productions(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts project monthly production items.

        https://docs.api.combocurve.com/api/put-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = cast(List[WriteResponse], self._put_items(url, data))

        return monthly_production

    def patch_project_monthly_productions(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Updates project monthly production items.

        https://docs.api.combocurve.com/api/patch-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = cast(List[WriteResponse], self._put_items(url, data))

        return monthly_production

    def delete_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Deletes project monthly production items.

        https://docs.api.combocurve.com/api/delete-project-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._delete_items(url, data)

        return monthly_production

    def get_project_daily_productions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily production items for a specific project id.

        https://docs.api.combocurve.com/api/get-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id, filters)
        params = {'take': GET_LIMIT}
        daily_production = self._get_items(url, params)

        order = {
            'well': 0,
            'date': 1,
        }
        return self._keysort(daily_production, order)

    def post_project_daily_productions(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Creates project daily production items.

        https://docs.api.combocurve.com/api/post-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = cast(List[WriteResponse], self._post_items(url, data))

        return daily_production

    def put_project_daily_productions(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Upserts project daily production items.

        https://docs.api.combocurve.com/api/put-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = cast(List[WriteResponse], self._put_items(url, data))

        return daily_production

    def patch_project_daily_productions(self, project_id: str, data: ItemList) -> List[WriteResponse]:
        """
        Updates project daily production items.

        https://docs.api.combocurve.com/api/patch-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = cast(List[WriteResponse], self._put_items(url, data))

        return daily_production

    def delete_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Deletes project daily production items.

        https://docs.api.combocurve.com/api/delete-project-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._delete_items(url, data)

        return daily_production


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
