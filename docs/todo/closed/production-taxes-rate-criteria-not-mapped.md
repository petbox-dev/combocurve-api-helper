# ProductionTaxes rate-based criteria (`oil_rate` and the other phases) are not mapped

Closed: 2026-11-03 -- settled by: `oil_rate`/`gas_rate`/`water_rate`, `offset_to_as_of_date`,
`offset_to_discount_date`, units `dollar_per_month`/`dollar_per_boe` and `null` values mapped;
all 8,149 live models export without an error.
If this was wrong, you will see: `NotImplementedError: Unknown production tax ...` again, or a
`fixtures/production_taxes_criteria.csv` failure in `test_fixtures.py`.

Severity: medium
Opened: 2026-11-03

## Resolution (2026-11-03)

A read-only scan of all 8,149 live ProductionTaxes models (210 projects plus company) answered the
open questions:

- Criteria in live data: `dates` 20,944 rows, `entire_well_life` 16,175, `oil_rate` 6,394,
  `offset_to_fpd` 2,966, `offset_to_as_of_date` 38. No `gas_rate` or `water_rate` in live data;
  the Postman collection lists both, plus `offset_to_discount_date`, `offset_to_end_history` and
  `spud_date_from_headers`.
- `oil_rate` periods are integer thresholds (`[0, 30]`, `[0, 35]`, `[30]`); no rate unit key.
- The scan found more than this item: units `dollar_per_month` (428 models) and `dollar_per_boe`
  (12) raised, `value: [null]` raised `TypeError` (13), offset periods came back as strings, and
  two ad valorem rows merged into one on the inverse (439 models). All are fixed.
- CC's API validator (dev project, 2026-11-03): severance takes `oil_rate` and `gas_rate`;
  **`water_rate` is ad valorem only**. Severance oil/NGL/drip condensate units are `pct_of_revenue`,
  `dollar_per_bbl`, `dollar_per_month`; `dollar_per_boe` was accepted on ad valorem. The API
  refuses `value: [null]` and `rows: []`, so those live models came from elsewhere.
- Three models built in the dev project and exported from CC are the fixture
  `fixtures/production_taxes_criteria.csv`. It confirms `oil rate`, `gas rate`, `water rate`,
  `as of`, `disc date`, `$/month`, `$/boe`, `Ad Val Tax 1`/`Ad Val Tax 2`, and shows
  `offset_to_first_segment` -> `maj seg`, `offset_to_end_history` -> `end hist` (both now mapped).
- The same export showed `dates` Period is `MM/YYYY`: settled
  `production-taxes-dates-period-loses-the-century.md` too.
- `spud_date_from_headers` still raises: no export shows its spelling.
- A scenario export of a live null-value model shows CC writes `null` as `nan`; the mapper does
  too (`fixtures/production_taxes_null_value.csv`).
- `production-taxes-model-with-no-rows-loses-its-state.md` was opened and closed the same day:
  CC's export also drops a model with no rows.

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
