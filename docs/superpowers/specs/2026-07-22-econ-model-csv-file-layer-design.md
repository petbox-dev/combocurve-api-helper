# Econ-Model model⇄CSV-file Layer — Design (combocurve-api-helper)

**Date:** 2026-07-22
**Status:** Draft for review.

## Problem

The econ-model mappers convert at the **row** level only: `to_csv_rows(model, context) -> list[dict[str, str]]`
and `from_csv_rows(rows) -> dict` (single model). They do **not** produce or consume CSV *text*, and
`from_csv_rows` takes the rows of exactly one model. A real ComboCurve CSV export is a **multi-model file**:
many models of one type stacked, each spanning one or more rows that share a `Model Name`.

So every caller re-writes the same boilerplate to bridge that gap — the `DictWriter`/`writeheader`/`writerows`
block to write, and the `DictReader` + group-by-`Model Name` + per-group `from_csv_rows` block to read
(see README "Econ models to / from CSV"). It is identical every time and easy to get subtly wrong
(fieldnames source, `newline=''`, multi-model grouping).

This layer adds the top-level conversion the API name promises: **model dict ⇄ CSV file**, in one call.

## Goals / Non-goals

**Goals**
- One call each direction, at the whole-file (multi-model) granularity CC actually emits.
- Single implementation of the shared file logic; mappers keep only their type-specific row logic.
- Keep the existing per-type free-function convention (`<base>_to_csv_rows`) for the new entry points.

**Non-goals (explicitly out of scope)**
- No fused fetch+convert and no new API calls — Level A transform sugar only (per the locked scope).
- No `to_json` / `from_json`: a model **is** a JSON-serializable dict; callers use stdlib `json` for `.json` files.
- No econ-model-type auto-detection: the type is fixed by which mapper / function the caller chooses.
- No `DateSettings → Dates` rename — already shipped (`date_settings.py` → `econ_model_type = 'Dates'`).

## Decisions (confirmed with user)

1. **Unit of conversion:** whole multi-model file. `to_csv` takes `list[dict]`; `from_csv` returns `list[dict]`.
   A single model is a length-1 list.
2. **JSON side:** the model dict is the JSON. Surface is CSV-text ⇄ `list[dict]` only.
3. **I/O interface:** string / file-like core, **plus** `read_csv(path)` / `write_csv(path, models)` path convenience.
4. **Shared-logic home:** promote `EconModelMapper` from `Protocol` to a concrete ABC; the four file-level
   methods live there once, implemented in terms of the abstract `columns` / `to_csv_rows` / `from_csv_rows`.
5. **Generated per-type surface:** generate `<base>_to_csv`, `<base>_from_csv`, and `get_<base>_mapper`
   free functions. `read_csv` / `write_csv` are base-class **methods only** (not 22 more free functions).
6. **Empty input:** `to_csv([])` returns a **header-only** string (a valid, importable CC template), never raises.

## Base class

`base.py`: `EconModelMapper` becomes an `abc.ABC`.

- **Abstract (subclass-provided, unchanged):** class attr `econ_model_type: str`, class attr `columns: list[str]`,
  `to_csv_rows(self, model, context=None) -> list[dict[str, str]]`, `from_csv_rows(self, rows) -> dict[str, Any]`.
- **Concrete (implemented once here):**
  - `to_csv(self, models: list[dict[str, Any]], context: Context | None = None) -> str`
  - `from_csv(self, source: str | TextIO) -> list[dict[str, Any]]`
  - `read_csv(self, path: str | os.PathLike[str]) -> list[dict[str, Any]]`
  - `write_csv(self, path: str | os.PathLike[str], models: list[dict[str, Any]], context: Context | None = None) -> None`

Each of the 11 mappers changes only its class header to `class XMapper(EconModelMapper):`. They already
satisfy the abstract members, so no body changes. `MAPPERS: Dict[str, EconModelMapper]` in `registry.py`
stays valid (subtype instances).

## Method behavior

### `to_csv(models, context) -> str`
1. Build a `csv.DictWriter(buf, fieldnames=self.columns)` over an `io.StringIO`.
2. `writeheader()` unconditionally — so an empty `models` list still yields a header-only string.
3. For each model, extend the buffer with `self.to_csv_rows(model, context)`.
4. Return `buf.getvalue()`.

**Context semantics:** one shared `context` applies to the whole file. `common_columns` already falls back
to each model's own `id`/`createdAt` when `context.id`/`context.created_at` are `None`
(`context.id or model.get('id','')`), so a single `context` carrying only `project_name` gives every model
its correct distinct `Model Id`/`Created At` while sharing `Project Name`. Passing `context=None` writes those
three columns blank (they remain in the header; matches current `to_csv_rows` behavior).

`to_csv_rows` already projects each row to exactly `self.columns`, so `DictWriter` cannot raise on extra keys.

### `from_csv(source) -> list[dict]`
1. Resolve text: `text = source.read() if hasattr(source, 'read') else source`.
2. `rows = list(csv.DictReader(io.StringIO(text)))`.
3. If the parsed header has no `Model Name` field, raise `ValueError` (not a CC econ-model export).
4. Group rows by `Model Name`, preserving first-seen order (the logic currently in the test helper
   `group_by_model_name`, promoted into production on the base class).
5. Return `[self.from_csv_rows(group) for group in groups]`.

