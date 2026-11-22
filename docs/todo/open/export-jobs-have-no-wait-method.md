# Export jobs have no wait method

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
