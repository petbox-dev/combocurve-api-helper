# ProductionTaxes rate-based criteria (`oil_rate` and the other phases) are not mapped

Severity: medium
Opened: 2026-11-03

## What happens now

`ProductionTaxes.to_row_dicts` raises on any API `criteria` outside `_CRITERIA_TO_CSV`
(`entire_well_life`, `offset_to_fpd`, `dates`). A project with one production-taxes model that uses
a rate-threshold criteria stops the whole export:

```
File ".../combocurve_api_helper/econ_models/production_taxes.py", line 202, in to_row_dicts
    raise NotImplementedError(f'Unknown production tax criteria: {row.criteria}')
NotImplementedError: Unknown production tax criteria: oil_rate
```

`from_row_dicts` has the same gap on the inverse (`_CRITERIA_FROM_CSV`, line 126).

## Evidence

- A nightly downstream consumer (an Airflow DAG that exports every project's ProductionTaxes) has
  failed with the error above on every run from 2026-10-27 to 2026-11-03. The last success was
  2026-10-26, so a model with `criteria == 'oil_rate'` first appeared in one project on or about
  that date. The exception also stops the loop, so later projects in the same run are not exported.
- Installed version: 2.5.0, the latest published.

## Scope: test every phase, not only oil

The fix must cover, and the tests must exercise, the rate criteria for **every phase** CC accepts
on a production-taxes row, not only `oil_rate`. Add one fixture per phase to
`tests/econ_models/` and round-trip each through `to_row_dicts` -> `from_row_dicts`.

## What is still unverified

- The full list of rate criteria names. Only `oil_rate` is observed. `gas_rate`, `water_rate` and
  any combined or fluid rate are assumptions; take the real list from the API schema or the CC UI.
- The `period` values for a rate criteria (threshold numbers, units, whether the first element is
  0 or a sentinel), and the CSV `Criteria` and `Period` spelling CC's own export uses for them.
- Whether the rate rows carry other keys (a rate unit, for example) that the model does not hold.

## What would unblock it

1. `GET` the affected ProductionTaxes model from the API and save the raw `rows` payload.
2. Download CC's CSV export of the same model for the `Criteria` and `Period` spelling.
3. Build one model per phase in a scratch project, export each, and add trimmed, anonymised
   fixtures before changing `_CRITERIA_TO_CSV`.

## Files

- `src/combocurve_api_helper/econ_models/production_taxes.py`: `_CRITERIA_TO_CSV`,
  `_CRITERIA_FROM_CSV`, `to_row_dicts` (period handling, line 205), `from_row_dicts`.
- `tests/econ_models/`: round-trip fixtures.
