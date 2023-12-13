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

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_company_daily_productions_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for company daily production.
        """
        url = f'{self.API_BASE_URL}/daily-productions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_monthly_productions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's monthly production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/monthly-productions'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_project_daily_productions_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific project's daily production.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/daily-productions'
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


    def get_company_monthly_productions(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company monthly production items.

        https://docs.api.combocurve.com/#6cecaf35-e501-4e21-899f-22261de76fff
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

        https://docs.api.combocurve.com/#8e46ba1e-c230-4d19-bd94-45af8fbe89cb
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._post_items(url, data)

        return monthly_production


    def put_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Upserts monthly production items.

        https://docs.api.combocurve.com/#7cc3b686-2f9f-470b-8dd0-810fd4fa13dc
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._put_items(url, data)

        return monthly_production


    def patch_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Updates monthly production items.

        https://docs.api.combocurve.com/#5167e26e-de2d-4860-aa3d-b9b9f80d0d24
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._put_items(url, data)

        return monthly_production


    def delete_company_monthly_productions(self, data: ItemList) -> ItemList:
        """
        Deletes monthly production items.

        https://docs.api.combocurve.com/#81ca806f-dfd5-4af2-b155-05439bdf1158
        """
        url = self.get_company_monthly_productions_url()
        monthly_production = self._delete_items(url, data)

        return monthly_production


    def get_company_daily_productions(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of company monthly production items.

        https://docs.api.combocurve.com/#d53b02b3-6574-40ee-bdfb-1e64191ae80a
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

        https://docs.api.combocurve.com/#9d7db301-2512-491d-8a8b-985cd3417d3e
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._post_items(url, data)

        return daily_production


    def put_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Upserts daily production items.

        https://docs.api.combocurve.com/#dfb57b4d-60aa-4116-b219-b174f01cc5dd
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._put_items(url, data)

        return daily_production


    def patch_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Updates daily production items.

        https://docs.api.combocurve.com/#64460347-9135-4020-9bc6-bb5eeebcbc85
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._patch_items(url, data)

        return daily_production


    def delete_company_daily_productions(self, data: ItemList) -> ItemList:
        """
        Delete daily production items.

        https://docs.api.combocurve.com/#4292e628-bfaa-4b9e-8ef2-467715e1092c
        """
        url = self.get_company_daily_productions_url()
        daily_production = self._delete_items(url, data)

        return daily_production


    def get_project_monthly_productions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly production items for a specific project id.

        https://docs.api.combocurve.com/#91a94565-b7cb-40f2-b5a2-0689d8efb897
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

        https://docs.api.combocurve.com/#2a58c950-1747-43d9-b0d7-c847db39c850
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._post_items(url, data)

        return monthly_production


    def put_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Upserts project monthly production items.

        https://docs.api.combocurve.com/#43c7de35-b397-464c-98c6-a5da1b37de5c
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._put_items(url, data)

        return monthly_production


    def patch_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates project monthly production items.

        https://docs.api.combocurve.com/#b5c7dc84-6897-4650-bf89-2709fd9189a7
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._put_items(url, data)

        return monthly_production


    def delete_project_monthly_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Deletes project monthly production items.

        https://docs.api.combocurve.com/#1c826ba7-ff89-434f-bf87-7e3957b25353
        """
        url = self.get_project_monthly_productions_url(project_id)
        monthly_production = self._delete_items(url, data)

        return monthly_production


    def get_project_daily_productions(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily production items for a specific project id.

        https://docs.api.combocurve.com/#637b21b2-6c45-4d19-829c-ffc0514ed86c
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

        https://docs.api.combocurve.com/#8e46ba1e-c230-4d19-bd94-45af8fbe89cb
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._post_items(url, data)

        return daily_production


    def put_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Upserts project daily production items.

        https://docs.api.combocurve.com/#c0a0e460-0692-4231-a4bc-e2602f73dd3a
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._put_items(url, data)

        return daily_production


    def patch_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Updates project daily production items.

        https://docs.api.combocurve.com/#91720250-6958-43e8-9d66-85498a628a02
        """
        url = self.get_project_daily_productions_url(project_id)
        daily_production = self._put_items(url, data)

        return daily_production


    def delete_project_daily_productions(self, project_id: str, data: ItemList) -> ItemList:
        """
        Deletes project daily production items.

        https://docs.api.combocurve.com/#e61b507c-76cb-4e2a-95ba-0c1381938129
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

daily_post_put_patch_response = """
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
