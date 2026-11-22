# Write record limits are unknown for most routes

Severity: low
Opened: 2026-11-22

## What happens now

`_post_items`, `_put_items` and `_patch_items` send all of `data` in one request when no `chunksize` is
given. Of the 72 direct write call sites in `src/`, about 15 pass a limit: `wells.py` (8,
`POST_PATCH_PUT_LIMIT`), `typecurves.py` (4), `forecasts.put_forecast_parameters` (caller-supplied) and,
since 2026-11-22, `production_comments.py`. `production.py` batches only in its `_request_batched` methods.
The rest send every record at once.

## Evidence

The production-comment POST answers 400 `RecordCountError` ("Too many records in a single request. Please
split your data in batches of at most 200 records") for 201 records on POST, PUT and PATCH (dev, 2026-11-22). Until then the
helper sent any number of comments in one request. `company_models.py` defines `POST_LIMIT` and
`PUT_LIMIT = 500` but no call passes them.

## Blast radius

A caller writing more records than a route accepts gets a 400 for the whole call instead of batched
requests. Nothing is written, so no data is lost; the caller must split `data` themselves.

## What would unblock it

Probe each write route on dev with N+1 fixture records (the error names the limit), record the limit as a
module constant, and pass it as `chunksize`. Start with the routes callers write in bulk: econ models,
production (the direct calls), forecast volumes and projects. A split write can leave earlier batches
applied when a later one raises (`APIBase._require_at_most` explains why the assignment routes refuse
instead); decide per route.

## Files

`src/combocurve_api_helper/base.py` (`_post_items`, `_put_items`, `_patch_items`), every module with a
write method; `src/combocurve_api_helper/company_models.py` (`POST_LIMIT`, `PUT_LIMIT` unused).
