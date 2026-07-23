from typing import Dict, Optional

import requests

from .base import APIBase, Item, ItemList


GET_LIMIT = 1000


class Directional(APIBase):
    ######
    # URLs
    ######

    def get_directional_surveys_url(self, filters: Optional[Dict[str, str]] = None) -> str:
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

    ###########
    # API calls
    ###########

    def get_directional_surveys(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of directional survey items.

        https://docs.api.combocurve.com/api/get-directional-surveys
        """
        url = self.get_directional_surveys_url(filters)
        params = {'take': GET_LIMIT}
        directional_surveys = self._get_items(url, params)

        return directional_surveys

    def get_directional_survey_by_id(self, directional_survey_id: str) -> Item:
        """
        Returns a directional survey item from its id.

        https://docs.api.combocurve.com/api/get-directional-surveys-by-id
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
        """
        # The endpoint receives a single object body, not a list, so
        # `self._post_items` (which chunks a list) does not apply.
        headers = self.auth.get_auth_headers()
        url = self.get_directional_surveys_url()

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return self._extract_json(response)[0]

    def put_directional_survey_by_id(self, directional_survey_id: str, data: Item) -> Item:
        """
        Updates a specific directional survey from its id. The single-object body
        carries `spatialDataType`, `dataSource`, and `update` / `add` blocks.

        https://docs.api.combocurve.com/api/put-directional-surveys-by-id
        """
        # The endpoint receives a single object body, not a list.
        headers = self.auth.get_auth_headers()
        url = self.get_directional_survey_by_id_url(directional_survey_id)

        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()

        return self._extract_json(response)[0]

    def delete_directional_survey_by_id(self, directional_survey_id: str) -> ItemList:
        """
        Deletes a specific directional survey from its id.

        https://docs.api.combocurve.com/api/delete-directional-surveys-by-id
        """
        url = self.get_directional_survey_by_id_url(directional_survey_id)
        return self._delete_items(url, data=[])
