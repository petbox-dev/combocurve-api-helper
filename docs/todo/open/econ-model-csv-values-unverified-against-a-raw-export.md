# Econ-model CSV values not verified against a raw ComboCurve export

Severity: medium
Opened: 2026-09-30

## What happens now

Three CSV behaviours rest on a resaved file or on a statement, not on a raw ComboCurve export, and no
fixture covers them, so the real-export round-trip gate (`tests/econ_models/test_fixtures.py`) cannot
see them:

- **StreamProperties `btu` Value format.** `_btu_rows` writes `num_to_csv` (`'1100'`). Every other
  StreamProperties Value uses `num_to_csv_float` (`'100.0'`), and the `num_to_csv_float` docstring says
  StreamProperties Value always shows `100.0`. One of the two is wrong for `btu` rows.
- **`btu` row omitted at the default.** That a category at 1000 gets no row, per category, is the
  reported behaviour. The one export seen shows only off-default rows.
- **`Model Type = 'company'`.** `Context(scope='company')` writes the literal `company`. No export in
  the repo shows that ComboCurve writes it. `from_row_dicts` drops the scope, so a company export
  read back and written again says `project`.

## Evidence

The 2026-09-06 export behind the `btu` comment looks resaved (unquoted fields, `9/2/2025 20:54` date
form, `0`/`100` where raw exports write `0.0`/`100.0`). It fails the repo's own round-trip gate on its
7 non-`btu` rows, so it cannot settle `'1100'` vs `'1100.0'`. Found by the 2026-09-30 `/code-fix`
NUMERIC audit.

## What would unblock it

A raw (not opened in Excel) ComboCurve StreamProperties CSV export with an off-default and an
at-default `btuContent` category, and one company-scope econ-model export. Add them as trimmed,
anonymised fixtures, then choose the `btu` formatter and decide whether `model_identity` returns
the scope.

## Files

- `src/combocurve_api_helper/econ_models/stream_properties.py`: `_btu_rows`, `_BTU_DEFAULT`
- `src/combocurve_api_helper/econ_models/formats.py`: `num_to_csv_float`, `model_type`
- `src/combocurve_api_helper/econ_models/base.py`: `Context.scope`, `model_identity`
- `tests/econ_models/fixtures/stream_properties.csv`: no `btu` rows
