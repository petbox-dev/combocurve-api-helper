import requests

from .base import APIBase, Item


# The async export routes live under /v2 (every other route in this package is /v1);
# their URLs use `APIBase.API_BASE_URL_V2`.


class Exports(APIBase):
    ######
    # URLs
    ######

    def get_v2_export_url(self, kind: str) -> str:
        """
        Returns the API url for submitting a v2 async export of the given kind
        ('forecast-parameters', 'forecast-volumes', 'econ-monthly', 'econ-one-liners').
        """
        return f'{self.API_BASE_URL_V2}/exports/{kind}'

    def get_v2_export_by_job_id_url(self, kind: str, job_id: str) -> str:
        """
        Returns the API url for polling a v2 async export job of the given kind.
        """
        base_url = self.get_v2_export_url(kind)
        return f'{base_url}/{job_id}'

    def get_exports_url(self) -> str:
        """
        Returns the API url for the v1 top-level exports endpoint.
        """
        return f'{self.API_BASE_URL}/exports'

    ###########
    # API calls
    ###########

    def _post_v2_export(self, kind: str, data: Item) -> Item:
        """
        Submits a v2 async export of `kind` (single-object body) and returns the
        job carrying its job id; poll `_get_v2_export` for status/results.
        """
        headers = self.auth.get_auth_headers()
        url = self.get_v2_export_url(kind)

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return self._extract_json(response)[0]

    def _get_v2_export(self, kind: str, job_id: str) -> Item:
        """
        Returns the status/result of a v2 async export job of `kind` from its job id.
        """
        headers = self.auth.get_auth_headers()
        url = self.get_v2_export_by_job_id_url(kind, job_id)

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return self._extract_json(response)[0]

    def post_export_forecast_parameters(self, data: Item) -> Item:
        """
        Submits an async forecast-parameters export; returns the job (with its job
        id). Poll `get_export_forecast_parameters_by_job_id` for status/results.

        https://docs.api.combocurve.com/api/post-v2-exports-forecast-parameters
        """
        return self._post_v2_export('forecast-parameters', data)

    def get_export_forecast_parameters_by_job_id(self, job_id: str) -> Item:
        """
        Returns the status/result of a forecast-parameters export job.

        https://docs.api.combocurve.com/api/get-v2-exports-forecast-parameters-by-job-id
        """
        return self._get_v2_export('forecast-parameters', job_id)

    def post_export_forecast_volumes(self, data: Item) -> Item:
        """
        Submits an async forecast-volumes export; returns the job (with its job id).
        Poll `get_export_forecast_volumes_by_job_id` for status/results.

        https://docs.api.combocurve.com/api/post-v2-exports-forecast-volumes
        """
        return self._post_v2_export('forecast-volumes', data)

    def get_export_forecast_volumes_by_job_id(self, job_id: str) -> Item:
        """
        Returns the status/result of a forecast-volumes export job.

        https://docs.api.combocurve.com/api/get-v2-exports-forecast-volumes-by-job-id
        """
        return self._get_v2_export('forecast-volumes', job_id)

    def post_export_econ_monthly(self, data: Item) -> Item:
        """
        Submits an async econ-monthly export; returns the job (with its job id).
        Poll `get_export_econ_monthly_by_job_id` for status/results.

        https://docs.api.combocurve.com/api/post-v2-exports-econ-monthly
        """
        return self._post_v2_export('econ-monthly', data)

    def get_export_econ_monthly_by_job_id(self, job_id: str) -> Item:
        """
        Returns the status/result of an econ-monthly export job.

        https://docs.api.combocurve.com/api/get-v2-exports-econ-monthly-by-job-id
        """
        return self._get_v2_export('econ-monthly', job_id)

    def post_export_econ_one_liners(self, data: Item) -> Item:
        """
        Submits an async econ-one-liners export; returns the job (with its job id).
        Poll `get_export_econ_one_liners_by_job_id` for status/results.

        https://docs.api.combocurve.com/api/post-v2-exports-econ-one-liners
        """
        return self._post_v2_export('econ-one-liners', data)

    def get_export_econ_one_liners_by_job_id(self, job_id: str) -> Item:
        """
        Returns the status/result of an econ-one-liners export job.

        https://docs.api.combocurve.com/api/get-v2-exports-econ-one-liners-by-job-id
        """
        return self._get_v2_export('econ-one-liners', job_id)

    def post_export(self, data: Item) -> Item:
        """
        Submits a v1 top-level export request (single-object body, e.g.
        {'exportType': ..., 'expirationHours': ...}); returns the export job.

        https://docs.api.combocurve.com/api/post-exports
        """
        headers = self.auth.get_auth_headers()
        url = self.get_exports_url()

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return self._extract_json(response)[0]
