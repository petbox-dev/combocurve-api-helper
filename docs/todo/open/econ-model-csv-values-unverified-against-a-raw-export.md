# Econ-model CSV values not verified against a raw ComboCurve export

Severity: low
Opened: 2026-09-30

## What happens now

Two CSV behaviours rest on a statement, not on a raw ComboCurve export, so the real-export
round-trip gate (`tests/econ_models/test_fixtures.py`) cannot see them:

- **One `btu` category at the default, the other not.** `_btu_rows` drops a category equal to 1000
  and writes the other. No export shows that mix.
- **`Model Type = 'company'`.** `Context(scope='company')` writes the literal `company`. No export
  in the repo or in the 2026-09 downloads has a `company` row (every model is `project`).
  `from_row_dicts` drops the scope, so a company export read back and written again says `project`.

## Settled 2026-09-30

A raw export dated 2026-09-06 (every field quoted) writes `btu` Value as `'1100.0'` / `'900.0'`,
the `num_to_csv_float` form. `_btu_rows` wrote `'1100'` and was corrected; the two rows are now in
`fixtures/stream_properties.csv`, so the gate covers the format. The same export has no `btu` row
for any of its 149 other models, so a model with both categories at the default gets none.
A resaved copy of that export (unquoted, `1100`) had misled the first reading.

## What would unblock it

A raw ComboCurve export of a StreamProperties model with exactly one `btuContent` category off the
default, and a raw export of a company-scope econ model. Add them as trimmed, anonymised fixtures,
then decide whether `model_identity` returns the scope.

## Files

- `src/combocurve_api_helper/econ_models/stream_properties.py`: `_btu_rows`, `_BTU_DEFAULT`
- `src/combocurve_api_helper/econ_models/formats.py`: `model_type`
- `src/combocurve_api_helper/econ_models/base.py`: `Context.scope`, `model_identity`
