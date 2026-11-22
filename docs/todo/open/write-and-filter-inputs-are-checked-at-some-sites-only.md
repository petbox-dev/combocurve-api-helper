# Write and filter inputs are checked at some sites only

Severity: low
Opened: 2026-11-22

## What happens now

Pre-existing gaps found by the code-fix run on the missing-api-routes branch (2026-11-22):

- An empty `data` list is refused (`_require_records` / `_records_from`) at about 16 write sites; about 55
  other POST/PUT/PATCH methods (wells, production, forecasts, scenarios, type curves, econ models) pass `[]`
  to the transport, which then sends the request with no body.
- `_require_any_filter` treats a whitespace-only id as a value, so `delete_scenarios(id='  ')`,
  `delete_type_curves(id='  ')`, the wells deletes and `delete_*_productions(well_id='  ')` send it, while
  `_require_id_sequence` and `_split_ids` refuse it.
- `_require_assignment_delete` checks the wells of each record but not `model` / `qualifierName`.
- A single dict passed to `post_directional_surveys_batch` (typed `ItemList`) is sent as its key names.

- `_request_items_pages_chunks` with an explicit `chunksize=0` and non-empty `data` sends a body-less request
  (`_request_batched` refuses a `chunksize` below 1 since 2026-11-22).
- `typecurves._request_one_item` and `APIBase._send_for_item` are two single-object helpers; both now return
  `{}` for an empty success body, but they differ on a list body.

## What is unverified

Whether the server reads a body-less write, a blank id or a blank qualifier as unfiltered.

## What would unblock it

Move the empty-`data` refusal into `_request_items_pages_chunks` for non-DELETE methods (with an explicit
body-less POST for `econ_runs.post_econ_run_monthly_export`), and use one blank-id predicate in
`_require_any_filter`, `production._delete_filters`, `_require_id_sequence` and `_split_ids`.

## Files

`src/combocurve_api_helper/base.py`, `production.py`, `wells.py`, `scenarios.py`, `typecurves.py`,
`directional.py`
