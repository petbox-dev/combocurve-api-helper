from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


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

    def post_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Creates monthly production items.

        https://docs.api.combocurve.com/api/post-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._post_items(url, data)

        return monthly_production

    def put_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Upserts monthly production items.

        https://docs.api.combocurve.com/api/put-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._put_items(url, data)

        return monthly_production

    def patch_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Updates monthly production items.

        https://docs.api.combocurve.com/api/patch-monthly-productions
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._put_items(url, data)

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

    def post_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Creates daily production items.

        https://docs.api.combocurve.com/api/post-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._post_items(url, data)

        return daily_production

    def put_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Upserts daily production items.

        https://docs.api.combocurve.com/api/put-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._put_items(url, data)

        return daily_production

    def patch_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Updates daily production items.

        https://docs.api.combocurve.com/api/patch-daily-productions
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._patch_items(url, data)

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

    def post_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Creates project monthly production items.

        https://docs.api.combocurve.com/api/post-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._post_items(url, data)

        return monthly_production

    def put_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Upserts project monthly production items.

        https://docs.api.combocurve.com/api/put-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._put_items(url, data)

        return monthly_production

    def patch_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates project monthly production items.

        https://docs.api.combocurve.com/api/patch-projects-monthly-productions
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._put_items(url, data)

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

    def post_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Creates project daily production items.

        https://docs.api.combocurve.com/api/post-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._post_items(url, data)

        return daily_production

    def put_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Upserts project daily production items.

        https://docs.api.combocurve.com/api/put-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._put_items(url, data)

        return daily_production

    def patch_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates project daily production items.

        https://docs.api.combocurve.com/api/patch-projects-daily-productions
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._put_items(url, data)

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
                "choke": 13,
                "co2Injection": 123,
                "createdAt": "2020-01-21T16:58:08.986Z",
                "date": "2017-01-15T00:00:00.000Z",
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "daysOn": 30,
                "gas": 16925,
                "gasInjection": 123,
                "ngl": 123,
                "oil": 1022,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "water": 4631,
                "waterInjection": 123,
                "well": "5e286e0d8f3df51d7ae744a3"
            },
            {
                "choke": 13,
                "co2Injection": 123,
                "createdAt": "2020-01-21T16:58:08.986Z",
                "date": "2017-01-15T00:00:00.000Z",
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "daysOn": 30,
                "gas": 16925,
                "gasInjection": 123,
                "ngl": 123,
                "oil": 1022,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "water": 4631,
                "waterInjection": 123,
                "well": "5e286e0d8f3df51d7ae744a3"
            }
        ]
"""

monthly_post_put_patch_response = """
        Example data:
        [
            {
                "choke": 13,
                "chosenID": 28058901650448,
                "co2Injection": 123,
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "dataSource": "internal",
                "date": "2017-01-15T00:00:00.000Z",
                "daysOn": 30,
                "gas": 16925,
                "gasInjection": 123,
                "ngl": 123,
                "oil": 1022,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "water": 4631,
                "waterInjection": 123,
                "well": "5e286e0d8f3df51d7ae744a3"
            },
            {
                "choke": 13,
                "chosenID": 28058901650555,
                "co2Injection": 123,
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "dataSource": "internal",
                "date": "2020-02-15T00:00:00.000Z",
                "daysOn": 30,
                "gas": 16925,
                "gasInjection": 123,
                "ngl": 123,
                "oil": 1022,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "water": 4631,
                "waterInjection": 123,
                "well": "5e281e0d8f3df51d7ae845j3"
            }
        ]

        Example response:
        [
            {
                "generalErrors": [
                    {
                        "name": "ValidationError",
                        "message": "The field 'well' is required.",
                        "location": "In body of request at position [0]"
                    },
                    {
                        "name": "ValidationError",
                        "message": "The field 'date' is required.",
                        "location": "In body of request at position [2]"
                    }
                ],
                "results": [
                    {
                        "status": "Success",
                        "code": 200,
                        "well": "62b1c13e2750169012ee4515",
                        "date": "2023-01-01T00:00:00.000Z"
                    },
                    {
                        "status": "Success",
                        "code": 200,
                        "well": "62b1c13e4857169000ee4613",
                        "date": "2023-01-01T00:00:00.000Z"
                    }
                ],
                "failedCount": 2,
                "successCount": 2
            }
        ]
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
                "bottomHolePressure": 10000,
                "casingHeadPressure": 100.4,
                "choke": 13,
                "co2Injection": 123,
                "createdAt": "2020-01-21T16:58:08.986Z",
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "date": "2010-10-27T00:00:00.000Z",
                "flowlinePressure": 457,
                "gas": 1.0596808195,
                "gasInjection": 123,
                "gasLiftInjectionPressure": 635,
                "hoursOn": 24,
                "ngl": 123,
                "oil": 4.8788599968,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "tubingHeadPressure": 2211.3,
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "vesselSeparatorPressure": 48.46,
                "water": 95.5182647705,
                "waterInjection": 123,
                "well": "5e286e0d8f3df51d7ae744a3"
            },
            {
                "bottomHolePressure": 10000,
                "casingHeadPressure": 100.4,
                "choke": 13,
                "co2Injection": 123,
                "createdAt": "2020-01-21T16:58:08.986Z",
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "date": "2010-10-27T00:00:00.000Z",
                "flowlinePressure": 457,
                "gas": 1.0596808195,
                "gasInjection": 123,
                "gasLiftInjectionPressure": 635,
                "hoursOn": 24,
                "ngl": 123,
                "oil": 4.8788599968,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "tubingHeadPressure": 2211.3,
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "vesselSeparatorPressure": 48.46,
                "water": 95.5182647705,
                "waterInjection": 123,
                "well": "5c306e0d8f3df51d7ae867r6"
            }
        ]
