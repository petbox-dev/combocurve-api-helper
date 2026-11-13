# Econ-model unassign sends an empty wells filter

Severity: medium
Opened: 2026-11-13

## What happens now

`delete_econ_model_assignments_by_type_by_id` (`_econ_model_base.py`, and the 16 generated per-type
wrappers in `_models_generated.py`) builds `filters['wells'] = wells if isinstance(wells, str) else
','.join(wells)`. `wells=[]`, `wells=['']` and `wells=''` all give `''`, and `_build_params_string`
drops only `None`, so the request carries `?scenarioId=..&wells=`. `['a', '']` sends `wells=a,`.

3.1.0 added a guard for the same hazard on `delete_scenario_combo` (`combo_ids`) and on
`delete_scenario_lookup_table_assignment_by_id` (`well_ids`): `scenarios._require_id_sequence`
takes the list first, then refuses a bare `str`, an empty sequence and an empty id. This route has no
such guard.

## Unverified

What the server does with a blank `wells=`: refuse it, ignore the filter (unassign every well of the
model in that scenario), or match nothing. Not probed. If it ignores the filter, a caller whose well
lookup came back empty unassigns the model from every well.

## What would unblock it

One dev probe: assign a model to two wells, send `wells=`, read `X-Delete-Count`. Then either apply
the same guard (move `_require_id_sequence` to `base.py` and call it here, keeping the comma join) or
record that the server refuses it.

## Related

`delete_scenario_model_assignments` checks only that `data` is non-empty: a record with
`wellIds: []` or `wellIds: ['']` passes. `delete_scenario_wells(wells: str)` passes `','`.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phase 2 duplication pass.
