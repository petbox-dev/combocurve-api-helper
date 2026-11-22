from .base import APIBase, Item

# The async export routes live under /v2 (every other route in this package is /v1);
# their URLs use `APIBase.API_BASE_URL_V2`.
#
# Job statuses, seen live on dev 2026-11-22: the forecast kinds read `running` from the first poll, then
# `successful`; the econ kinds go `pending` -> `complete`. Both waiting statuses are
# `base.RUNNING_JOB_STATUSES`, so the `wait_for_export_*` methods use `APIBase._wait_for_job`. A failed
# export, and a job id the server does not know, read as `failed` (HTTP 200, not 404).

# Longer than the 10 minutes after which the server marks an econ export that has written no file as
# `failed` (the collection's description), so a wait sees that `failed` rather than timing out first.
EXPORT_WAIT_TIMEOUT_SECONDS = 900.0
EXPORT_POLL_SECONDS = 2.0


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
        return self._send_for_item('post', self.get_v2_export_url(kind), data)

    def _get_v2_export(self, kind: str, job_id: str) -> Item:
        """
        Returns the status/result of a v2 async export job of `kind` from its job id.
        """
        return self._send_for_item('get', self.get_v2_export_by_job_id_url(kind, job_id))

    def _wait_for_v2_export(self, kind: str, job_id: str, timeout_seconds: float, poll_seconds: float) -> Item:
        """
        Polls a v2 export job of `kind` until its status is no longer `pending` or `running`; returns the
        last job read.
        """
        return self._wait_for_job(
            lambda: self._get_v2_export(kind, job_id), timeout_seconds, poll_seconds, f'{kind} export job {job_id}'
        )

    def post_export_forecast_parameters(self, data: Item) -> Item:
        """
        Starts an async export of a forecast's segment parameters to a file and returns `{"jobId": ...}`;
        wait for it with `wait_for_export_forecast_parameters`, or poll
        `get_export_forecast_parameters_by_job_id`. `data` takes `projectId`, `forecastId`, and optional
        `fileType`, `phases` (per-phase `startDate`), `adjustParameters` and `options` (`series`,
        `wells`); `options.wells` limits the export to those wells. A body with `fileType: "csv"` was
        accepted and still wrote a `parquet` file (live 2026-11-22).

        The trigger answers 202 with `{"jobId": ...}` only. At most 5 triggers per 60 seconds per export
        kind and tenant (the collection's description); a 429 is retried by the transport. A trigger that
        names a forecast or an econ run that is not in the project or scenario answers 404 at once, and
        no job is made (live 2026-11-22). No docs link: the collection names this operation with spaces, which
        no `/api/<slug>` link can carry.
        """
        return self._post_v2_export('forecast-parameters', data)

    def get_export_forecast_parameters_by_job_id(self, job_id: str) -> Item:
        """
        Returns a forecast-parameters export job: `status`, `runDate` and `result`. Seen live
        (2026-11-22): `running` from the first poll, then `successful` about 60 to 80 seconds after the
        trigger for one well. A `successful` job's `result` has `fileUrls` (one signed download url per
        file, valid for 24 hours: `X-Goog-Expires=86400`), `fileType`, `project`, `forecast` and `user`.
        A failed job, and a job id the server does not know, read as `status: "failed"` with HTTP 200;
        the `result` may carry an `error` message. Wait with `wait_for_export_forecast_parameters`.
        """
        return self._get_v2_export('forecast-parameters', job_id)

    def wait_for_export_forecast_parameters(
        self,
        job_id: str,
        timeout_seconds: float = EXPORT_WAIT_TIMEOUT_SECONDS,
        poll_seconds: float = EXPORT_POLL_SECONDS,
    ) -> Item:
        """
        Polls `get_export_forecast_parameters_by_job_id` every `poll_seconds` until the job is no longer
        `pending` or `running`, and returns it; check its `status`: `successful` for a good export (the
        file urls are in `result.fileUrls`), `failed` otherwise. Raises `TimeoutError` when it has not
        finished within `timeout_seconds`. An export of one well took about 60 to 80 seconds (live
        2026-11-22). Not an API route: it calls the job route repeatedly.
        """
        return self._wait_for_v2_export('forecast-parameters', job_id, timeout_seconds, poll_seconds)

    def post_export_forecast_volumes(self, data: Item) -> Item:
        """
        Starts an async export of forecast (and optionally production) volumes to a file and returns
        `{"jobId": ...}`; wait for it with `wait_for_export_forecast_volumes`, or poll
        `get_export_forecast_volumes_by_job_id`. `data` takes `projectId`, `forecastId`, and optional
        `phases`, `wells`, `fileType`, `mergeForecastAndProduction`, and `forecast` / `production`
        windows (`resolution`, `start`, `end`). Besides the trigger rate limit, the collection states a
        cap of 10 forecast-volume exports queued or running per tenant (429 beyond it). A `wells` id
        that is not in the forecast is accepted at the trigger; the job then reads `failed` within
        seconds, with no `error` message (live 2026-11-22).

        The trigger answers 202 with `{"jobId": ...}` only. At most 5 triggers per 60 seconds per export
        kind and tenant (the collection's description); a 429 is retried by the transport. A trigger that
        names a forecast or an econ run that is not in the project or scenario answers 404 at once, and
        no job is made (live 2026-11-22). No docs link: the collection names this operation with spaces, which
        no `/api/<slug>` link can carry.
        """
        return self._post_v2_export('forecast-volumes', data)

    def get_export_forecast_volumes_by_job_id(self, job_id: str) -> Item:
        """
        Returns a forecast-volumes export job: `status`, `runDate` and `result`. Seen live (2026-11-22):
        `running` from the first poll, then `successful` about 60 to 80 seconds after the trigger for one
        well and one year of monthly volumes. A `successful` job's `result` has `fileUrls` (one signed
        download url per file, valid for 24 hours), `fileType`, `project`, `forecast` and `user`. A
        failed job, and a job id the server does not know, read as `status: "failed"` with HTTP 200; a
        failed forecast-volumes job's `result` held only `fileType`. Wait with
        `wait_for_export_forecast_volumes`.
        """
        return self._get_v2_export('forecast-volumes', job_id)

    def wait_for_export_forecast_volumes(
        self,
        job_id: str,
        timeout_seconds: float = EXPORT_WAIT_TIMEOUT_SECONDS,
        poll_seconds: float = EXPORT_POLL_SECONDS,
    ) -> Item:
        """
        Polls `get_export_forecast_volumes_by_job_id` every `poll_seconds` until the job is no longer
        `pending` or `running`, and returns it; check its `status`: `successful` for a good export (the
        file urls are in `result.fileUrls`), `failed` otherwise. Raises `TimeoutError` when it has not
        finished within `timeout_seconds`. An export of one well took about 60 to 80 seconds (live
        2026-11-22). Not an API route: it calls the job route repeatedly.
        """
        return self._wait_for_v2_export('forecast-volumes', job_id, timeout_seconds, poll_seconds)

    def post_export_econ_monthly(self, data: Item) -> Item:
        """
        Starts an async export of an econ run's monthly results to a file and returns `{"jobId": ...}`;
        wait for it with `wait_for_export_econ_monthly`, or poll `get_export_econ_monthly_by_job_id`.
        `data` takes `projectId`, `scenarioId`, `runId`, and optional `fileType` and `timeZone`; the
        export covers the whole run (the body has no well filter). One trigger answered a 500 that did
        not repeat on the next tries (live 2026-11-22); a POST is not sent again, so that 500 is raised.

        The trigger answers 202 with `{"jobId": ...}` only. At most 5 triggers per 60 seconds per export
        kind and tenant (the collection's description); a 429 is retried by the transport. A trigger that
        names a forecast or an econ run that is not in the project or scenario answers 404 at once, and
        no job is made (live 2026-11-22). No docs link: the collection names this operation with spaces, which
        no `/api/<slug>` link can carry.
        """
        return self._post_v2_export('econ-monthly', data)

    def get_export_econ_monthly_by_job_id(self, job_id: str) -> Item:
        """
        Returns an econ-monthly export job: `status`, `runDate` and `result`. Seen live (2026-11-22):
        `pending`, then `complete` (not `successful`, as the forecast kinds) about 65 to 75 seconds after
        the first trigger for a small run; a second export of the same run read `complete` at the first
        poll. A `complete` job's `result` has `fileUrls` (one signed download url per file, valid for 24
        hours), `fileType`, `project`, `scenario`, `run` and `user`. The server marks a job that writes no
        file within 10 minutes `failed` (the collection's description). A job id the server does not know
        reads as `status: "failed"` with HTTP 200 and `result.error` `"Job <id> not found"`. Wait with
        `wait_for_export_econ_monthly`.
        """
        return self._get_v2_export('econ-monthly', job_id)

    def wait_for_export_econ_monthly(
        self,
        job_id: str,
        timeout_seconds: float = EXPORT_WAIT_TIMEOUT_SECONDS,
        poll_seconds: float = EXPORT_POLL_SECONDS,
    ) -> Item:
        """
        Polls `get_export_econ_monthly_by_job_id` every `poll_seconds` until the job is no longer
        `pending` or `running`, and returns it; check its `status`: `complete` for a good export (the file
        urls are in `result.fileUrls`), `failed` otherwise. Raises `TimeoutError` when it has not finished
        within `timeout_seconds`; the default (900) outlasts the server's 10-minute limit, so a stuck
        export comes back `failed` rather than as a timeout. A small run took about 65 to 75 seconds
        (live 2026-11-22). Not an API route: it calls the job route repeatedly.
        """
        return self._wait_for_v2_export('econ-monthly', job_id, timeout_seconds, poll_seconds)

    def post_export_econ_one_liners(self, data: Item) -> Item:
        """
        Starts an async export of an econ run's one-liners to a file and returns `{"jobId": ...}`; wait
        for it with `wait_for_export_econ_one_liners`, or poll `get_export_econ_one_liners_by_job_id`.
        `data` takes `projectId`, `scenarioId`, `runId`, and optional `fileType` and `timeZone`; the
        export covers the whole run (the body has no well filter).

        The trigger answers 202 with `{"jobId": ...}` only. At most 5 triggers per 60 seconds per export
        kind and tenant (the collection's description); a 429 is retried by the transport. A trigger that
        names a forecast or an econ run that is not in the project or scenario answers 404 at once, and
        no job is made (live 2026-11-22). No docs link: the collection names this operation with spaces, which
        no `/api/<slug>` link can carry.
        """
        return self._post_v2_export('econ-one-liners', data)

    def get_export_econ_one_liners_by_job_id(self, job_id: str) -> Item:
        """
        Returns an econ-one-liners export job: `status`, `runDate` and `result`. Seen live (2026-11-22):
        `pending`, then `complete` (not `successful`, as the forecast kinds) about 70 seconds after the
        trigger for a small run. A `complete` job's `result` has `fileUrls` (one signed download url per
        file, valid for 24 hours), `fileType`, `projectId`, `scenarioId`, `runId` and `user` (the econ
        monthly job names these `project`, `scenario`, `run`). The server marks a job that writes no file
        within 10 minutes `failed` (the collection's description). A job id the server does not know
        reads as `status: "failed"` with HTTP 200 and `result.error` `"Job <id> not found"`. Wait with
        `wait_for_export_econ_one_liners`.
        """
        return self._get_v2_export('econ-one-liners', job_id)

    def wait_for_export_econ_one_liners(
        self,
        job_id: str,
        timeout_seconds: float = EXPORT_WAIT_TIMEOUT_SECONDS,
        poll_seconds: float = EXPORT_POLL_SECONDS,
    ) -> Item:
        """
        Polls `get_export_econ_one_liners_by_job_id` every `poll_seconds` until the job is no longer
        `pending` or `running`, and returns it; check its `status`: `complete` for a good export (the file
        urls are in `result.fileUrls`), `failed` otherwise. Raises `TimeoutError` when it has not finished
        within `timeout_seconds`; the default (900) outlasts the server's 10-minute limit, so a stuck
        export comes back `failed` rather than as a timeout. A small run took about 70 seconds (live
        2026-11-22). Not an API route: it calls the job route repeatedly.
        """
        return self._wait_for_v2_export('econ-one-liners', job_id, timeout_seconds, poll_seconds)

    def post_export(self, data: Item) -> Item:
        """
        Submits a v1 top-level export request (single-object body, e.g.
        {'exportType': ..., 'expirationHours': ...}); returns the export job.

        https://docs.api.combocurve.com/api/post-exports

        Example data:
        {
            "exportType": "monthlyCombinedVolumeExport",
            "expirationHours": 24
        }

        Example response:
        {
            "exportType": "string",
            "fileType": "string",
            "fileUrls": [
                "string"
            ]
        }
        """
        return self._send_for_item('post', self.get_exports_url(), data)
