# Export jobs have no wait method

Closed: 2026-11-22 -- settled by: live dev exports of all four v2 kinds went `pending`/`running` then `successful` (forecast kinds), `complete` (econ kinds) or `failed`, so `wait_for_export_forecast_parameters`, `_forecast_volumes`, `_econ_monthly` and `_econ_one_liners` are built on the unchanged `_wait_for_job` (default timeout 900 s), with offline tests for finish, failed and timeout
If this was wrong, you will see: a `wait_for_export_*` call returning a job whose `status` is a new in-progress value (e.g. `queued`) before the file exists, or a `TimeoutError` on an export that finishes in the UI

Severity: low
Opened: 2026-11-21

## What happens now

Shapefile and formation jobs have `wait_for_*` methods built on `APIBase._wait_for_job`, which polls until
the status is neither `pending` nor `running`. The v2 export jobs (`exports.py`, `get_export_*_by_job_id`)
have no wait method; callers poll by hand.

## What is unverified

The status values of a v2 export job. `_wait_for_job` assumes `pending`/`running` while working.

## What would unblock it

One live export on dev, recording each status it passes through. If they match, a wait method is one call to
`_wait_for_job` per export kind.

## Files

`src/combocurve_api_helper/exports.py`, `src/combocurve_api_helper/base.py` (`_wait_for_job`)

## Findings 2026-11-22 (live, dev)

One export of each v2 kind was started on the dev test project (forecast kinds limited to one well of a
one-well forecast; econ kinds on a three-well run) and polled every 1.5 to 2 s with its
`get_export_*_by_job_id` method. No file was downloaded.

| Kind | Statuses seen | Good final status | Time to finish |
|---|---|---|---|
| `forecast-parameters` | `running` (from the first poll, 1.4 s) -> `successful` | `successful` | 61 s, 77 s |
| `forecast-volumes` | `running` -> `successful` | `successful` | 77 s |
| `econ-monthly` | `pending` -> `complete` | `complete` | 65 s, 72 s; a repeat export of the same run read `complete` at the first poll (0.3 s) |
| `econ-one-liners` | `pending` -> `complete` | `complete` | 73 s |

- The waiting statuses are `pending` and `running`, the same as `base.RUNNING_JOB_STATUSES`, so
  `_wait_for_job` fits unchanged. The good final status differs by kind: `successful` (forecast kinds),
  `complete` (econ kinds). The failed status is `failed` for every kind.
- Job payload: `status`, `runDate`, `result`. A good `result` has `fileUrls` (one signed Google Cloud
  Storage url per file, `X-Goog-Expires=86400`, so 24 hours), `fileType` (`parquet`), and the ids of the
  job's objects plus `user`. The forecast kinds and econ-monthly name them `project`, `forecast` /
  `scenario`, `run`; econ-one-liners names them `projectId`, `scenarioId`, `runId`.
- Failed shapes: a job id the server does not know answers HTTP 200 with `status: "failed"` (not 404),
  `result: {"user": ..., "error": "Job <id> not found"}` on the econ kinds and `result: {"fileType":
  "parquet"}` on forecast-volumes (also for a job id that is not hex). A forecast-volumes trigger with a
  `wells` id that is not in the forecast is accepted (202) and the job reads `failed` within 3 s, with
  `result` holding only `fileType` and no `error`. A trigger naming a forecast or econ run that is not in
  the project or scenario answers 404 at once (`ForecastNotFoundInProjectError`,
  `RequestValidationError`) and no job is made.
- Other: a forecast-parameters body with `fileType: "csv"` was accepted and wrote `parquet`. One
  econ-monthly trigger answered 500 `InternalServerError`; the next five identical or near-identical
  triggers answered 202.

Done: `wait_for_export_forecast_parameters`, `wait_for_export_forecast_volumes`,
`wait_for_export_econ_monthly`, `wait_for_export_econ_one_liners` (one per kind, matching the per-kind
public methods over the private `_get_v2_export(kind, ...)`), on `_wait_for_job`; default
`timeout_seconds` 900 (the server fails an econ export with no file after 10 minutes, so the wait sees
that instead of timing out) and `poll_seconds` 2. Offline tests in `tests/test_exports.py`.