**Tolerance:** extra columns are ignored and missing optional columns default, because `from_csv_rows`
reads via `row.get(col, default)`. Grouping keys strictly off `Model Name`; `Model Id` is not used (it is
blank in exports without a supplied context). CC forbids duplicate model names within a type, so `Model Name`
is a valid identity key.

### `read_csv(path)` / `write_csv(path, models, context)`
Thin path wrappers owning the file handle: `open(path, ..., encoding='utf-8', newline='')`
(`newline=''` per the `csv` module contract). `read_csv` delegates to `from_csv(handle)`;
`write_csv` writes `to_csv(models, context)`.

## Generated per-type surface

Extend `scripts/generate_csv_functions.py`. For each mapper-backed type it currently emits
`<base>_to_csv_rows` / `<base>_from_csv_rows`; add three more:

```python
def <base>_to_csv(models: List[Dict[str, Any]], context: Optional[Context] = None) -> str:
    """Convert a list of `<EconModelType>` API dicts to a multi-model CSV string."""
    return get_mapper('<EconModelType>').to_csv(models, context)


def <base>_from_csv(source: Union[str, TextIO]) -> List[Dict[str, Any]]:
    """Parse a `<EconModelType>` CSV (string or file-like) into a list of API dicts."""
    return get_mapper('<EconModelType>').from_csv(source)


def get_<base>_mapper() -> EconModelMapper:
    """Return the singleton mapper for `<EconModelType>` (magic-string-free accessor)."""
    return get_mapper('<EconModelType>')
```

`get_<base>_mapper` returns the base `EconModelMapper` type: it programs to the interface (all public
methods live on the base), keeps the generated module's imports minimal (adds only `EconModelMapper` and
`TextIO`/`Union` to the existing imports), and needs no cast. `read_csv`/`write_csv` are reached through it
(`get_capex_mapper().read_csv(path)`) — that is the path-convenience access point, so no per-type
`read_csv`/`write_csv` free functions are generated.

`__all__` grows from 2 to **5 names per mapper** (`_to_csv_rows`, `_from_csv_rows`, `_to_csv`, `_from_csv`,
`get_<base>_mapper`).

## Files touched

- `src/combocurve_api_helper/econ_models/base.py` — Protocol → ABC + 4 concrete methods + grouping helper.
- The 11 mapper modules — one-line class-header change each (inherit `EconModelMapper`).
- `scripts/generate_csv_functions.py` — emit the 3 new functions per type; update `HEADER` docstring.
- `src/combocurve_api_helper/econ_models/_csv_generated.py` — regenerated (checked-in artifact).
- `src/combocurve_api_helper/econ_models/__init__.py` — re-export flows through `_csv_generated.__all__` (already `*`-imported); verify the new names surface.
- `tests/econ_models/test_csv_generated.py` — freshness test unchanged; coverage tests updated: 5 names/mapper,
  `__all__` length `== 5 * len(MAPPERS)`, name-suffix assertions extended, add delegation checks for the new funcs.
- `README.md` — replace the manual `DictWriter`/`DictReader` example with the one-call form.

## Public API — before / after

```python
# before
import csv
mapper = get_mapper("Expenses")
with open("expenses.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=mapper.columns); w.writeheader()
    w.writerows(mapper.to_csv_rows(model))
with open("expenses.csv", newline="") as f:
    rows = list(csv.DictReader(f))
payload = mapper.from_csv_rows(rows)          # only handles ONE model's rows

# after
from combocurve_api_helper.econ_models import expenses_to_csv, expenses_from_csv, get_expenses_mapper
get_expenses_mapper().write_csv("expenses.csv", [model_a, model_b])   # path convenience
models = get_expenses_mapper().read_csv("expenses.csv")              # list[dict], multi-model
csv_text = expenses_to_csv([model_a, model_b])                       # -> str
models2 = expenses_from_csv(csv_text)                                # str or file-like -> list[dict]
```

## Testing

- **Freshness:** existing `test_generated_file_is_current` covers the regenerated file unchanged.
- **Coverage:** update the two `__all__`/`hasattr` tests to the 5-per-mapper shape.
- **Round-trip (file level):** for every fixture in `FIXTURE_FILES`, read the fixture text via `from_csv`
  and assert it equals the per-model `from_csv_rows` results (grouped as the fixtures already are); then
  `to_csv(models)` must re-emit a CSV whose `DictReader` parse equals the original fixture rows
  (byte-identical header + row order).
- **Edge cases:** `to_csv([])` → header-only string that `from_csv` maps back to `[]`;
  `from_csv` accepts both a `str` and a `StringIO`; a header with no `Model Name` raises `ValueError`.

## Risks / edge cases

- **Protocol → ABC** is a structural change. Risk: an external subclass that relied on the Protocol not
  requiring inheritance. Mitigation: internal-only usage; all in-repo mappers migrate in this change.
- **Header-only round trip:** `from_csv` on a header-only file yields `[]` (no `Model Name` values grouped),
  which is correct and symmetric with `to_csv([])`. The no-`Model Name`-column error only fires when the
  `Model Name` *column* is absent, not when it is merely empty of rows.
- **Blank `Model Name`:** a model exported with an empty name groups under `''`. Acceptable — mirrors the
  existing `model_identity`/test-helper behavior; CC exports always carry a name.
