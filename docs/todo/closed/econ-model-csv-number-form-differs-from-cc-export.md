# Econ-model CSV number form (`9` vs `9.0`) differs from CC's export

Closed: 2026-11-03 -- settled by: decision to write every float-valued column in float form.
Each mapper declares `float_columns`; they write `9.0` and read back as `float`
(`tests/econ_models/test_float_columns.py`). The real-export gate compares those columns by
number. Against one project's include-defaults export afterwards: Differentials 32/32 and
StreamProperties 41/41 match as text; ProductionTaxes (131/136) and Expenses (53/53) differ only
where CC wrote an integer form (`3` vs `3.0`).
If this was wrong, you will see: a consumer that compares CSV text with a CC export, or a CC
import that refuses `9.0` in a column CC wrote as `9`.

Severity: low
Opened: 2026-11-03

## What happens now

Each mapper writes a number in one fixed form per column: `num_to_csv` (`9`) or `num_to_csv_float`
(`9.0`). CC's export writes the form of the number as CC stores it. The value is the same; only the
text differs, so a text comparison with a CC export fails and a numeric one passes.

## Evidence

One project, mapper API -> CSV compared with CC's "include defaults" project export, 2026-11-03:

| Type | Models | Match | Differ | Example (CC vs mapper) |
|---|---|---|---|---|
| StreamProperties | 41 | 41 | 0 | |
| ProductionTaxes | 136 | 127 | 9 | Value `9.0` vs `9` |
| Differentials | 32 | 0 | 32 | Value `0.0` vs `0` |
| Expenses | 53 | 0 | 53 | Value `0` vs `0.0`; Paying WI `1` vs `1.0` |

The rows, keys and categories match in all four; only number text differs.

ProductionTaxes Value text against the API value's JSON type (697 values): float -> CC wrote
`str()` of it (522); int -> CC wrote `3` (142); int -> CC wrote **`9.0`** (33). So the API returns
some stored doubles as JSON integers, and the API data cannot tell `9` from `9.0`.

## What was ruled out

A type-preserving rule (JSON int -> `9`, JSON float -> `9.0`) in every mapper: StreamProperties
fell from 41 matches to 0 (CC writes default rows as `0.0`, the API returns `0`), and Expenses
showed differences in other columns too (not traced). Not adopted.

## What is still unverified

- Whether CC writes default rows in one fixed form per type (StreamProperties and Differentials
  `0.0`, Expenses `0`). If so, a per-row rule for default rows could close most of the gap.
- Whether any consumer compares CSV text rather than numbers. If none does, this needs no fix.

## Files

- `src/combocurve_api_helper/econ_models/formats.py`: `num_to_csv`, `num_to_csv_float`
- `src/combocurve_api_helper/econ_models/expenses.py`, `differentials.py`, `production_taxes.py`
