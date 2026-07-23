from typing import Dict, Optional

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class ForecastConfigurations(APIBase):
    ######
    # URLs
    ######

    def get_forecast_configurations_url(self, filters: Optional[Dict[str, str]] = None) -> str:
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

    def get_forecast_configurations(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of forecast configurations. These are the reusable
        forecast-run presets referenced by `post_forecast_run`.

        https://docs.api.combocurve.com/api/get-forecast-configurations

        Example response:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "forecastType": "probabilistic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "monthly_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "oil"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "None",
                                    "enforce_sw": true
                                },
                                "axisCombo": "ratio",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "header_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "fixed_date",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "none",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "last",
                                "peakSensitivity": "mid",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                },
                "createdBy": "string",
                "createdByName": "string",
                "isAdmin": true,
                "createdAt": "2020-01-01",
                "updatedAt": "2020-01-01"
            },
            {
                "id": "5e272d38b78910dd2a1bd691",
                "name": "Example",
                "forecastType": "deterministic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "daily_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "water"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "Low",
                                    "enforce_sw": true
                                },
                                "axisCombo": "ratio",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "last",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "duration_from_last_data",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "mid",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "end_flat",
                                "peakSensitivity": "mid",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                },
                "createdBy": "string",
                "createdByName": "string",
                "isAdmin": true,
                "createdAt": "2020-01-01",
                "updatedAt": "2020-01-01"
            }
        ]
        """
        url = self.get_forecast_configurations_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_forecast_configuration_by_id(self, forecast_configuration_id: str) -> Item:
        """
        Returns a specific forecast configuration from its id.

        https://docs.api.combocurve.com/api/get-forecast-configuration-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "name": "Example",
            "forecastType": "deterministic",
            "project": "string",
            "forecastScope": {
                "auto": true,
                "proximity": true
            },
            "resolution": "daily_preference",
            "overwriteManual": true,
            "automaticForecast": {
                "streamConfigurations": [
                    {
                        "streams": [
                            "gas"
                        ],
                        "configuration": {
                            "modelParameters": {
                                "modelName": "string",
                                "b": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "b2": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "c": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "D_eff": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "D2_eff": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "D_lim_eff_range": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "minus_t_decline_t0": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "minus_t_elf_t_peak": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "minus_t_peak_t0": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "minus_t1_t_peak": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "q_end": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "q_peak": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "q_start": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "t_linear_duration": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "D_lim_eff": 123.45,
                                "b_prior": 123.45,
                                "b_strength": "None",
                                "enforce_sw": true
                            },
                            "axisCombo": "ratio",
                            "basePhase": "string",
                            "valueRange": {
                                "min": 123.45,
                                "max": 123.45
                            },
                            "timeDict": {
                                "mode": "absolute_range",
                                "unit": "string",
                                "numRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "absoluteRange": {
                                    "min": "2020-01-01",
                                    "max": "2020-01-01"
                                },
                                "headerRange": {
                                    "min": "string",
                                    "max": "string"
                                }
                            },
                            "weightDict": {
                                "mode": "string",
                                "unit": "string",
                                "numRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "absoluteRange": {
                                    "min": "2020-01-01",
                                    "max": "2020-01-01"
                                },
                                "value": 123.45
                            },
                            "wellLifeDict": {
                                "wellLifeMethod": "duration_from_today",
                                "num": 123.45,
                                "unit": "string",
                                "fixedDate": "2020-01-01"
                            },
                            "matchEur": {
                                "matchType": "string",
                                "matchForecastId": "5e272d38b78910dd2a1bd691",
                                "matchPercentChange": 123.45,
                                "matchEurNum": 123.45,
                                "errorPercentage": 123.45
                            },
                            "dispersion": 123.45,
                            "flatForecastThres": 123.45,
                            "internalFilter": "none",
                            "internalFilterAll": true,
                            "lowDataThreshold": 123.45,
                            "movingAverageDays": 123.45,
                            "peakPreference": "end_flat",
                            "peakSensitivity": "mid",
                            "percentileRange": {
                                "min": 123.45,
                                "max": 123.45
                            },
                            "qFinal": 123.45,
                            "remove0": true,
                            "shortProdThreshold": 123.45,
                            "useLowDataForecast": true,
                            "useMinimumData": true,
                            "validIdx": 123.45,
                            "percentile": [
                                123.45
                            ],
                            "probPara": [
                                "string"
                            ]
                        },
                        "name": "Example"
                    }
                ]
            },
            "createdBy": "string",
            "createdByName": "string",
            "isAdmin": true,
            "createdAt": "2020-01-01",
            "updatedAt": "2020-01-01"
        }
        """
        url = self.get_forecast_configuration_by_id_url(forecast_configuration_id)
        return self._get_items(url)[0]

    def post_forecast_configurations(self, data: ItemList) -> ItemList:
        """
        Creates one or more forecast configurations.

        https://docs.api.combocurve.com/api/post-forecast-configurations

        Example data:
        [
            {
                "name": "Example",
                "forecastType": "probabilistic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "daily_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "oil"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "High",
                                    "enforce_sw": true
                                },
                                "axisCombo": "rate",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "absolute_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "duration_from_today",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "none",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "max",
                                "peakSensitivity": "low",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                }
            },
            {
                "name": "Example",
                "forecastType": "deterministic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "daily_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "oil"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "Medium",
                                    "enforce_sw": true
                                },
                                "axisCombo": "rate",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "absolute_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "duration_from_today",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "none",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "last",
                                "peakSensitivity": "high",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                }
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
        url = self.get_forecast_configurations_url()
        return self._post_items(url, data)

    def put_forecast_configurations(self, data: ItemList) -> ItemList:
        """
        Upserts one or more forecast configurations.

        https://docs.api.combocurve.com/api/put-forecast-configurations

        Example data:
        [
            {
                "name": "Example",
                "forecastType": "probabilistic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "daily_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "oil"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "High",
                                    "enforce_sw": true
                                },
                                "axisCombo": "rate",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "absolute_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "duration_from_today",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "none",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "max",
                                "peakSensitivity": "low",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                }
            },
            {
                "name": "Example",
                "forecastType": "deterministic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "daily_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "oil"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "Medium",
                                    "enforce_sw": true
                                },
                                "axisCombo": "rate",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "absolute_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "duration_from_today",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "none",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "last",
                                "peakSensitivity": "high",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                }
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
        url = self.get_forecast_configurations_url()
        return self._put_items(url, data)

    def patch_forecast_configurations(self, data: ItemList) -> ItemList:
        """
        Partially updates one or more forecast configurations.

        https://docs.api.combocurve.com/api/patch-forecast-configurations

        Example data:
        [
            {
                "name": "Example",
                "forecastType": "probabilistic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "monthly_only",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "oil"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "High",
                                    "enforce_sw": true
                                },
                                "axisCombo": "rate",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "absolute_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "duration_from_first_data",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "very_high",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "last",
                                "peakSensitivity": "high",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                }
            },
            {
                "name": "Example",
                "forecastType": "probabilistic",
                "project": "string",
                "forecastScope": {
                    "auto": true,
                    "proximity": true
                },
                "resolution": "daily_preference",
                "overwriteManual": true,
                "automaticForecast": {
                    "streamConfigurations": [
                        {
                            "streams": [
                                "water"
                            ],
                            "configuration": {
                                "modelParameters": {
                                    "modelName": "string",
                                    "b": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "b2": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "c": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D2_eff": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff_range": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_decline_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_elf_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t_peak_t0": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "minus_t1_t_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_end": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_peak": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "q_start": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "t_linear_duration": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "D_lim_eff": 123.45,
                                    "b_prior": 123.45,
                                    "b_strength": "Low",
                                    "enforce_sw": true
                                },
                                "axisCombo": "ratio",
                                "basePhase": "string",
                                "valueRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "timeDict": {
                                    "mode": "absolute_range",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "headerRange": {
                                        "min": "string",
                                        "max": "string"
                                    }
                                },
                                "weightDict": {
                                    "mode": "string",
                                    "unit": "string",
                                    "numRange": {
                                        "min": 123.45,
                                        "max": 123.45
                                    },
                                    "absoluteRange": {
                                        "min": "2020-01-01",
                                        "max": "2020-01-01"
                                    },
                                    "value": 123.45
                                },
                                "wellLifeDict": {
                                    "wellLifeMethod": "fixed_date",
                                    "num": 123.45,
                                    "unit": "string",
                                    "fixedDate": "2020-01-01"
                                },
                                "matchEur": {
                                    "matchType": "string",
                                    "matchForecastId": "5e272d38b78910dd2a1bd691",
                                    "matchPercentChange": 123.45,
                                    "matchEurNum": 123.45,
                                    "errorPercentage": 123.45
                                },
                                "dispersion": 123.45,
                                "flatForecastThres": 123.45,
                                "internalFilter": "very_high",
                                "internalFilterAll": true,
                                "lowDataThreshold": 123.45,
                                "movingAverageDays": 123.45,
                                "peakPreference": "max",
                                "peakSensitivity": "low",
                                "percentileRange": {
                                    "min": 123.45,
                                    "max": 123.45
                                },
                                "qFinal": 123.45,
                                "remove0": true,
                                "shortProdThreshold": 123.45,
                                "useLowDataForecast": true,
                                "useMinimumData": true,
                                "validIdx": 123.45,
                                "percentile": [
                                    123.45
                                ],
                                "probPara": [
                                    "string"
                                ]
                            },
                            "name": "Example"
                        }
                    ]
                }
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
        url = self.get_forecast_configurations_url()
        return self._patch_items(url, data)

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
