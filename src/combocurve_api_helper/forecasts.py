import warnings
from typing import Callable, List, Dict, Optional, Union, Any, Iterator, Mapping

import requests
from more_itertools import chunked

from .base import APIBase, Item, ItemList
from ._batch import BatchChunk, BatchWriteResult


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
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
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
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
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
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
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
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> str:
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
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str
    ) -> str:
        """
        Returns the API url for a specific forecast segment parameters from its
        forecast id, well id, phase, and series.
        """

        VALID_PHASES = ['oil', 'gas', 'water']
        VALID_SERIES = ['best', 'p10', 'p50', 'p90']

        if phase.lower() not in VALID_PHASES:
            warnings.warn(f"`phase` '{phase}' is not in list of valid names:\n{VALID_PHASES}")

        if series.lower() not in VALID_SERIES:
            warnings.warn(f"`series` '{series}' is not in list of valid names:\n{VALID_SERIES}")

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

        https://docs.api.combocurve.com/api/get-forecasts

        Example response:
        [
            {
                "createdAt": "2020-01-01",
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "runDate": "2020-01-01",
                "running": true,
                "tags": [
                    {
                        "createdAt": "2020-01-01",
                        "description": "string",
                        "name": "Example",
                        "updatedAt": "2020-01-01"
                    }
                ],
                "type": "string",
                "updatedAt": "2020-01-01"
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

        https://docs.api.combocurve.com/api/post-forecasts

        Example data:
        [
            {
                "name": "Example",
                "type": "string"
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
                    "forecastId": "5e272d38b78910dd2a1bd691",
                    "name": "Example",
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
        url = self.get_forecasts_url(project_id)
        forecasts = self._post_items(url, data)

        return forecasts

    def post_forecast_wells(
        self,
        project_id: str,
        forecast_id: str,
        well_ids: List[str],
        *,
        chunksize: int = 100,
    ) -> ItemList:
        """
        Scope a list of well id's to a specific forecast, for a given project.

        Optionally, specify the `chunksize` to control how many wells are posted
        per request to avoid HTTP 413 Content Too Large or 504 Gateway Timeout errors
        when making requests to the ComboCurve API.

        https://docs.api.combocurve.com/api/post-wells-to-forecast
        """
        # NOTE: we can't use `self._post_items` since it expects the base data to be a list
        # whereas this particular endpoint receives an object

        headers = self.auth.get_auth_headers()
        url = self.get_forecast_wells_url(project_id, forecast_id)

        items: ItemList = []
        for well_ids_chunk in chunked(well_ids, chunksize):
            data = {'wellIds': well_ids_chunk}
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            items.extend(self._extract_json(response))

        return items

    def get_forecast_by_id(self, project_id: str, forecast_id: str) -> Item:
        """
        Returns a specific forecast from its forecast id.

        https://docs.api.combocurve.com/api/get-forecast-by-id

        Example response:
        {
            "createdAt": "2020-01-01",
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "runDate": "2020-01-01",
            "running": true,
            "tags": [
                {
                    "createdAt": "2020-01-01",
                    "description": "string",
                    "name": "Example",
                    "updatedAt": "2020-01-01"
                }
            ],
            "type": "string",
            "updatedAt": "2020-01-01"
        }
        """
        url = self.get_forecast_by_id_url(project_id, forecast_id)
        params = {'take': GET_LIMIT}
        forecasts = self._get_items(url, params)

        return forecasts[0]

    def get_forecast_aries(
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of ARIES parameters for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-aries-forecast

        Example response:
        [
            {
                "forecast": [
                    {
                        "PROPNUM": "string",
                        "WELL NAME": "string",
                        "WELL NUMBER": "string",
                        "INPT ID": "string",
                        "API10": "string",
                        "API12": "string",
                        "API14": "string",
                        "CHOSEN ID": "string",
                        "ARIES ID": "string",
                        "PHDWIN ID": "string",
                        "SECTION": 123,
                        "SEQUENCE": 123,
                        "QUALIFIER": "string",
                        "KEYWORD": "string",
                        "EXPRESSION": "string"
                    }
                ],
                "well": "string"
            }
        ]
        """
        url = self.get_forecast_aries_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)

    def get_forecast_outputs(
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of outputs for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-forecast-outputs

        Example response:
        [
            {
                "best": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "createdAt": "2020-01-01",
                "forecasted": true,
                "forecastedAt": "2020-01-01",
                "forecastedBy": "string",
                "id": "5e272d38b78910dd2a1bd691",
                "forecast": "string",
                "forecastType": "string",
                "forecastSubType": "string",
                "p10": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "p50": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "p90": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45
                        }
                    ],
                    "eur": 123.45
                },
                "phase": "string",
                "ratio": {
                    "segments": [
                        {
                            "b": 123.45,
                            "diEffSec": 123.45,
                            "diNominal": 123.45,
                            "endDate": "2020-01-01",
                            "qEnd": 123.45,
                            "qStart": 123.45,
                            "realizedDSwEffSec": 123.45,
                            "segmentIndex": 123,
                            "segmentType": "string",
                            "startDate": "2020-01-01",
                            "swDate": "2020-01-01",
                            "qSw": 123.45,
                            "slope": 123.45
                        }
                    ],
                    "basePhase": "string",
                    "eur": 123.45
                },
                "reviewedAt": "2020-01-01",
                "reviewedBy": "string",
                "runDate": "2020-01-01",
                "status": "string",
                "typeCurve": "string",
                "typeCurveApplySettings": {
                    "applyNormalization": true,
                    "fpdSource": "string",
                    "riskFactor": 123.45
                },
                "typeCurveData": {
                    "name": "Example",
                    "type": "string"
                },
                "updatedAt": "2020-01-01",
                "well": "string",
                "data_freq": "string"
            }
        ]
        """
        url = self.get_forecast_outputs_url(project_id, forecast_id, filters)
        params = {'take': GET_LIMIT_OUTPUTS_ARIES}
        return self._get_items(url, params)

    def get_forecast_output_by_id(self, project_id: str, forecast_id: str, output_id: str) -> Item:
        """
        Returns a specific forecast output from its forecast id and output id.

        https://docs.api.combocurve.com/api/get-forecast-output-by-id

        Example response:
        {
            "best": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45
                    }
                ],
                "eur": 123.45
            },
            "createdAt": "2020-01-01",
            "forecasted": true,
            "forecastedAt": "2020-01-01",
            "forecastedBy": "string",
            "id": "5e272d38b78910dd2a1bd691",
            "forecast": "string",
            "forecastType": "string",
            "forecastSubType": "string",
            "p10": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45
                    }
                ],
                "eur": 123.45
            },
            "p50": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45
                    }
                ],
                "eur": 123.45
            },
            "p90": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45
                    }
                ],
                "eur": 123.45
            },
            "phase": "string",
            "ratio": {
                "segments": [
                    {
                        "b": 123.45,
                        "diEffSec": 123.45,
                        "diNominal": 123.45,
                        "endDate": "2020-01-01",
                        "qEnd": 123.45,
                        "qStart": 123.45,
                        "realizedDSwEffSec": 123.45,
                        "segmentIndex": 123,
                        "segmentType": "string",
                        "startDate": "2020-01-01",
                        "swDate": "2020-01-01",
                        "qSw": 123.45,
                        "slope": 123.45
                    }
                ],
                "basePhase": "string",
                "eur": 123.45
            },
            "reviewedAt": "2020-01-01",
            "reviewedBy": "string",
            "runDate": "2020-01-01",
            "status": "string",
            "typeCurve": "string",
            "typeCurveApplySettings": {
                "applyNormalization": true,
                "fpdSource": "string",
                "riskFactor": 123.45
            },
            "typeCurveData": {
                "name": "Example",
                "type": "string"
            },
            "updatedAt": "2020-01-01",
            "well": "string",
            "data_freq": "string"
        }
        """
        url = self.get_forecast_output_by_id_url(project_id, forecast_id, output_id)
        params = {'take': GET_LIMIT}
        outputs = self._get_items(url, params)

        return outputs[0]

    def get_forecast_daily_volumes(
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of daily volumes for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-forecast-daily-volumes

        Example response:
        [
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "probabilistic",
                "well": "string",
                "resolution": "daily",
                "phases": [
                    {
                        "phase": "customNumber4",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P50",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "water",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    },
                    {
                        "phase": "oil",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "best",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            },
                            {
                                "eur": 123.45,
                                "series": "P90",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "gas",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    }
                ]
            },
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "probabilistic",
                "well": "string",
                "resolution": "monthly",
                "phases": [
                    {
                        "phase": "customNumber3",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P50",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            },
                            {
                                "eur": 123.45,
                                "series": "P90",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "water",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    },
                    {
                        "phase": "_project_custom_stream_16",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P90",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            },
                            {
                                "eur": 123.45,
                                "series": "P10",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "oil",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
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
        self, project_id: str, forecast_id: str, filters: Optional[Dict[str, str]] = None
    ) -> ItemList:
        """
        Returns a list of monthly volumes for a specific project id and forecast id.

        https://docs.api.combocurve.com/api/get-forecast-monthly-volumes

        Example response:
        [
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "probabilistic",
                "well": "string",
                "resolution": "daily",
                "phases": [
                    {
                        "phase": "customNumber4",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P50",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "water",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    },
                    {
                        "phase": "oil",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "best",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            },
                            {
                                "eur": 123.45,
                                "series": "P90",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "gas",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    }
                ]
            },
            {
                "project": "string",
                "forecast": "string",
                "forecastType": "probabilistic",
                "well": "string",
                "resolution": "monthly",
                "phases": [
                    {
                        "phase": "customNumber3",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P50",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            },
                            {
                                "eur": 123.45,
                                "series": "P90",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "water",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
                    },
                    {
                        "phase": "_project_custom_stream_16",
                        "series": [
                            {
                                "eur": 123.45,
                                "series": "P90",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            },
                            {
                                "eur": 123.45,
                                "series": "P10",
                                "startDate": "2020-01-01",
                                "endDate": "2020-01-01",
                                "volumes": [
                                    123.45
                                ]
                            }
                        ],
                        "forecastOutputId": "5e272d38b78910dd2a1bd691",
                        "ratio": {
                            "eur": 123.45,
                            "basePhase": "oil",
                            "startDate": "2020-01-01",
                            "endDate": "2020-01-01",
                            "volumes": [
                                123.45
                            ]
                        }
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
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str, data: ItemList
    ) -> ItemList:
        """
        Inserts a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/api/post-projects-forecast-segment-parameters

        Example data:
        [
            {
                "segmentType": "string",
                "startDate": "string",
                "endDate": "string",
                "qStart": 123.45,
                "qEnd": 123.45,
                "diEffSec": 123.45,
                "b": 123.45,
                "targetDSwEffSec": 123.45,
                "flatValue": 123.45,
                "slope": 123.45,
                "realizedDEffSw": 123.45,
                "d": 123.45,
                "dEff": 123.45,
                "calculatedField": "string"
            }
        ]

        Example response:
        {
            "status": "string",
            "segmentCount": 123,
            "id": "5e272d38b78910dd2a1bd691"
        }
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._post_items(url, data)

        return segments

    def put_forecast_segment_parameters(
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str, data: ItemList
    ) -> ItemList:
        """
        Updates a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/api/put-projects-forecast-segment-parameters

        Example data:
        [
            {
                "segmentType": "string",
                "startDate": "string",
                "endDate": "string",
                "qStart": 123.45,
                "qEnd": 123.45,
                "diEffSec": 123.45,
                "b": 123.45,
                "targetDSwEffSec": 123.45,
                "flatValue": 123.45,
                "slope": 123.45,
                "realizedDEffSw": 123.45,
                "d": 123.45,
                "dEff": 123.45,
                "calculatedField": "string"
            }
        ]

        Example response:
        {
            "status": "string",
            "segmentCount": 123,
            "id": "5e272d38b78910dd2a1bd691"
        }
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._put_items(url, data)

        return segments

    def delete_forecast_segment_parameters(
        self, project_id: str, forecast_id: str, well_id: str, phase: str, series: str
    ) -> ItemList:
        """
        Deletes a specific well's forecast parameters from its forecast id,
        well id, phase, and series.

        https://docs.api.combocurve.com/api/delete-projects-forecast-segment-parameters
        """
        url = self.get_forecast_segment_parameters_url(project_id, forecast_id, well_id, phase, series)
        segments = self._delete_items(url, data=[])

        return segments

    # Bulk forecast parameters (whole-forecast PUT) and forecast run (async job)

    def get_forecast_parameters_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url for a forecast's parameters (bulk, whole-forecast).
        Route: /v1/projects/{projectId}/forecasts/{forecastId}/parameters
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        return f'{base_url}/parameters'

    def put_forecast_parameters(
        self, project_id: str, forecast_id: str, data: ItemList, *, chunksize: int = 25
    ) -> ItemList:
        """
        Upserts forecast parameters in bulk for a specific forecast. Each item in
        `data` is one well x phase record ({well, phase, series, forecastType,
        segments, ...}); see `put_forecast_segment_parameters` for the
        single-well variant.

        The endpoint accepts at most 25 well x phase records per PUT, so `data`
        is chunked into groups of `chunksize` (default 25) and each chunk is sent
        as a separate request. A record is one well x phase (not one decline
        segment), so 25 records is e.g. ~8 wells across oil/gas/water; there is
        no separate per-segment limit.
        """
        url = self.get_forecast_parameters_url(project_id, forecast_id)
        return self._put_items(url, data, chunksize)

    def put_forecast_parameters_batched(
        self,
        project_id: str,
        forecast_id: str,
        data: ItemList,
        *,
        chunksize: int = 25,
        max_workers: int = 10,
        on_progress: Optional[Callable[[BatchChunk], None]] = None,
    ) -> BatchWriteResult:
        """Upsert forecast parameters in parallel chunks, returning the 207 envelope.

        Like `put_forecast_parameters`, but sends the (max 25 well x phase
        record) chunks concurrently and returns a `BatchWriteResult` instead of a
        flattened `ItemList`. The endpoint replies 207 Multi-Status, so
        ``result.results[i]`` corresponds to ``data[i]`` and per-record failures
        are preserved (``result.failed_count`` / ``result.ok``) rather than
        silently dropped. Prefer this when you need to detect partial failures or
        want parallel throughput; `on_progress` is called once per completed
        chunk (from the calling thread) for progress reporting.
        """
        url = self.get_forecast_parameters_url(project_id, forecast_id)
        return self._request_batched(
            'put', url, data, chunksize=chunksize, max_workers=max_workers, on_progress=on_progress
        )

    def get_forecast_run_url(self, project_id: str, forecast_id: str) -> str:
        """
        Returns the API url to run a specific forecast.
        Route: /v1/projects/{projectId}/forecasts/{forecastId}/run
        """
        base_url = self.get_forecast_by_id_url(project_id, forecast_id)
        return f'{base_url}/run'

    def get_forecast_run_by_job_id_url(self, project_id: str, forecast_id: str, job_id: str) -> str:
        """
        Returns the API url for the status of a specific forecast run job.
        Route: /v1/projects/{projectId}/forecasts/{forecastId}/run/{jobId}
        """
        base_url = self.get_forecast_run_url(project_id, forecast_id)
        return f'{base_url}/{job_id}'

    def post_forecast_run(self, project_id: str, forecast_id: str, configuration_id: Optional[str] = None) -> ItemList:
        """
        Starts an (async) run of a specific forecast, optionally using a named
        forecast configuration. Returns the run job (carrying its `jobId`); poll
        `get_forecast_run_by_job_id` for status.
        """
        # The run endpoint receives a single object body ({configurationId}), not
        # a list, so `self._post_items` (which chunks a list) does not apply.
        headers = self.auth.get_auth_headers()
        url = self.get_forecast_run_url(project_id, forecast_id)

        data: Dict[str, str] = {}
        if configuration_id is not None:
            data['configurationId'] = configuration_id

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return self._extract_json(response)

    def get_forecast_run_by_job_id(self, project_id: str, forecast_id: str, job_id: str) -> Item:
        """
        Returns the status of a specific forecast run job from its job id.
        """
        url = self.get_forecast_run_by_job_id_url(project_id, forecast_id, job_id)
        jobs = self._get_items(url)

        return jobs[0]
