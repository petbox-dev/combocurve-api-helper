# GET well filters on some routes are unverified (repeated keys, cap)

Severity: low
Opened: 2026-11-22

## What happens now

These GET filters are typed `dict[str, str]` and sent as given, so a caller can only pass one id or a
comma-joined string: `get_econ_model_assignments_by_type_by_id` / `count_*` (`wells`, now `QueryFilters` but not
batched), `get_econ_run_onelines` (`well`), `get_*_production_comments` (`well`), `get_forecast_aries`.
`get_scenario_econ_model_assignments` takes no `filters`, although its url builder documents a live-verified
repeated `wellId` filter capped at 100.

The root and path-level volume getters' docstrings ("Accepted keys are ...") omit the collection's repeatable
`phase` key (at most 3; oil, gas and water when omitted), and `phase` is not in
`root._COUNT_COMPARABLE_VOLUME_FILTERS`, so a `phase` filter skips the project count check (unverified whether
the count still matches with `phase`).

## What is unverified

Whether each route takes repeated keys, refuses a comma-joined value (the econ-model unassign DELETE on the
same key does), and caps at 100.

## What would unblock it

A live probe on dev per route (2 ids repeated, 2 ids comma-joined, 100 and 101 ids). Where it behaves like the
DELETE, type the filter `QueryFilters` and read through `_get_items_in_value_batches`.

## Files

`src/combocurve_api_helper/_econ_model_base.py`, `econ_runs.py`, `production_comments.py`, `forecasts.py`,
`scenarios.py`
