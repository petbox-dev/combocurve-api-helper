from typing import List, Dict, Optional, Union, Any, Iterator, Mapping

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class TypeCurves(APIBase):
    ######
    # URLs
    ######

    def get_type_curves_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of type curves for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/type-curves'
        if filters is None:
            return url

        parameters: List[str] = []
        for key, value in filters.items():
            parameters.append(f'{key}={value}')

        url += '?' + '&'.join(parameters)
        return url


    def get_type_curve_by_id_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for a specific type curve from its type curve id.
        """
        base_url = self.get_type_curves_url(project_id)
        return f'{base_url}/{type_curve_id}'


    def get_type_curve_representative_wells_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for representative wells for a specific project id
        and type curve id.
        """
        base_url = self.get_type_curve_by_id_url(project_id, type_curve_id)
        return f'{base_url}/representative-wells'


    def get_type_curve_daily_fits_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for daily fits for a specific project id and
        type curve id.
        """
        base_url = self.get_type_curve_by_id_url(project_id, type_curve_id)
        return f'{base_url}/daily-fits'


    def get_type_curve_monthly_fits_url(self, project_id: str, type_curve_id: str) -> str:
        """
        Returns the API url for monthly fits for a specific project id and
        type curve id.
        """
        base_url = self.get_type_curve_by_id_url(project_id, type_curve_id)
        return f'{base_url}/monthly-fits'


    ###########
    # API calls
    ###########


    def get_type_curves(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of type curves for a specific project id.

        https://docs.api.combocurve.com/#8bee4cfe-8385-449f-bf14-fcbefae49376

        Example response:
        [
            {
                "id": "5f971a8f6749f60012dcb93a",
                "fits": {
                    "gas": {
                        "align": "noalign",
                        "type": "ratio",
                        "ratio": {
                            "best": {
                                "segments": [
                                    {
                                        "diEffSec": -1.9356784875378144e+64,
                                        "diNominal": -0.40527283738862535,
                                        "endDate": "1900-01-03T00:00:00.000Z",
                                        "qEnd": 0.65,
                                        "qStart": 0.289,
                                        "segmentIndex": 1,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-01-01T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "diEffSec": -2329943.3656889563,
                                        "diNominal": -0.04014060218444928,
                                        "endDate": "1900-02-04T00:00:00.000Z",
                                        "qEnd": 2.255960335333368,
                                        "qStart": 0.65,
                                        "segmentIndex": 2,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-01-04T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "diEffSec": -2.207990593837427,
                                        "diNominal": -0.003191361417944981,
                                        "endDate": "1900-09-16T00:00:00.000Z",
                                        "qEnd": 4.596289501233267,
                                        "qStart": 2.255960335333368,
                                        "segmentIndex": 3,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-02-05T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "diEffSec": -0.19878365762011524,
                                        "diNominal": -0.000496392673744735,
                                        "endDate": "1902-01-02T00:00:00.000Z",
                                        "qEnd": 5.809803154555608,
                                        "qStart": 4.596289501233268,
                                        "segmentIndex": 4,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-09-17T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "diEffSec": 0.2834768765929031,
                                        "diNominal": 0.0009126482122112908,
                                        "endDate": "1902-06-06T00:00:00.000Z",
                                        "qEnd": 5.050540452347935,
                                        "qStart": 5.812687814180152,
                                        "segmentIndex": 5,
                                        "segmentType": "exp_dec",
                                        "startDate": "1902-01-03T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "diEffSec": -0.2700709020179275,
                                        "diNominal": -0.0006545454545454557,
                                        "endDate": "1902-08-01T00:00:00.000Z",
                                        "qEnd": 5.230896140714752,
                                        "qStart": 5.045933188358814,
                                        "segmentIndex": 6,
                                        "segmentType": "exp_inc",
                                        "startDate": "1902-06-07T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "endDate": "1957-05-04T00:00:00.000Z",
                                        "qEnd": 5230.896140714753,
                                        "qStart": 5.230896140714752,
                                        "segmentIndex": 7,
                                        "segmentType": "flat",
                                        "startDate": "1902-08-02T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    }
                                ],
                                "basePhase": "oil"
                            },
                            "p10": {
                                "segments": [
                                    {
                                        "diEffSec": -19.03019588305437,
                                        "diNominal": -0.008205998436997675,
                                        "endDate": "1900-06-14T00:00:00.000Z",
                                        "qEnd": 9.934713702278211,
                                        "qStart": 2.586359568181722,
                                        "segmentIndex": 1,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-01-01T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "endDate": "1960-01-01T00:00:00.000Z",
                                        "qEnd": 10,
                                        "qStart": 10,
                                        "segmentIndex": 2,
                                        "segmentType": "flat",
                                        "startDate": "1900-06-15T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    }
                                ],
                                "basePhase": "oil"
                            },
                            "p50": {
                                "segments": [
                                    {
                                        "diEffSec": -0.8197624792373521,
                                        "diNominal": -0.00163916765683374,
                                        "endDate": "1901-08-02T00:00:00.000Z",
                                        "qEnd": 4.495562361966487,
                                        "qStart": 1.7430768614506325,
                                        "segmentIndex": 1,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-01-01T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "endDate": "1960-01-01T00:00:00.000Z",
                                        "qEnd": 4.500726935245159,
                                        "qStart": 4.500726935245159,
                                        "segmentIndex": 2,
                                        "segmentType": "flat",
                                        "startDate": "1901-08-03T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    }
                                ],
                                "basePhase": "oil"
                            },
                            "p90": {
                                "segments": [
                                    {
                                        "diEffSec": -1.254722746009547,
                                        "diNominal": -0.0022259466519473133,
                                        "endDate": "1902-01-16T00:00:00.000Z",
                                        "qEnd": 2.085760285022735,
                                        "qStart": 0.39724708091575084,
                                        "segmentIndex": 1,
                                        "segmentType": "exp_inc",
                                        "startDate": "1900-01-01T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    },
                                    {
                                        "endDate": "1960-01-01T00:00:00.000Z",
                                        "qEnd": 2.0889017962137455,
                                        "qStart": 2.0889017962137455,
                                        "segmentIndex": 2,
                                        "segmentType": "flat",
                                        "startDate": "1902-01-17T00:00:00.000Z",
                                        "swDate": "1900-01-01T00:00:00.000Z"
                                    }
                                ],
                                "basePhase": "oil"
                            }
                        }
                    },
                    "oil": {
                        "align": "align",
                        "best": {
                            "segments": [
                                {
                                    "b": 1.5091302849041728,
                                    "diEffSec": 0.8087956942539849,
                                    "diNominal": 0.020214904578588575,
                                    "endDate": "1903-11-02T00:00:00.000Z",
                                    "qEnd": 46.30140751606845,
                                    "qStart": 565.8426475633156,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.40796215056740753,
                                    "diEffSec": 0.15067845386557088,
                                    "diNominal": 0.0004623709905521584,
                                    "endDate": "1946-03-01T00:00:00.000Z",
                                    "qEnd": 0.8000369356121517,
                                    "qStart": 46.280001967410215,
                                    "realizedDSwEffSec": 0.07999999999999985,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1903-11-03T00:00:00.000Z",
                                    "swDate": "1918-03-23T10:42:42.546Z"
                                }
                            ]
                        },
                        "type": "rate",
                        "p10": {
                            "segments": [
                                {
                                    "b": 1.4473065847374396,
                                    "diEffSec": 0.7901205746441922,
                                    "diNominal": 0.016228668706516017,
                                    "endDate": "1905-04-16T00:00:00.000Z",
                                    "qEnd": 69.88448111424226,
                                    "qStart": 989.8093811909654,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.2780164284502177,
                                    "diEffSec": 0.11805629470557266,
                                    "diNominal": 0.00035002509565129283,
                                    "endDate": "1955-01-20T00:00:00.000Z",
                                    "qEnd": 0.8000862491347466,
                                    "qStart": 69.86002257138924,
                                    "realizedDSwEffSec": 0.0800000000000003,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1905-04-17T00:00:00.000Z",
                                    "swDate": "1919-10-19T01:26:39.667Z"
                                }
                            ]
                        },
                        "p50": {
                            "segments": [
                                {
                                    "b": 1.4504077622226106,
                                    "diEffSec": 0.8333589669012218,
                                    "diNominal": 0.02350180017998131,
                                    "endDate": "1904-04-15T00:00:00.000Z",
                                    "qEnd": 33.4881622297015,
                                    "qStart": 526.2895049856261,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.37818635840198644,
                                    "diEffSec": 0.14215900419970873,
                                    "diNominal": 0.00043222366174103564,
                                    "endDate": "1943-05-27T00:00:00.000Z",
                                    "qEnd": 0.8001067084111635,
                                    "qStart": 33.4736879281039,
                                    "realizedDSwEffSec": 0.08000000000000007,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1904-04-16T00:00:00.000Z",
                                    "swDate": "1918-10-03T11:38:55.651Z"
                                }
                            ]
                        },
                        "p90": {
                            "segments": [
                                {
                                    "b": 1.330976365522085,
                                    "diEffSec": 0.8651203747969143,
                                    "diNominal": 0.027540833225479046,
                                    "endDate": "1904-08-11T00:00:00.000Z",
                                    "qEnd": 11.737596991926225,
                                    "qStart": 262.95245274414793,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.4015966656320213,
                                    "diEffSec": 0.14396037326298317,
                                    "diNominal": 0.00043913121734991134,
                                    "endDate": "1931-05-29T00:00:00.000Z",
                                    "qEnd": 0.8001156867048187,
                                    "qStart": 11.732443044339771,
                                    "realizedDSwEffSec": 0.08000000000000007,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1904-08-12T00:00:00.000Z",
                                    "swDate": "1918-06-15T14:03:37.341Z"
                                }
                            ]
                        }
                    },
                    "water": {
                        "align": "align",
                        "best": {
                            "segments": [
                                {
                                    "b": 1.2680338558089648,
                                    "diEffSec": 0.8363358318632641,
                                    "diNominal": 0.01927038542826107,
                                    "endDate": "1904-07-03T00:00:00.000Z",
                                    "qEnd": 88.51217611065589,
                                    "qStart": 1660.7876917443944,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.3700527996951682,
                                    "diEffSec": 0.15271300615018446,
                                    "diNominal": 0.0004679053456603507,
                                    "endDate": "1953-10-08T00:00:00.000Z",
                                    "qEnd": 0.8000019740163588,
                                    "qStart": 88.47076608622676,
                                    "realizedDSwEffSec": 0.08000000000000007,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1904-07-04T00:00:00.000Z",
                                    "swDate": "1920-08-09T08:42:03.495Z"
                                }
                            ]
                        },
                        "type": "rate",
                        "p10": {
                            "segments": [
                                {
                                    "b": 1.2995634725098673,
                                    "diEffSec": 0.8221473319816679,
                                    "diNominal": 0.01776364438358374,
                                    "endDate": "1904-11-09T00:00:00.000Z",
                                    "qEnd": 159.71665502377877,
                                    "qStart": 2830.4983593264888,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.3605208385003536,
                                    "diEffSec": 0.13975144611361723,
                                    "diNominal": 0.0004235280148922512,
                                    "endDate": "1960-01-01T00:00:00.000Z",
                                    "qEnd": 0.9890791185137173,
                                    "qStart": 159.649017967522,
                                    "realizedDSwEffSec": 0.07999999999999985,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1904-11-10T00:00:00.000Z",
                                    "swDate": "1919-09-12T11:22:10.083Z"
                                }
                            ]
                        },
                        "p50": {
                            "segments": [
                                {
                                    "b": 1.1320253716029958,
                                    "diEffSec": 0.8986812923088446,
                                    "diNominal": 0.02987667216831467,
                                    "endDate": "1904-11-02T00:00:00.000Z",
                                    "qEnd": 42.68452543225325,
                                    "qStart": 1605.7135455277207,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.4262168225004256,
                                    "diEffSec": 0.1589519988663871,
                                    "diNominal": 0.0004918617911779854,
                                    "endDate": "1945-07-18T00:00:00.000Z",
                                    "qEnd": 0.800065977018731,
                                    "qStart": 42.66353349737412,
                                    "realizedDSwEffSec": 0.08000000000000007,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1904-11-03T00:00:00.000Z",
                                    "swDate": "1919-06-03T21:56:02.275Z"
                                }
                            ]
                        },
                        "p90": {
                            "segments": [
                                {
                                    "b": 1.2452224501905522,
                                    "diEffSec": 0.8145245566245766,
                                    "diNominal": 0.01572011965705079,
                                    "endDate": "1905-05-16T00:00:00.000Z",
                                    "qEnd": 15.211161895059824,
                                    "qStart": 290.62867530434505,
                                    "segmentIndex": 1,
                                    "segmentType": "arps",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "b": 0.32178592715641674,
                                    "diEffSec": 0.13275639979523757,
                                    "diNominal": 0.0003990417218176966,
                                    "endDate": "1935-08-18T00:00:00.000Z",
                                    "qEnd": 0.8000578016564031,
                                    "qStart": 15.20509278187113,
                                    "realizedDSwEffSec": 0.07999999999999985,
                                    "segmentIndex": 2,
                                    "segmentType": "arps_modified",
                                    "startDate": "1905-05-17T00:00:00.000Z",
                                    "swDate": "1920-10-28T08:45:20.063Z"
                                }
                            ]
                        }
                    }
                },
                "forecast": "5f85c4df8420070012ca8d75",
                "name": "TC1"
            }
        ]
        """
        url = self.get_type_curves_url(project_id, filters)
        params = {'take': GET_LIMIT}
        type_curves = self._get_items(url, params)

        order = {
            'name': 0,
            'id': 3,
            'createdAt': 2,
            'updatedAt': 1,
        }
        return self._keysort(type_curves, order)


    def get_type_curve_by_id(self, project_id: str, type_curve_id: str) -> Item:
        """
        Returns a specific type curve from its type curve id.

        https://docs.api.combocurve.com/#d28fbde4-9213-46ee-bec8-3fb3ef8658f4

        Example response:
        {
            "id": "5f971a8f6749f60012dcb93a",
            "fits": {
                "gas": {
                    "align": "noalign",
                    "type": "ratio",
                    "ratio": {
                        "best": {
                            "segments": [
                                {
                                    "diEffSec": -1.9356784875378144e+64,
                                    "diNominal": -0.40527283738862535,
                                    "endDate": "1900-01-03T00:00:00.000Z",
                                    "qEnd": 0.65,
                                    "qStart": 0.289,
                                    "segmentIndex": 1,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "diEffSec": -2329943.3656889563,
                                    "diNominal": -0.04014060218444928,
                                    "endDate": "1900-02-04T00:00:00.000Z",
                                    "qEnd": 2.255960335333368,
                                    "qStart": 0.65,
                                    "segmentIndex": 2,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-01-04T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "diEffSec": -2.207990593837427,
                                    "diNominal": -0.003191361417944981,
                                    "endDate": "1900-09-16T00:00:00.000Z",
                                    "qEnd": 4.596289501233267,
                                    "qStart": 2.255960335333368,
                                    "segmentIndex": 3,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-02-05T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "diEffSec": -0.19878365762011524,
                                    "diNominal": -0.000496392673744735,
                                    "endDate": "1902-01-02T00:00:00.000Z",
                                    "qEnd": 5.809803154555608,
                                    "qStart": 4.596289501233268,
                                    "segmentIndex": 4,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-09-17T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "diEffSec": 0.2834768765929031,
                                    "diNominal": 0.0009126482122112908,
                                    "endDate": "1902-06-06T00:00:00.000Z",
                                    "qEnd": 5.050540452347935,
                                    "qStart": 5.812687814180152,
                                    "segmentIndex": 5,
                                    "segmentType": "exp_dec",
                                    "startDate": "1902-01-03T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "diEffSec": -0.2700709020179275,
                                    "diNominal": -0.0006545454545454557,
                                    "endDate": "1902-08-01T00:00:00.000Z",
                                    "qEnd": 5.230896140714752,
                                    "qStart": 5.045933188358814,
                                    "segmentIndex": 6,
                                    "segmentType": "exp_inc",
                                    "startDate": "1902-06-07T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "endDate": "1957-05-04T00:00:00.000Z",
                                    "qEnd": 5230.896140714753,
                                    "qStart": 5.230896140714752,
                                    "segmentIndex": 7,
                                    "segmentType": "flat",
                                    "startDate": "1902-08-02T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                }
                            ],
                            "basePhase": "oil"
                        },
                        "p10": {
                            "segments": [
                                {
                                    "diEffSec": -19.03019588305437,
                                    "diNominal": -0.008205998436997675,
                                    "endDate": "1900-06-14T00:00:00.000Z",
                                    "qEnd": 9.934713702278211,
                                    "qStart": 2.586359568181722,
                                    "segmentIndex": 1,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "endDate": "1960-01-01T00:00:00.000Z",
                                    "qEnd": 10,
                                    "qStart": 10,
                                    "segmentIndex": 2,
                                    "segmentType": "flat",
                                    "startDate": "1900-06-15T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                }
                            ],
                            "basePhase": "oil"
                        },
                        "p50": {
                            "segments": [
                                {
                                    "diEffSec": -0.8197624792373521,
                                    "diNominal": -0.00163916765683374,
                                    "endDate": "1901-08-02T00:00:00.000Z",
                                    "qEnd": 4.495562361966487,
                                    "qStart": 1.7430768614506325,
                                    "segmentIndex": 1,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "endDate": "1960-01-01T00:00:00.000Z",
                                    "qEnd": 4.500726935245159,
                                    "qStart": 4.500726935245159,
                                    "segmentIndex": 2,
                                    "segmentType": "flat",
                                    "startDate": "1901-08-03T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                }
                            ],
                            "basePhase": "oil"
                        },
                        "p90": {
                            "segments": [
                                {
                                    "diEffSec": -1.254722746009547,
                                    "diNominal": -0.0022259466519473133,
                                    "endDate": "1902-01-16T00:00:00.000Z",
                                    "qEnd": 2.085760285022735,
                                    "qStart": 0.39724708091575084,
                                    "segmentIndex": 1,
                                    "segmentType": "exp_inc",
                                    "startDate": "1900-01-01T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                },
                                {
                                    "endDate": "1960-01-01T00:00:00.000Z",
                                    "qEnd": 2.0889017962137455,
                                    "qStart": 2.0889017962137455,
                                    "segmentIndex": 2,
                                    "segmentType": "flat",
                                    "startDate": "1902-01-17T00:00:00.000Z",
                                    "swDate": "1900-01-01T00:00:00.000Z"
                                }
                            ],
                            "basePhase": "oil"
                        }
                    }
                },
                "oil": {
                    "align": "align",
                    "best": {
                        "segments": [
                            {
                                "b": 1.5091302849041728,
                                "diEffSec": 0.8087956942539849,
                                "diNominal": 0.020214904578588575,
                                "endDate": "1903-11-02T00:00:00.000Z",
                                "qEnd": 46.30140751606845,
                                "qStart": 565.8426475633156,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.40796215056740753,
                                "diEffSec": 0.15067845386557088,
                                "diNominal": 0.0004623709905521584,
                                "endDate": "1946-03-01T00:00:00.000Z",
                                "qEnd": 0.8000369356121517,
                                "qStart": 46.280001967410215,
                                "realizedDSwEffSec": 0.07999999999999985,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1903-11-03T00:00:00.000Z",
                                "swDate": "1918-03-23T10:42:42.546Z"
                            }
                        ]
                    },
                    "type": "rate",
                    "p10": {
                        "segments": [
                            {
                                "b": 1.4473065847374396,
                                "diEffSec": 0.7901205746441922,
                                "diNominal": 0.016228668706516017,
                                "endDate": "1905-04-16T00:00:00.000Z",
                                "qEnd": 69.88448111424226,
                                "qStart": 989.8093811909654,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.2780164284502177,
                                "diEffSec": 0.11805629470557266,
                                "diNominal": 0.00035002509565129283,
                                "endDate": "1955-01-20T00:00:00.000Z",
                                "qEnd": 0.8000862491347466,
                                "qStart": 69.86002257138924,
                                "realizedDSwEffSec": 0.0800000000000003,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1905-04-17T00:00:00.000Z",
                                "swDate": "1919-10-19T01:26:39.667Z"
                            }
                        ]
                    },
                    "p50": {
                        "segments": [
                            {
                                "b": 1.4504077622226106,
                                "diEffSec": 0.8333589669012218,
                                "diNominal": 0.02350180017998131,
                                "endDate": "1904-04-15T00:00:00.000Z",
                                "qEnd": 33.4881622297015,
                                "qStart": 526.2895049856261,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.37818635840198644,
                                "diEffSec": 0.14215900419970873,
                                "diNominal": 0.00043222366174103564,
                                "endDate": "1943-05-27T00:00:00.000Z",
                                "qEnd": 0.8001067084111635,
                                "qStart": 33.4736879281039,
                                "realizedDSwEffSec": 0.08000000000000007,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1904-04-16T00:00:00.000Z",
                                "swDate": "1918-10-03T11:38:55.651Z"
                            }
                        ]
                    },
                    "p90": {
                        "segments": [
                            {
                                "b": 1.330976365522085,
                                "diEffSec": 0.8651203747969143,
                                "diNominal": 0.027540833225479046,
                                "endDate": "1904-08-11T00:00:00.000Z",
                                "qEnd": 11.737596991926225,
                                "qStart": 262.95245274414793,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.4015966656320213,
                                "diEffSec": 0.14396037326298317,
                                "diNominal": 0.00043913121734991134,
                                "endDate": "1931-05-29T00:00:00.000Z",
                                "qEnd": 0.8001156867048187,
                                "qStart": 11.732443044339771,
                                "realizedDSwEffSec": 0.08000000000000007,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1904-08-12T00:00:00.000Z",
                                "swDate": "1918-06-15T14:03:37.341Z"
                            }
                        ]
                    }
                },
                "water": {
                    "align": "align",
                    "best": {
                        "segments": [
                            {
                                "b": 1.2680338558089648,
                                "diEffSec": 0.8363358318632641,
                                "diNominal": 0.01927038542826107,
                                "endDate": "1904-07-03T00:00:00.000Z",
                                "qEnd": 88.51217611065589,
                                "qStart": 1660.7876917443944,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.3700527996951682,
                                "diEffSec": 0.15271300615018446,
                                "diNominal": 0.0004679053456603507,
                                "endDate": "1953-10-08T00:00:00.000Z",
                                "qEnd": 0.8000019740163588,
                                "qStart": 88.47076608622676,
                                "realizedDSwEffSec": 0.08000000000000007,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1904-07-04T00:00:00.000Z",
                                "swDate": "1920-08-09T08:42:03.495Z"
                            }
                        ]
                    },
                    "type": "rate",
                    "p10": {
                        "segments": [
                            {
                                "b": 1.2995634725098673,
                                "diEffSec": 0.8221473319816679,
                                "diNominal": 0.01776364438358374,
                                "endDate": "1904-11-09T00:00:00.000Z",
                                "qEnd": 159.71665502377877,
                                "qStart": 2830.4983593264888,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.3605208385003536,
                                "diEffSec": 0.13975144611361723,
                                "diNominal": 0.0004235280148922512,
                                "endDate": "1960-01-01T00:00:00.000Z",
                                "qEnd": 0.9890791185137173,
                                "qStart": 159.649017967522,
                                "realizedDSwEffSec": 0.07999999999999985,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1904-11-10T00:00:00.000Z",
                                "swDate": "1919-09-12T11:22:10.083Z"
                            }
                        ]
                    },
                    "p50": {
                        "segments": [
                            {
                                "b": 1.1320253716029958,
                                "diEffSec": 0.8986812923088446,
                                "diNominal": 0.02987667216831467,
                                "endDate": "1904-11-02T00:00:00.000Z",
                                "qEnd": 42.68452543225325,
                                "qStart": 1605.7135455277207,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.4262168225004256,
                                "diEffSec": 0.1589519988663871,
                                "diNominal": 0.0004918617911779854,
                                "endDate": "1945-07-18T00:00:00.000Z",
                                "qEnd": 0.800065977018731,
                                "qStart": 42.66353349737412,
                                "realizedDSwEffSec": 0.08000000000000007,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1904-11-03T00:00:00.000Z",
                                "swDate": "1919-06-03T21:56:02.275Z"
                            }
                        ]
                    },
                    "p90": {
                        "segments": [
                            {
                                "b": 1.2452224501905522,
                                "diEffSec": 0.8145245566245766,
                                "diNominal": 0.01572011965705079,
                                "endDate": "1905-05-16T00:00:00.000Z",
                                "qEnd": 15.211161895059824,
                                "qStart": 290.62867530434505,
                                "segmentIndex": 1,
                                "segmentType": "arps",
                                "startDate": "1900-01-01T00:00:00.000Z",
                                "swDate": "1900-01-01T00:00:00.000Z"
                            },
                            {
                                "b": 0.32178592715641674,
                                "diEffSec": 0.13275639979523757,
                                "diNominal": 0.0003990417218176966,
                                "endDate": "1935-08-18T00:00:00.000Z",
                                "qEnd": 0.8000578016564031,
                                "qStart": 15.20509278187113,
                                "realizedDSwEffSec": 0.07999999999999985,
                                "segmentIndex": 2,
                                "segmentType": "arps_modified",
                                "startDate": "1905-05-17T00:00:00.000Z",
                                "swDate": "1920-10-28T08:45:20.063Z"
                            }
                        ]
                    }
                }
            },
            "forecast": "5f85c4df8420070012ca8d75",
            "name": "TC1"
        }
        """
        url = self.get_type_curve_by_id_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        type_curves = self._get_items(url, params)

        return type_curves[0]


    def get_type_curve_representative_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Returns a list of representative wells for a specific project id and
        type curve id.

        https://docs.api.combocurve.com/#ad854ce8-2a59-4c18-b4db-93f7dff5081a

        Example response:
        [
            {
                "api14": "4222739136",
                "wellName": "FIRE EYES 47-38 4AH-EAST",
                "wellNumber": "",
                "gas": {
                    "eur": 211.9239825954883,
                    "dataFrequency": "monthly",
                    "eurPll": "",
                    "forecastType": "rate;automatic",
                    "hasData": true,
                    "hasForecast": true,
                    "rep": true,
                    "valid": true
                },
                "oil": {
                    "eur": 543.3768626963551,
                    "dataFrequency": "monthly",
                    "eurPll": "",
                    "forecastType": "rate;automatic",
                    "hasData": true,
                    "hasForecast": true,
                    "rep": true,
                    "valid": true
                },
                "water": {
                    "eur": 3413.6138535190103,
                    "dataFrequency": "monthly",
                    "eurPll": "",
                    "forecastType": "rate;automatic",
                    "hasData": true,
                    "hasForecast": true,
                    "rep": true,
                    "valid": true
                }
            }
        ]
        """
        url = self.get_type_curve_representative_wells_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        representative_wells = self._get_items(url, params)

        order = {
            'wellName': 0,
            'id': 1,
        }
        return self._keysort(representative_wells, order)


    def get_type_curve_daily_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Returns a list of daily fits for a specific project id and
        type curve id.

        https://docs.api.combocurve.com/#710a5516-f471-4788-91d6-5787a9bea6db

        Example response:
        [
            {
                "date": "01/09/2023",
                "gas": {
                    "best": 100,
                    "p10": 222,
                    "p50": 333,
                    "p90": 4444
                },
                "oil": {
                    "best": 504,
                    "p10": 504,
                    "p50": 504,
                    "p90": 504
                },
                "water": {
                    "best": 7854,
                    "p10": 6523,
                    "p50": 98,
                    "p90": 32
                }
            }
        ]
        """
        url = self.get_type_curve_daily_fits_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        daily_fits = self._get_items(url, params)
        return daily_fits


    def get_type_curve_monthly_fits(self, project_id: str, type_curve_id: str) -> ItemList:
        """
        Returns a list of monthly fits for a specific project id and
        type curve id.

        https://docs.api.combocurve.com/#f226dfec-e4ba-451a-9246-8bb2a4585d40

        Example response:
        [
            {
                "date": "01/09/2023",
                "gas": {
                    "best": 100,
                    "p10": 222,
                    "p50": 333,
                    "p90": 4444
                },
                "oil": {
                    "best": 504,
                    "p10": 504,
                    "p50": 504,
                    "p90": 504
                },
                "water": {
                    "best": 7854,
                    "p10": 6523,
                    "p50": 98,
                    "p90": 32
                }
            }
        ]
        """
        url = self.get_type_curve_monthly_fits_url(project_id, type_curve_id)
        params = {'take': GET_LIMIT}
        monthly_fits = self._get_items(url, params)
        return monthly_fits
