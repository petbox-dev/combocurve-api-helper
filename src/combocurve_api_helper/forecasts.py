import warnings
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

        url += self._build_params_string(filters)
        return url


    def get_forecast_by_id_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url for a specific forecast from its forecast id.
        """
        base_url = self.get_forecasts_url(project_id)
        return f'{base_url}/{forecast_id}'


    def get_forecast_wells_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url for a specific forecast's wells from its forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        return f'{base_url}/wells'


    def get_forecast_aries_url(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific forecast's ARIES parameters from its forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/aries'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_forecast_outputs_url(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for a specific forecast outputs from its forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/outputs'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_forecast_output_by_id_url(self, project_id: str, forecast_id: str, output_id: str) -> str:
        """
        Returns the API url for a specific forecast output from its forecast id and output id.
        """
        base_url = self.get_forecast_outputs_url(project_id, forecast_id)
        return f'{base_url}/{output_id}'


    def get_forecast_daily_volumes_url(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for daily volumes for a specific project id and forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/daily-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_forecast_monthly_volumes_url(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for monthly volumes for a specific project id and forecast id.
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/monthly-volumes'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_forecast_segment_parameters_url(
            self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str) -> str:
        """
        Returns the API url for a specific forecast segment parameters from its
        forecast id, well id, phase, and series.
        """

        VALID_PHASES = ['oil', 'gas', 'water']
        VALID_SERIES = ['best', 'p10', 'p50', 'p90']

        if phase.lower() not in VALID_PHASES:
            warnings.warn(f'`phase` \'{phase}\' is not in list of valid names:\n{VALID_PHASES}')

        if series.lower() not in VALID_SERIES:
            warnings.warn(f'`series` \'{series}\' is not in list of valid names:\n{VALID_SERIES}')

        phase = phase.lower()
        series = series.lower()

        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        url = f'{base_url}/parameters/{well_id}/{phase}/{series}'

        return url


    ###########
    # API calls
    ###########


    def get_forecasts(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of forecasts for a specific project id.

        https://docs.api.combocurve.com/#3f80e303-3285-4ce1-aec8-40ab2d518e9e

        Example response:
        [
            {
                "createdAt": "2020-01-21T16:58:08.986Z",
                "id": "5e5981b9e23dae0012624d72",
                "name": "Test forecast",
                "runDate": "2020-06-08T19:14:22.012Z",
                "running": false,
                "type": "probabilistic",
                "updatedAt": "2020-01-21T17:58:08.986Z"
            }
        ]
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


    def post_forecasts(self, project_id: str, data: ItemList) -> ItemList:
        """
        Creates new forecasts for a specific project id.

        https://docs.api.combocurve.com/#e49824bc-678f-4b10-aaee-14d5ec1825cf

        Example data:
        [
            {
                "name": "Test forecast",
                "type": "deterministic"
            },
            {
                "name": "Test forecast 2",
                "type": "probabilistic"
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "ValidationError",
                    "message": "The field 'name' is required.",
                    "location": "In body of request at position [0]"
                },
                {
                    "name": "ValidationError",
                    "message": "The field 'unique' is required.",
                    "location": "In body of request at position [2]"
                }
            ],
            "results": [
                {
                    "status": "Success",
                    "code": 200,
                    "name": "Test forecast"
                },
                {
                    "status": "Success",
                    "code": 200,
                    "name": "Test forecast 2"
                }
            ],
            "failedCount": 2,
            "successCount": 2
        }
        """
        url = self.get_forecasts_url(project_id)
        forecasts = self._post_items(url, data)

        return forecasts


    def get_forecast_by_id(self, project_id: str, forecast_id: str) -> Item:
        """
        Returns a specific forecast from its forecast id.

        https://docs.api.combocurve.com/#5fec685c-a64e-43bb-b32a-920d1a0c3be7

        Example response:
        {
            "createdAt": "2020-01-21T16:58:08.986Z",
            "id": "5e5981b9e23dae0012624d72",
            "name": "Test forecast",
            "runDate": "2020-06-08T19:14:22.012Z",
            "running": false,
            "type": "probabilistic",
            "updatedAt": "2020-01-21T17:58:08.986Z"
        }
        """
        url = self.get_forecast_by_id_url(project_id, forecast_id)
        params = {'take': GET_LIMIT}
        forecasts = self._get_items(url, params)

        return forecasts[0]


    def get_forecast_aries(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of ARIES parameters for a specific project id and forecast id.

        https://docs.api.combocurve.com/#d24c7390-9c9e-48e7-91aa-1ad2c9551bd2

        Example response:
        [
            {
                "well": "602d31de4477b92029913e56",
                "forecast": [
                    {
                        "PROPNUM": "1PDPOIL020",
                        "WELL NAME": "1PDPOIL235",
                        "WELL NUMBER": "1H",
                        "INPT ID": "DTHrr7FMza",
                        "API10": "1234567890",
                        "API12": "12345678901",
                        "API14": "12345678901214",
                        "CHOSEN ID": "1PDPOIL235",
                        "ARIES ID": "1PDPOIL235",
                        "PHDWIN ID": "9E5F5CC579867509254700023",
                        "SECTION": 4,
                        "SEQUENCE": 10,
                        "QUALIFIER": "CC_QUAL",
                        "KEYWORD": "CUMS",
                        "EXPRESSION": "0 0 0 0 0 0"
                    },
                    {
                        "PROPNUM": "1PDPOIL020",
                        "WELL NAME": "1PDPOIL236",
                        "WELL NUMBER": "2H",
                        "INPT ID": "KMLrr7FMqq",
                        "API10": "1234567890",
                        "API12": "12345678901",
                        "API14": "12345678901214",
                        "CHOSEN ID": "1PDPOIL236",
                        "ARIES ID": "1PDPOIL236",
                        "PHDWIN ID": "9E5F5CC579867509254700023",
                        "SECTION": 5,
                        "SEQUENCE": 20,
                        "QUALIFIER": "CC_QUAL",
                        "KEYWORD": "CUMS",
                        "EXPRESSION": "0 0 0 0 0 0"
                    },
                    {
                        "PROPNUM": "1PDPOIL020",
                        "WELL NAME": "1PDPOIL237",
                        "WELL NUMBER": "3H",
                        "INPT ID": "LGHrr9FMhg",
                        "API10": "1234567890",
                        "API12": "12345678901",
                        "API14": "12345678901214",
                        "CHOSEN ID": "1PDPOIL237",
                        "ARIES ID": "1PDPOIL237",
                        "PHDWIN ID": "9E5F5CC579867509254700023",
                        "SECTION": 6,
                        "SEQUENCE": 30,
                        "QUALIFIER": "CC_QUAL",
                        "KEYWORD": "CUMS",
                        "EXPRESSION": "0 0 0 0 0 0"
                    }
                ]
            }
        ]
        """
        url = self.get_forecast_aries_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)


    def get_forecast_outputs(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of outputs for a specific project id and forecast id.

        https://docs.api.combocurve.com/#b396508a-bb08-4014-916e-3f7543dfd58b

        Example response:
        [
            {
                "best": {
                    "segments": [
                        {
                            "b": 1.5,
                            "diEffSec": 0.603721736666588,
                            "diNominal": 0.005491514853419089,
                            "endDate": "2001-02-12T00:00:00.000Z",
                            "qEnd": 0.10001738801851469,
                            "qStart": 2.2340862422997945,
                            "realizedDSwEffSec": 0.07999999999999996,
                            "segmentIndex": 1,
                            "segmentType": "arps_modified",
                            "startDate": "1982-05-15T00:00:00.000Z",
                            "swDate": "1989-07-17T02:09:12.931Z"
                        }
                    ],
                    "eur": 539853.3300559863
                },
                "createdAt": "2020-01-21T16:58:08.986Z",
                "forecasted": true,
                "forecastedAt": "2020-01-31T22:58:50.578Z",
                "forecastedBy": "5e272d39b78910dd2a1bd8ea",
                "id": "5e272f1d4b97ed0013313088",
                "forecast": "6285655e2448a0ec88951dba",
                "p10": {
                    "segments": [
                        {
                            "b": 1.5,
                            "diEffSec": 0.461422453817678,
                            "diNominal": 0.0027926834451796035,
                            "endDate": "2005-11-15T00:00:00.000Z",
                            "qEnd": 0.10000470857720545,
                            "qStart": 2.2340862422997945,
                            "realizedDSwEffSec": 0.07999999999999996,
                            "segmentIndex": 1,
                            "segmentType": "arps_modified",
                            "startDate": "1982-05-15T00:00:00.000Z",
                            "swDate": "1989-03-21T18:28:58.327Z"
                        }
                    ],
                    "eur": 539853.3300559863
                },
                "p50": {
                    "segments": [
                        {
                            "b": 1.5,
                            "diEffSec": 0.603721736666588,
                            "diNominal": 0.005491514853419089,
                            "endDate": "2001-02-12T00:00:00.000Z",
                            "qEnd": 0.10001738801851469,
                            "qStart": 2.2340862422997945,
                            "realizedDSwEffSec": 0.07999999999999996,
                            "segmentIndex": 1,
                            "segmentType": "arps_modified",
                            "startDate": "1982-05-15T00:00:00.000Z",
                            "swDate": "1989-07-17T02:09:12.931Z"
                        }
                    ]
                },
                "p90": {
                    "segments": [
                        {
                            "b": 1.4864126197388372,
                            "diEffSec": 0.6377483484117903,
                            "diNominal": 0.006490343943301474,
                            "endDate": "1999-10-06T00:00:00.000Z",
                            "qEnd": 0.1000051797269731,
                            "qStart": 2.2340862422997945,
                            "realizedDSwEffSec": 0.07999999999999996,
                            "segmentIndex": 1,
                            "segmentType": "arps_modified",
                            "startDate": "1982-05-15T00:00:00.000Z",
                            "swDate": "1989-08-30T11:51:00.367Z"
                        }
                    ],
                    "eur": 539853.3300559863
                },
                "phase": "oil",
                "reviewedAt": "2020-01-31T23:00:00.00Z",
                "reviewedBy": "5e272d38b78910dd2a1bd6b5",
                "runDate": "2020-01-31T22:58:50.578Z",
                "status": "in_progress",
                "typeCurveData": {
                    "name": "applied-type-curve",
                    "type": "ratio"
                },
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "well": "5e272d39b78910dd2a1bd8fe",
                "data_freq": "monthly"
            },
            {
                "best": {
                    "segments": [
                        {
                            "b": 0.5871650672699218,
                            "diEffSec": 0.5717582558912915,
                            "diNominal": 0.003009175917809707,
                            "endDate": "2015-06-16T00:00:00.000Z",
                            "qEnd": 92.20980498278352,
                            "qStart": 423.3332616779596,
                            "realizedDSwEffSec": 0.07999999999999996,
                            "segmentIndex": 1,
                            "segmentType": "arps_modified",
                            "startDate": "2013-03-19T00:00:00.000Z",
                            "swDate": "2031-08-05T06:08:36.544Z"
                        }
                    ],
                    "eur": 539853.3300559863
                },
                "createdAt": "2020-01-21T16:58:08.986Z",
                "forecasted": true,
                "forecastedAt": "2020-01-31T22:58:50.578Z",
                "forecastedBy": "5e272d39b78910dd2a1bd8ea",
                "id": "5f24af6537794900129b17af",
                "forecast": "6285655e2448a0ec88951dba",
                "phase": "oil",
                "reviewedAt": "2020-01-31T23:00:00.00Z",
                "reviewedBy": "5e272d38b78910dd2a1bd6b5",
                "runDate": "2020-07-31T23:57:20.352Z",
                "status": "in_progress",
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "well": "5ed67b2ec3629ac71ded298b",
                "data_freq": "monthly"
            },
            {
                "createdAt": "2020-01-21T16:58:08.986Z",
                "forecasted": true,
                "forecastedAt": "2020-01-31T22:58:50.578Z",
                "forecastedBy": "5e272d39b78910dd2a1bd8ea",
                "id": "5f24af6537794900129b17af",
                "forecast": "6285655e2448a0ec88951dba",
                "phase": "oil",
                "ratio": {
                    "basePhase": "oil",
                    "segments": [
                        {
                            "b": 0.5871650672699218,
                            "diEffSec": 0.5717582558912915,
                            "diNominal": 0.003009175917809707,
                            "endDate": "2015-06-16T00:00:00.000Z",
                            "qEnd": 92.20980498278352,
                            "qStart": 423.3332616779596,
                            "realizedDSwEffSec": 0.07999999999999996,
                            "segmentIndex": 1,
                            "segmentType": "arps_modified",
                            "startDate": "2013-03-19T00:00:00.000Z",
                            "swDate": "2031-08-05T06:08:36.544Z"
                        }
                    ],
                    "eur": 4544.45
                },
                "reviewedAt": "2020-01-31T23:00:00.00Z",
                "reviewedBy": "5e272d38b78910dd2a1bd6b5",
                "runDate": "2020-07-31T23:57:20.352Z",
                "status": "in_progress",
                "typeCurveData": {
                    "name": "applied-type-curve",
                    "type": "ratio"
                },
                "updatedAt": "2020-01-21T17:58:08.986Z",
                "well": "5ed67b2ec3629ac71ded298b",
                "data_freq": "monthly"
            }
        ]
        """
        url = self.get_forecast_outputs_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)


    def get_forecast_output_by_id(self, project_id: str, forecast_id: str, output_id: str) -> Item:
        """
        Returns a specific forecast output from its forecast id and output id.

        https://docs.api.combocurve.com/#4a6312b3-51cf-48d8-bef2-7752e840b2e0

        Example response:
        {
            "best": {
                "segments": [
                    {
                        "b": 1.5,
                        "diEffSec": 0.603721736666588,
                        "diNominal": 0.005491514853419089,
                        "endDate": "2001-02-12T00:00:00.000Z",
                        "qEnd": 0.10001738801851469,
                        "qStart": 2.2340862422997945,
                        "realizedDSwEffSec": 0.07999999999999996,
                        "segmentIndex": 1,
                        "segmentType": "arps_modified",
                        "startDate": "1982-05-15T00:00:00.000Z",
                        "swDate": "1989-07-17T02:09:12.931Z"
                    }
                ],
                "eur": 539853.3300559863
            },
            "createdAt": "2020-01-21T16:58:08.986Z",
            "forecasted": true,
            "forecastedAt": "2020-01-31T22:58:50.578Z",
            "forecastedBy": "5e272d39b78910dd2a1bd8ea",
            "id": "5e272f1d4b97ed0013313088",
            "forecast": "6285655e2448a0ec88951dba",
            "p10": {
                "segments": [
                    {
                        "b": 1.5,
                        "diEffSec": 0.461422453817678,
                        "diNominal": 0.0027926834451796035,
                        "endDate": "2005-11-15T00:00:00.000Z",
                        "qEnd": 0.10000470857720545,
                        "qStart": 2.2340862422997945,
                        "realizedDSwEffSec": 0.07999999999999996,
                        "segmentIndex": 1,
                        "segmentType": "arps_modified",
                        "startDate": "1982-05-15T00:00:00.000Z",
                        "swDate": "1989-03-21T18:28:58.327Z"
                    }
                ],
                "eur": 539853.3300559863
            },
            "p50": {
                "segments": [
                    {
                        "b": 1.5,
                        "diEffSec": 0.603721736666588,
                        "diNominal": 0.005491514853419089,
                        "endDate": "2001-02-12T00:00:00.000Z",
                        "qEnd": 0.10001738801851469,
                        "qStart": 2.2340862422997945,
                        "realizedDSwEffSec": 0.07999999999999996,
                        "segmentIndex": 1,
                        "segmentType": "arps_modified",
                        "startDate": "1982-05-15T00:00:00.000Z",
                        "swDate": "1989-07-17T02:09:12.931Z"
                    }
                ]
            },
            "p90": {
                "segments": [
                    {
                        "b": 1.4864126197388372,
                        "diEffSec": 0.6377483484117903,
                        "diNominal": 0.006490343943301474,
                        "endDate": "1999-10-06T00:00:00.000Z",
                        "qEnd": 0.1000051797269731,
                        "qStart": 2.2340862422997945,
                        "realizedDSwEffSec": 0.07999999999999996,
                        "segmentIndex": 1,
                        "segmentType": "arps_modified",
                        "startDate": "1982-05-15T00:00:00.000Z",
                        "swDate": "1989-08-30T11:51:00.367Z"
                    }
                ],
                "eur": 539853.3300559863
            },
            "phase": "OIL",
            "reviewedAt": "2020-01-31T23:00:00.00Z",
            "reviewedBy": "5e272d38b78910dd2a1bd6b5",
            "runDate": "2020-01-31T22:58:50.578Z",
            "status": "in_progress",
            "typeCurveData": {
                "name": "applied-type-curve",
                "type": "ratio"
            },
            "updatedAt": "2020-01-21T17:58:08.986Z",
            "well": "5e272d39b78910dd2a1bd8fe",
            "data_freq": "monthly"
        }
        """
        url = self.get_forecast_output_by_id_url(project_id, forecast_id, output_id)
        params = {'take': GET_LIMIT}
        outputs = self._get_items(url, params)

        return outputs[0]


    def get_forecast_daily_volumes(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of daily volumes for a specific project id and forecast id.

        https://docs.api.combocurve.com/#5c8407df-a92f-464a-976c-60fc610caafd

        Example response:
        [
            {
                "project": "63bdcdf1dc401f0012613185",
                "forecast": "63bdce14dc401f00126131a7",
                "well": "63bdcdf56782656f8aaad644",
                "resolution": "daily",
                "phases": [
                    {
                        "phase": "gas",
                        "forecastOutputId": "63bdce17dc401f0012614f34",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 1980202.8287785284,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    },
                    {
                        "phase": "oil",
                        "forecastOutputId": "63bdce17dc401f0012614f34",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 610156.72736362,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "project": "63bdcdf1dc401f0012613185",
                "forecast": "63bdce14dc401f00126131a7",
                "well": "63bdcdf56782654efaaad6ca",
                "resolution": "daily",
                "phases": [
                    {
                        "phase": "gas",
                        "forecastOutputId": "63bdce17dc401f00126150f5",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 1980202.8287785284,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    },
                    {
                        "phase": "oil",
                        "forecastOutputId": "63bdce17dc401f00126150f5",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 610156.72736362,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        """
        url = self.get_forecast_daily_volumes_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        daily_volumes = self._get_items(url, params)

        order = {
            'well': 0,
        }
        return self._keysort(daily_volumes, order)


    def get_forecast_monthly_volumes(
            self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of monthly volumes for a specific project id and forecast id.

        https://docs.api.combocurve.com/#f4d538aa-1c10-41f2-bcb3-d9e3716e2ecf

        Example response:
        [
            {
                "project": "63bdcdf1dc401f0012613185",
                "forecast": "63bdce14dc401f00126131a7",
                "well": "63bdcdf56782656f8aaad644",
                "resolution": "daily",
                "phases": [
                    {
                        "phase": "gas",
                        "forecastOutputId": "63bdce17dc401f0012614f34",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 1980202.8287785284,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    },
                    {
                        "phase": "oil",
                        "forecastOutputId": "63bdce17dc401f0012614f34",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 610156.72736362,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "project": "63bdcdf1dc401f0012613185",
                "forecast": "63bdce14dc401f00126131a7",
                "well": "63bdcdf56782654efaaad6ca",
                "resolution": "daily",
                "phases": [
                    {
                        "phase": "gas",
                        "forecastOutputId": "63bdce17dc401f00126150f5",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 1980202.8287785284,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    },
                    {
                        "phase": "oil",
                        "forecastOutputId": "63bdce17dc401f00126150f5",
                        "series": [
                            {
                                "series": "best",
                                "startDate": "2020-03-15T00:00:00.000Z",
                                "endDate": "2025-03-15T00:00:00.000Z",
                                "eur": 610156.72736362,
                                "volumes": [
                                    0,
                                    1,
                                    2
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        """
        url = self.get_forecast_monthly_volumes_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT}
        monthly_volumes = self._get_items(url, params)

        order = {
            'well': 0,
        }
        return self._keysort(monthly_volumes, order)


    def post_forecast_segment_parameters(
            self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str,
            data: ItemList) -> ItemList:
        """
        Inserts a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/#498a95b7-5c23-4aae-b92a-191503ac0c5c

        Example data:
        [
            {
                "segmentType": "arps",
                "startDate": "2022-07-28",
                "endDate": "2028-07-26",
                "qStart": 497.54078888022735,
                "qEnd": 169.85103,
                "diEffSec": 0.2708,
                "b": 1.3
            },
            {
                "segmentType": "arps_modified",
                "startDate": "2028-07-27",
                "endDate": "2037-07-14",
                "qStart": 497.54078888022735,
                "qEnd": 108.2303,
                "diEffSec": 0.2708,
                "b": 0.9,
                "targetDSwEffSec": 0.06
            }
        ]

        Example response:
        {
            "status": "success",
            "segmentCount": "8,",
            "id": "62b1c13e2750169012ee4515"
        }
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._post_items(url, data)

        return segments


    def put_forecast_segment_parameters(
            self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str,
            data: ItemList) -> ItemList:
        """
        Updates a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/#59772626-e3af-458e-8ec4-9e57287706f6

        Example data:
        [
            {
                "segmentType": "arps",
                "startDate": "2022-07-28",
                "endDate": "2028-07-26",
                "qStart": 497.54078888022735,
                "qEnd": 169.85103,
                "diEffSec": 0.2708,
                "b": 1.3
            },
            {
                "segmentType": "arps_modified",
                "startDate": "2028-07-27",
                "endDate": "2037-07-14",
                "qStart": 497.54078888022735,
                "qEnd": 108.2303,
                "diEffSec": 0.2708,
                "b": 0.9,
                "targetDSwEffSec": 0.06
            }
        ]

        Example response:
        {
            "status": "success",
            "segmentCount": "8,",
            "id": "62b1c13e2750169012ee4515"
        }
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._put_items(url, data)

        return segments


    def delete_forecast_segment_parameters(
            self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str) -> ItemList:
        """
        Deletes a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/#943e863d-2dbd-4f83-a21e-f0305c072c07
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._delete_items(url, data=[])

        return segments
