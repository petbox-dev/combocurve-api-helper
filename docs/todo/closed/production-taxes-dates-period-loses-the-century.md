# ProductionTaxes `dates` Period loses the century

Closed: 2026-11-03 -- settled by: a raw CC export writes the Period as `MM/YYYY` (`01/1900`,
`01/1976`, `01/2000`, `07/2023`); the mapper now writes and reads that form. `'%b-%y'` was how
Excel displays `MM/YYYY`, so the export behind commit 04a903b had been saved again from Excel.
The old form is still read, with its old rule. All 8,149 live models round-trip their dates.
If this was wrong, you will see: a fixture `dates` row in `fixtures/production_taxes_criteria.csv`
that fails `test_fixtures.py`, or a CC import that refuses a `MM/YYYY` Period.

Severity: medium
Opened: 2026-11-03

## What happens now

`to_row_dicts` writes a `dates` period as `'%b-%y'` (`'2023-07-01'` -> `'Jul-23'`), the form
commit 04a903b verified against a CC export. `from_row_dicts` reads `'Jan-00'` as the
`1900-01-01` sentinel and every other value as 20xx. Two cases come back wrong, without an error:

- A period from 1901 to 1999 comes back 100 years late: `'1976-01-01'` -> `'Jan-76'` -> `'2076-01-01'`.
- A period of `2000-01-01` comes back as `1900-01-01`.

The API -> CSV direction is correct. Only the inverse, and so a CSV written back to CC, is wrong.

## Evidence

A read-only scan of all 8,149 live ProductionTaxes models on 2026-11-03:

- 144 models (548 rows) have a period from 1973 to 1999.
- 79 models (230 rows) start at `2000-01-01`.
- 502 rows start at `1900-01-01`. The old comment said every schedule starts there; most do not
  (`2014-10-01` on 2,762 rows, for example).

## What is still unverified

- How CC itself reads a two-digit year when it imports its own CSV. A POSIX-style pivot
  (69-99 -> 19xx, 00-68 -> 20xx) would fix the 1973-1999 rows and break nothing in the live data,
  but it is a guess about CC.
- Whether CC's export writes `2000-01-01` and `1900-01-01` both as `'Jan-00'`. If it does, the CSV
  cannot tell them apart, and no inverse can be lossless.

## What would unblock it

1. Export from CC one ProductionTaxes model with `dates` periods 1900-01-01, 1976-01-01,
   2000-01-01 and 2023-07-01, and read the Period cells.
2. Import that CSV back into CC and read the dates CC stores.
3. Add the trimmed export as a fixture, then set the inverse to match CC.

## Files

- `src/combocurve_api_helper/econ_models/production_taxes.py`: `_dates_period_to_csv`,
  `_dates_period_from_csv`, `_DATES_START_SENTINEL_*`.
- `tests/econ_models/test_production_taxes.py`: `DATES`, `test_dates_criteria_*`.
