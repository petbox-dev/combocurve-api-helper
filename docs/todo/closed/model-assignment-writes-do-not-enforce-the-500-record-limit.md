# Model-assignment writes do not enforce the 500-record limit

Closed: 2026-11-21 -- settled by: `APIBase._require_at_most` enforces 500 records on the model-assignment PUT/DELETE (and the econ-model and lookup-table assignment writes), plus the 25,000-`wellIds` cap, before any request
If this was wrong, you will see: a 400 from the server instead of a local `ValueError` on 501 records, or a valid batch of 500 or fewer refused locally

Severity: low
Opened: 2026-11-13

## What happens now

The Postman collection documents a maximum of 500 records for four scenario assignment routes. 3.1.0
enforces it on two of them, before any request:

| Route | Method | Limit enforced |
|---|---|---|
| PUT lookup-table assignments | `put_scenario_lookup_table_assignments` | yes (`MAX_LOOKUP_TABLE_ASSIGNMENT_RECORDS`) |
| DELETE lookup-table assignment | `delete_scenario_lookup_table_assignment_by_id` | yes (`MAX_LOOKUP_TABLE_UNASSIGN_WELLS`) |
| PUT model assignments | `put_scenario_model_assignments` | no |
| DELETE model assignments | `delete_scenario_model_assignments` | no |

Without the check, 501 records go as one request, and the caller gets the server's 400 instead of a
`ValueError` that names the limit.

## Decision for the fix

Refuse, do not split. The model-assignment DELETE is all-or-nothing on the server; a split write
would leave earlier batches applied when a later one fails, and `_put_items` / `_delete_responses`
return nothing that says how many were sent (the reason 3.1.0 refuses rather than splits the
lookup-table PUT).

`get_scenario_model_assignments` documents `wellId` "up to 100 values"; that is also not checked.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phase 2 duplication pass.

## Resolution (2026-11-21)

`put_scenario_model_assignments` and `delete_scenario_model_assignments` refuse more than 500 records
with `ValueError` before any request, through one helper (`APIBase._require_at_most`) that all six
scenario limit checks now share, with the existing messages. Both assignment PUTs (model and econ-model)
also refuse more than 25,000 `wellIds` summed across the records (documented). The `wellId` "up to 100
values" on `get_scenario_model_assignments` was already handled by batching (`_filter_value_batches`);
`get_scenario_well_incrementals` now batches the same way.
