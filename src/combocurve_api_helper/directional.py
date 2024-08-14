from typing import List, Dict, Optional, Union, Any, Iterator, Mapping, cast

from .base import APIBase, Item, ItemList


GET_LIMIT = 1000


class Directional(APIBase):
    ######
    # URLs
    ######

    def get_directional_surveys_url(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url of directional surveys for a specific project id.
        """
        url = f'{self.API_BASE_URL}/projects/{project_id}/directional-surveys'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url


    def get_directional_survey_by_id_url(self, project_id: str, directional_survey_id: str) -> str:
        """
        Returns the API url for a specific directional survey from its
        directional survey id.
        """
        base_url = self.get_directional_surveys_url(project_id)
        return f'{base_url}/{directional_survey_id}'


    ###########
    # API calls
    ###########


    def get_directional_surveys(self, project_id: str, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of directional survey items for a specific project id.

        https://docs.api.combocurve.com/#e5bd0d9e-32ef-4fc7-9634-01bcc5dd6134

        Example response:
        [
            {
                "id": "64a5d81cdf46498bc8941a00",
                "well": "64a5d81cdf46498bc8941a00",
                "project": "64a5d81cdf46498bc8941a00",
                "dataSource": "IHS",
                "spatialDataType": "NAD27",
                "measuredDepth": [
                    0,
                    10
                ],
                "trueVerticalDepth": [
                    0,
                    10
                ],
                "azimuth": [
                    0,
                    10
                ],
                "inclination": [
                    0,
                    10
                ],
                "deviationEW": [
                    0,
                    10
                ],
                "deviationNS": [
                    0,
                    10
                ],
                "latitude": [
                    0,
                    10
                ],
                "longitude": [
                    0,
                    10
                ],
                "createdAt": "2019-01-01T00:00:00.000Z",
                "updatedAt": "2019-01-01T00:00:00.000Z"
            }
        ]
        """
        url = self.get_directional_surveys_url(project_id, filters)
        params = {'take': GET_LIMIT}
        directional_surveys = self._get_items(url, params)

        return directional_surveys


    def get_directional_survey_by_id(self, project_id: str, directional_survey_id: str) -> Item:
        """
        Returns a directional survey item for a specific project id and
        directional survey id.

        https://docs.api.combocurve.com/#a432abf4-eb7e-425c-8daa-22dd36680d3e

        Example response:
        {
            "id": "64a5d81cdf46498bc8941a00",
            "well": "64a5d81cdf46498bc8941a00",
            "project": "64a5d81cdf46498bc8941a00",
            "dataSource": "IHS",
            "spatialDataType": "NAD27",
            "measuredDepth": [
                0,
                10
            ],
            "trueVerticalDepth": [
                0,
                10
            ],
            "azimuth": [
                0,
                10
            ],
            "inclination": [
                0,
                10
            ],
            "deviationEW": [
                0,
                10
            ],
            "deviationNS": [
                0,
                10
            ],
            "latitude": [
                0,
                10
            ],
            "longitude": [
                0,
                10
            ],
            "createdAt": "2019-01-01T00:00:00.000Z",
            "updatedAt": "2019-01-01T00:00:00.000Z"
        }
        """
        url = self.get_directional_survey_by_id_url(project_id, directional_survey_id)
        directional_surveys = self._get_items(url)

        return directional_surveys[0]
