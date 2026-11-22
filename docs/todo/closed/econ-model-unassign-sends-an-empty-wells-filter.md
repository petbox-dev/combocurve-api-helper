# Econ-model unassign sends an empty wells filter

Closed: 2026-11-21 -- settled by: blank and empty ids refused locally (`APIBase._split_ids`, `_require_assignment_wells`); a live probe showed a blank `wells=` is a server 400 and a comma-joined `wells` of two or more ids is also a 400, so the unassign and `delete_scenario_wells` now send one `wells` key per id
If this was wrong, you will see: a live unassign of two or more wells failing with 400 "is not a valid ObjectId", or `X-Delete-Count` lower than the number of wells sent

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

## Resolution (2026-11-21)

Probed live on dev (throwaway `API Helper Fixture probe` dates qualifier, the dates model assigned to
two wells, cleaned up; nothing of that name is left):

- `wells=` (blank) -> 400 `RequestStructureError`, `` `` is not a valid ObjectId``, location
  `wells[0]`; nothing deleted. The server refuses it, so the feared "unassign every well" does not occur.
- `wells=a,b` (comma-joined) -> 400 `` `a,b` is not a valid ObjectId``. The form this method sent for
  two or more wells never worked.
- `wells=a&wells=b` (repeated key) -> 204, `X-Delete-Count: 2`.

Fixed: `delete_econ_model_assignments_by_type_by_id` (and the 16 generated wrappers, which delegate)
refuse an empty sequence, an empty id, `''` and a `str` with an empty element after splitting on `,`,
before any request (`scenarios._split_ids`, which reuses `APIBase._require_id_sequence`); they send one
repeated `wells` key per id. A `str` is still accepted and split on `,`.
`delete_scenario_model_assignments` refuses a record without `allWells: true` whose `wellIds` is absent,
empty, a `str` or holds an empty id. `delete_scenario_wells` refuses `','`-style input (its
comma-joined wire form is not verified live).
