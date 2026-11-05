# A ProductionTaxes model with no rows loses its state

Closed: 2026-11-03 -- settled by: CC's own project export also writes no line for a model with
no rows (a raw 2026-11-03 export of a 716-model project left out its one non-unique zero-row
model, and every other non-unique model was in it). The mapper matches CC; no change.
If this was wrong, you will see: a CC export with a line (blank Key/Category/Value) for a model
whose API `rows` is empty.

Severity: low
Opened: 2026-11-03

## What happens now

`ProductionTaxesMapper.to_row_dicts` writes one CSV row per period of each API row. A model with
`data.rows == []` gives no CSV rows, so:

- `from_row_dicts` on that empty list returns `state: ''` (the state is read from the rows), not
  the model's `state` (`'custom'` in every live case).
- At file level (`to_csv`), the model writes no line at all, so it is not in the CSV.

## Evidence

A read-only scan of all 8,149 live ProductionTaxes models on 2026-11-03: 135 have zero rows,
all with `state: 'custom'`. These are the only `state` differences in a full API -> CSV -> API
round trip.

## What is still unverified

- What CC's own CSV export writes for a model with no rows: no line, or one line with blank
  Key/Category/Value. Only that tells whether the mapper should write a line.
- Whether the other mappers drop an empty model the same way. Not checked.

## What would unblock it

Export from CC one ProductionTaxes model with no rows. If the export has a line for it, add the
trimmed export as a fixture and write the same line.

## Files

- `src/combocurve_api_helper/econ_models/production_taxes.py`: `to_row_dicts`, `from_row_dicts`.
