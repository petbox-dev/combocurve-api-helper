from typing import Optional, cast

from requests.structures import CaseInsensitiveDict

from .base import APIBase, Item, ItemList, WriteResponse

# The API maximum of `take` on this route is 100 (verified live 2026-11-05: 1000 answers 400).
GET_LIMIT = 100


class Directional(APIBase):
    ######
    # URLs
    ######

    def get_directional_surveys_url(self, filters: Optional[dict[str, str]] = None) -> str:
        """
        Returns the API url for directional surveys.
        """
        url = f'{self.API_BASE_URL}/directional-surveys'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_directional_survey_by_id_url(self, directional_survey_id: str) -> str:
        """
        Returns the API url for a specific directional survey from its id.
        """
        base_url = self.get_directional_surveys_url()
        return f'{base_url}/{directional_survey_id}'

    def get_directional_surveys_batch_url(self) -> str:
        """
        Returns the API url of the directional-survey batch upsert.
        """
        return f'{self.get_directional_surveys_url()}/batch'

    ###########
    # API calls
    ###########

    def get_directional_surveys(self, filters: Optional[dict[str, str]] = None) -> ItemList:
        """
        Returns a list of directional survey items.

        https://docs.api.combocurve.com/api/get-directional-surveys

        Example response:
        [
            {
                "id": "5e272d38b78910dd2a1bd691",
                "well": "string",
                "measuredDepth": [
                    123.45
                ],
                "trueVerticalDepth": [
                    123.45
                ],
                "azimuth": [
                    123.45
                ],
                "inclination": [
                    123.45
                ],
                "deviationNS": [
                    123.45
                ],
                "deviationEW": [
                    123.45
                ],
                "latitude": [
                    123.45
                ],
                "longitude": [
                    123.45
                ],
                "project": "string",
                "createdAt": "2020-01-01T00:00:00.000Z",
                "updatedAt": "2020-01-01T00:00:00.000Z"
            }
        ]
        """
        url = self.get_directional_surveys_url(filters)
        params = {'take': GET_LIMIT}
        directional_surveys = self._get_items(url, params)

        return directional_surveys

    def count_directional_surveys(self, filters: Optional[dict[str, str]] = None) -> int:
        """
        Returns the number of directional surveys matching `filters`, from the
        `X-Query-Count` header of a HEAD request (no documents are fetched).

        https://docs.api.combocurve.com/api/head-directional-surveys
        """
        return self._count_items(self.get_directional_surveys_url(filters))

    def get_directional_survey_by_id(self, directional_survey_id: str) -> Item:
        """
        Returns a directional survey item from its id.

        https://docs.api.combocurve.com/api/get-directional-surveys-by-id

        Example response:
        {
            "id": "5e272d38b78910dd2a1bd691",
            "well": "string",
            "measuredDepth": [
                123.45
            ],
            "trueVerticalDepth": [
                123.45
            ],
            "azimuth": [
                123.45
            ],
            "inclination": [
                123.45
            ],
            "deviationNS": [
                123.45
            ],
            "deviationEW": [
                123.45
            ],
            "latitude": [
                123.45
            ],
            "longitude": [
                123.45
            ],
            "project": "string",
            "createdAt": "2020-01-01T00:00:00.000Z",
            "updatedAt": "2020-01-01T00:00:00.000Z"
        }
        """
        url = self.get_directional_survey_by_id_url(directional_survey_id)
        directional_surveys = self._get_items(url)

        return directional_surveys[0]

    def post_directional_surveys(self, data: Item) -> Item:
        """
        Creates a directional survey. The single-object body carries `chosenID`,
        `dataSource`, `spatialDataType`, the depth / coordinate arrays, and
        `projectID` (the project is specified in the body, not the URL).

        https://docs.api.combocurve.com/api/post-directional-surveys

        Example data:
        {
            "chosenID": "string",
            "dataSource": "string",
            "spatialDataType": "WGS84",
            "measuredDepth": [
                123.45
            ],
            "trueVerticalDepth": [
                123.45
            ],
            "azimuth": [
                123.45
            ],
            "inclination": [
                123.45
            ],
            "deviationEW": [
                123.45
            ],
            "deviationNS": [
                123.45
            ],
            "latitude": [
                123.45
            ],
            "longitude": [
                123.45
            ],
            "projectID": "string"
        }

        Example response:
        {
            "status": "string",
            "code": 123.45,
            "chosenID": "string",
            "errors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string",
                    "chosenID": "string"
                }
            ]
        }
        """
        # The endpoint receives a single object body, not a list, so
        # `self._post_items` (which chunks a list) does not apply.
        url = self.get_directional_surveys_url()

        return self._send_for_item('post', url, data)

    def post_directional_surveys_batch(self, data: ItemList) -> list[WriteResponse]:
        """
        Upserts several directional surveys in one request, one per well. Each record carries the same
        fields as the `post_directional_surveys` body (`chosenID`, `dataSource`, `spatialDataType`, the depth
        and coordinate arrays, and `projectID`). The response is 207 Multi-Status with one `results` entry
        per record, keyed by `chosenID`: a record the server refuses is reported there, not raised. An empty
        list raises `ValueError` before anything is sent. `data` is sent in one request; the documentation
        states no record limit, and none was measured.

        Verified live 2026-11-21 on dev: the well is found by `chosenID`, `dataSource` and `projectID`. A
        well with no survey gets one (`status` `created`, `code` 201); a well that has one has it replaced
        (`updated`, 200; the arrays are the new ones, the survey id is kept). A record whose well is not
        found is `status` `Error`, `code` 404, `WellNotFound`, while the other records are applied. The
        envelope had no `generalErrors` key when there were none.

        https://docs.api.combocurve.com/api/post-directional-surveys-batch

        Example data:
        [
            {
                "chosenID": "string",
                "dataSource": "string",
                "spatialDataType": "NAD27",
                "measuredDepth": [
                    123.45
                ],
                "trueVerticalDepth": [
                    123.45
                ],
                "azimuth": [
                    123.45
                ],
                "inclination": [
                    123.45
                ],
                "deviationEW": [
                    123.45
                ],
                "deviationNS": [
                    123.45
                ],
                "latitude": [
                    123.45
                ],
                "longitude": [
                    123.45
                ],
                "projectID": "string"
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
                    "chosenID": "string",
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
        self._require_records(data, 'directional survey')
        url = self.get_directional_surveys_batch_url()
        return cast('list[WriteResponse]', self._post_items(url, data))

    def put_directional_survey_by_id(self, directional_survey_id: str, data: Item) -> Item:
        """
        Updates a specific directional survey from its id. The single-object body
        carries `spatialDataType`, `dataSource`, and `update` / `add` blocks.

        https://docs.api.combocurve.com/api/put-directional-surveys

        Example data:
        {
            "spatialDataType": "NAD83",
            "dataSource": "string",
            "update": {
                "measuredDepth": [
                    123.45
                ],
                "trueVerticalDepth": [
                    123.45
                ],
                "latitude": [
                    123.45
                ],
                "longitude": [
                    123.45
                ],
                "azimuth": [
                    123.45
                ],
                "inclination": [
                    123.45
                ],
                "deviationEW": [
                    123.45
                ],
                "deviationNS": [
                    123.45
                ]
            },
            "add": {
                "measuredDepth": [
                    123.45
                ],
                "trueVerticalDepth": [
                    123.45
                ],
                "azimuth": [
                    123.45
                ],
                "inclination": [
                    123.45
                ],
                "deviationEW": [
                    123.45
                ],
                "deviationNS": [
                    123.45
                ],
                "latitude": [
                    123.45
                ],
                "longitude": [
                    123.45
                ]
            },
            "remove": [
                123.45
            ]
        }

        Example response:
        {
            "status": "string",
            "code": 123.45,
            "chosenID": "string",
            "errors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string",
                    "chosenID": "string"
                }
            ]
        }
        """
        # The endpoint receives a single object body, not a list.
        url = self.get_directional_survey_by_id_url(directional_survey_id)

        return self._send_for_item('put', url, data)

    def delete_directional_survey_by_id(self, directional_survey_id: str) -> CaseInsensitiveDict[str]:
        """
        Deletes a specific directional survey from its id, and returns the headers of the delete response.

        The route answers a success with an empty body (verified live 2026-11-21 on dev). Through 3.2.0 this
        method returned the parsed body, so it raised `JSONDecodeError` after the survey was already deleted;
        it now returns the headers, like the other delete-by-id methods.

        https://docs.api.combocurve.com/api/delete-directional-surveys-by-id
        """
        url = self.get_directional_survey_by_id_url(directional_survey_id)
        return self._delete_headers(url)