"""

daily_post_put_patch_response = """
        Example data:
        [
            {
                "bottomHolePressure": 10000,
                "casingHeadPressure": 100.4,
                "choke": 13,
                "chosenID": 28058901650448,
                "co2Injection": 123,
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "dataSource": "internal",
                "date": "2010-10-27T00:00:00.000Z",
                "flowlinePressure": 457,
                "gas": 1.0596808195,
                "gasInjection": 123,
                "gasLiftInjectionPressure": 635,
                "hoursOn": 24,
                "ngl": 123,
                "oil": 4.8788599968,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "tubingHeadPressure": 2211.3,
                "vesselSeparatorPressure": 48.46,
                "water": 95.5182647705,
                "waterInjection": 123,
                "well": "5e286e0d8f3df51d7ae744a3"
            },
            {
                "bottomHolePressure": 10000,
                "casingHeadPressure": 100.4,
                "choke": 13,
                "chosenID": 64458901659657,
                "co2Injection": 123,
                "customNumber0": 123,
                "customNumber1": 123,
                "customNumber2": 123,
                "customNumber3": 123,
                "customNumber4": 123,
                "customNumber5": 123,
                "customNumber6": 123,
                "customNumber7": 123,
                "customNumber8": 123,
                "customNumber9": 123,
                "customNumber10": 123,
                "customNumber11": 123,
                "customNumber12": 123,
                "customNumber13": 123,
                "customNumber14": 123,
                "customNumber15": 123,
                "customNumber16": 123,
                "customNumber17": 123,
                "customNumber18": 123,
                "customNumber19": 123,
                "dataSource": "internal",
                "date": "2010-10-28T00:00:00.000Z",
                "flowlinePressure": 457,
                "gas": 1.0596808195,
                "gasInjection": 123,
                "gasLiftInjectionPressure": 635,
                "hoursOn": 24,
                "ngl": 123,
                "oil": 4.8788599968,
                "operationalTag": "Start of production",
                "steamInjection": 123,
                "tubingHeadPressure": 2211.3,
                "vesselSeparatorPressure": 48.46,
                "water": 95.5182647705,
                "waterInjection": 123,
                "well": "5c306e0d8f3df51d7ae867r6"
            }
        ]

        Example response:
        [
            {
                "generalErrors": [
                    {
                        "name": "ValidationError",
                        "message": "The field 'well' is required.",
                        "location": "In body of request at position [0]"
                    },
                    {
                        "name": "ValidationError",
                        "message": "The field 'date' is required.",
                        "location": "In body of request at position [2]"
                    }
                ],
                "results": [
                    {
                        "status": "Success",
                        "code": 200,
                        "well": "62b1c13e2750169012ee4515",
                        "date": "2023-01-01T00:00:00.000Z"
                    },
                    {
                        "status": "Success",
                        "code": 200,
                        "well": "62b1c13e4857169000ee4613",
                        "date": "2023-01-01T00:00:00.000Z"
                    }
                ],
                "failedCount": 2,
                "successCount": 2
            }
        ]
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
