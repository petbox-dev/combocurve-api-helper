# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`combocurve-api-helper` is a typed Python client library that maps ComboCurve's v1 REST API
(`https://api.combocurve.com/v1`) to Python methods. It is published to PyPI; consumers `pip install`
it and drive it through the single `ComboCurveAPI` class. There is no application or service here —
just the library and its type/lint/test tooling.

## CRITICAL: this is a PUBLIC repo — no confidential data

This repository is public. NEVER commit confidential client/project data. This applies
especially to the econ-model test fixtures (`econ_models/fixtures/*.csv`) and to any
"verified live" provenance comments or test dicts:

- **Project names** and **model names** — including well/unit names and ARIES lookup keys —
  must be anonymized to synthetic placeholders (`Sample Project A`, `Sample Well 1`,
  `SAMPLE_*_LOOKUP`, …). Real live model **ObjectIds** likewise (they are not load-bearing —
  any 24-hex value works).
- Before committing a new fixture or a "verified live, project X, model Y" comment, replace
  the specifics with synthetic values. Afterward, grep the tree to confirm no real
  project/model/well names remain (mind line-wrapped names in comments).
- Bare basin/state geology words are fine once the client/project linkage is removed.

## CRITICAL: econ-model names differ by API surface

`assets/econModels.json` exists for exactly one reason: **an econ model is named
DIFFERENTLY on different API surfaces, and the forms do NOT reliably match.**
Each entry maps the forms for one model. When you touch econ-model / assignment /
qualifier / combo code, resolve the correct form from `econModels.json` for the
specific surface — never assume one form works everywhere.

| API surface | Form (`econModels.json` field) | Example |
|---|---|---|
| Scenario `/qualifiers` `econModel`, combo `qualifiers[].assumption`, `assignments/econ-models` grid `model` key | **camelCase** (`qualifier`) | `ownershipReversion`, `fluidModel` |
| Type filter (`get_econ_models_by_type`) | **PascalCase** (`econModelType`) | `OwnershipReversion`, `FluidModel` |
| Econ-model CRUD route **and assignment route `{econName}`** | **kebab** (`route`) | `ownership-reversions`, `fluid-models` |

**The assignment route's `{econName}` is the kebab `route`, NOT the PascalCase
`econModelType`.** The server tolerates PascalCase for most types by coincidental
normalization, but REJECTS it for `FluidModel` (`InvalidEconName: fluidmodel`) —
only the kebab `route` resolves, for all 16 assignable types (verified live; the
data dictionary's "Econ Model Assignment" example also uses the kebab form).
`_get_route_for_assignment` therefore returns `route`, like the CRUD builder.

Single-word models (`capex`, `pricing`) collapse all three forms to one lowercase
string and HIDE the distinction — that is the trap that hides bugs. **`FluidModel`
is the canary: test the multi-word / FluidModel case whenever you touch
assignment/qualifier code.** Diagnosis: a bad `econName` → `InvalidEconName`; a
valid `econName` with a nonexistent id → `EconTypeMismatch` — use that to tell a
name error from an id error.

(Related but separate: **forecast documents** are NOT assignable via the
assignment route — it returns `EconTypeMismatch: not 'forecast'`. Forecast→
qualifier wiring is a CC-UI operation; the grid is read-only.)

## Commands

Run from the repo root:

```bash
mypy src tests scripts                        # type check (primary gate; README also documents `mypy --package combocurve_api_helper`)
ruff check src tests scripts                  # lint (rules in pyproject.toml [tool.ruff.lint])
ruff format --check src tests scripts         # format check (line-length 120, single quotes; drop --check to apply)
pytest                                        # tests (testpaths = tests)
pytest tests/test_keysort.py::test_reverse_flips_the_order   # single test
CC_LIVE_TEST=1 pytest tests/test_api.py       # live read-only tests (needs ~/.combocurve/dev creds)
```

`scripts/test.sh` / `scripts/test.ps1` / `scripts/test.bat` are the canonical pre-commit checks --
all three run ruff (`check` + `format --check`), mypy, then pytest. Per the README contributing flow,
type checking must pass before committing.

**`scripts/` is in the gate on purpose.** It holds the codegen and audit tools, and their *string
literals* emit source that lands in `src/` -- a stale annotation there ships code that cannot run.
This is not hypothetical: `audit_econ_model_drift.py` printed a `_BASELINE_KEYS: Dict[str, ...]`
literal for pasting into `drift.py`, which imports no `Dict` and has no `from __future__ import
annotations`, so pasting raised `NameError`. A repo-wide typing sweep rewrote every real annotation
in that file but could not see inside the string. Keep `scripts/` in all three runners.

`mypy` is `strict = true` in `pyproject.toml`, plus `warn_unreachable`, `warn_no_return`, and
`disallow_any_unimported`. Every function needs full parameter and return annotations. Note
`warn_unreachable` makes defensive `isinstance` guards on typed parameters an error -- the two in
`base.extract_id` / `base.index_of` carry `# type: ignore[unreachable]` and a comment saying they are
runtime guards for untyped callers; keep that form rather than deleting the guard.

`ruff` lints `E/W/F/I/UP/B/SIM/TC/RUF` + `C90` (`SIM108` ignored: at line-length 120 it argues for
115-character ternaries that read worse than the if/else they replace).

## Python floor is 3.9.13 — annotation style follows from it

`requires-python = '>=3.9.13'`. The patch-level floor is **not** arbitrary: `combocurve-api-v1` has
declared `requires-python = >=3.9.13` since its 0.2.5, so that is this package's real floor. Declaring
it makes `pip` fail at install of *this* package rather than part-way through dependency resolution.

What that permits, and what it does not:

- **PEP 585 builtin generics (`dict[str, X]`, `list[X]`) — always fine.** Valid at runtime on 3.9.
  Prefer them; ruff `UP006` enforces it. Import `Sequence`/`Mapping`/`Iterator`/`Callable` from
  `collections.abc`, not `typing` (`UP035`).
- **PEP 604 unions (`X | None`) — only where the annotation is never evaluated**, i.e. in a module
  with `from __future__ import annotations`, or inside a quoted annotation. `X | Y` is 3.10+ at
  runtime. Ruff is target-aware and will not offer the rewrite otherwise, so trust it.
- **Runtime-evaluated positions must keep `Optional` / `Union`**: `TypeAlias` right-hand sides (e.g.
  `JsonValue` in `base.py`), unquoted `cast()` first arguments, and every annotation in a module that
  lacks the future import. The **pydantic econ-model row models keep `Optional` / `Union`** for this
  reason — pydantic re-evaluates string annotations at runtime, so `X | None` breaks there on 3.9 even
  *with* the future import. Match each module's existing spelling, including in prose/docstrings.
- `typing_extensions` is a real dependency: `TypeAlias` is 3.10+ and `Self` is 3.11+.

A `TYPE_CHECKING` block requires `from __future__ import annotations` in the same module, or the
deferred import raises `NameError` when the annotation is evaluated.

## Configuration is read at import time (gotcha)

Importing the package executes `config.py`, which loads two JSON files from `~/.combocurve/`:

- `combocurve.json` — Google service-account credentials (`ServiceAccount`)
- `cc-api.config.json` — `{"apikey": "..."}`

`config.cfg = Configuration.from_file(CC_API_CONFIG_JSON)` runs at module load, so **the package cannot
be imported without these files present**. Example shapes are in `config-examples/`. To point at
different files (e.g. dev creds), construct the client with
`ComboCurveAPI.from_alternate_config(combocurve_json_path, cc_api_config_json_path)` instead of `ComboCurveAPI()`.
`test_api.py` and `test_assignments_live.py` exercise the live API using dev creds under
`~/.combocurve/dev/`; both skip unless `CC_LIVE_TEST=1` and those creds are present, so they do not
run in CI or on machines without dev access. The dev filenames are `combocurve.json` and
**`cc-api.config.json`** — the same names `config.py` uses. Getting that wrong makes the skip predicate
unconditionally true and the live tests silently un-runnable, which is exactly what happened to
`test_api.py` (it looked for `cc_api_config.json`) until 2.1.0. `test_api.py` is read-only;
**`test_assignments_live.py` performs writes** (it creates and deletes a throwaway scenario qualifier).

## Architecture

**Single entrypoint via mixin composition.** `ComboCurveAPI` (`__init__.py`) is an empty class that
multiply-inherits every endpoint group: `Root, Projects, Scenarios, Production, EconRuns, Wells, Models,
CompanyModels, Forecasts, TypeCurves, Directional`. Each of those is a mixin in its own module that
subclasses `APIBase`. Users only ever instantiate `ComboCurveAPI`.

**`base.py` is the HTTP engine.** `APIBase` holds the auth object and all request plumbing. For each verb
there are four parallel methods following one naming scheme:

- `_<verb>_responses_iterator` → yields raw `requests.Response` per page
- `_<verb>_responses` → list of `Response`
- `_<verb>_items_iterator` → yields `ItemList` (JSON parsed to list-of-dicts) per page
- `_<verb>_items` → flattened `ItemList`

GET goes through `_request_items_pages`; POST/PATCH/PUT/DELETE go through `_request_items_pages_chunks`,
which splits `data` into `chunksize` batches (via `more_itertools.chunked`). Pagination is automatic:
both loops follow `get_next_page_url(response.headers)` from the upstream `combocurve-api-v1` package until
exhausted. Auth headers are re-fetched (`self.auth.get_auth_headers()`) before every individual request.

**Type vocabulary** (defined in `base.py`, re-exported from `__init__.py`): `JsonValue` — the recursive
JSON-value union (`str | int | float | bool | Sequence[JsonValue] | Mapping[str, JsonValue] | None`, spelled
with `Union` because the alias is evaluated at runtime; the container arms are the covariant
`Sequence`/`Mapping` so concrete `list[...]`/`dict[...]` payloads type-check despite `list`/`dict`
invariance) — `Item` (= `dict[str, JsonValue]`, one API object), `ItemList` (= `list[Item]`). Endpoint
methods take and return these, not custom model classes — responses stay as plain dicts. Write methods
(POST/PUT/PATCH) return `list[WriteResponse]` (the 207 envelope), not `ItemList`.
(`PrimativeValue`/`IterableValue` were removed in 2.0.0 — they could not express `null`, arrays of objects,
or nested arrays; `JsonValue` subsumes both.)

Because `dict` is **invariant** in its value type, a `dict[str, str]` literal is not an `Item`. Annotate
test/helper literals as `Item` / `ItemList` explicitly rather than letting them infer.

**List ordering goes through `_keysort`, and its correctness argument is easy to break.** Every `get_*`
list method sorts via `APIBase._keysort(items, order)`, where `order` maps key → position. The key is
assembled by **writing** each value to `order[key]`; reading `values[order[key]]` instead applies the
*inverse* permutation. Those two agree only when `order` composed with the payload's own JSON key
sequence is self-inverse — a property of the data, not of `order`. **ComboCurve does not serialize keys
uniformly**: projects/scenarios/forecasts arrive `createdAt, id, name, updatedAt` (self-inverse, so they
were fine), while econ models, type curves and wells lead with `id`, and econ runs arrive
`id, runDate, status` — none self-inverse, so those four groups were silently sorted by `updatedAt` /
`status` until 2.1.0. **Do not reason about this from the bundled docstring examples.** They come from the
Postman collection and disagree with live data for several endpoints — the shipped type-curve example is
`id, name, updatedAt, createdAt` while live is `id, name, createdAt, updatedAt`, which points at a
different sort key. Nor are the examples uniformly alphabetical (wells lead with `dataSource`, productions
with `date`). Verify arrival order against the live API, per endpoint, and re-derive the permutation —
`name` and `wellName` behave identically under live key order, so an argument about one does not transfer
to the other by analogy.
Do not "simplify" `sort_by_key` back to an indexed read. Two more things it does deliberately: it
**mutates the items it sorts**, padding absent ordering keys with `None` (callers have always seen those
fields in returned payloads), and it **validates `order` once per call**, rejecting negative or duplicate
positions — both silently corrupt the key. Gaps are legal and pad as `''`.

The orderings are single-sourced as `base.LIST_SORT_ORDER` and `base.WELL_LIST_SORT_ORDER` (plus small
module-private ones for econ runs, productions, forecast volumes, representative wells). Reuse them; do
not re-inline a literal. `company_models.SORT_ORDER` is a backwards-compatible alias for
`LIST_SORT_ORDER`, kept bound because it is an importable name in a public module.

**Per-endpoint pattern.** Within each module, every endpoint is expressed as a pair: a `*_url(...)` builder
that assembles the path (and appends query string via `_build_params_string`), and the public API method
that calls the builder, sets `params = {'take': GET_LIMIT}`, and dispatches through a `base.py` helper.
Methods that return a single object index `[0]` off the `ItemList`. Each public method's docstring carries
the matching `https://docs.api.combocurve.com/#<anchor>` link — keep this when adding methods.

**Those are TWO query-parameter channels, and `requests` appends rather than merges them.** The `filters`
handed to the url builder are baked into the url string by `_build_params_string`; `params` is passed
separately to `requests` (`take`, plus `concurrency` on the econ-run monthly-export routes). A key present
in both — in practice `take`, which callers legitimately pass as a filter — used to arrive twice (`?take=50&take=200`), and the API rejects the pair outright
(`TypeError: `50,200` is not a valid number`) rather than picking one. `_drop_params_already_in_url`
reconciles them once, in `_request_with_retry`: **the url wins**, so an explicit filter overrides the
method's default page size. Do not re-introduce a second reconciliation point, and do not assume a value
passed in `params` survives — if the url already carries that key, it is dropped. Note the batched-write
path is the one exception that does NOT funnel through `_request_with_retry`: `_send_one_chunk` calls
`requests.request` directly and has its own retry loop. It passes no `params` today, so nothing is wrong —
but a query parameter added there would not be reconciled.
Relatedly, `_build_params_string` percent-encodes and drops `None` values, so callers must NOT pre-encode.
It keeps `,` literal and encodes a space as `%20`, not `+`: three callers join list filters on commas
(`econ_runs` `columns`, `_econ_model_base` `wells`, `scenarios` `econNames`) and those wire formats were
live-verified unencoded. Don't "fix" that back to the `urlencode` default.

**Route paths are hand-written and were wrong FIVE times.** `forecast-monthly-volumes`,
`forecast-daily-volumes`, `wells-identifiers`, `type-curves/{id}/fits/daily` and `.../fits/monthly` all
shipped misspelled through 2.1.0 and 404'd with `{"code": 5, "message": "Method does not exist."}`. Three
were found by hand; the last two only fell out of the mechanical check. `tests/test_route_paths.py` now
resolves each method's `docs.api.combocurve.com/api/<slug>` docstring link to its Postman collection item
and asserts the paired `*_url` builder produces that item's path — run it (network-gated, like
`test_docstring_slugs.py`) rather than eyeballing a new route literal.

**Resource nesting mirrors the REST hierarchy** and is threaded through method arguments:
`projects` → `projects/{project_id}/scenarios` and `projects/{project_id}/forecasts` →
`.../scenarios/{scenario_id}/well-assignments`. So scenario/forecast methods take `project_id`, etc.

**Bundled reference data** lives in `assets/`: `wellHeader.json` populates `APIBase.REFERENCE_WELLHEADER`
and `WELLHEADER_COLUMNS` (lowercased-name → canonical-name map); `econModels.json` populates `ECON_MODELS`.
`package-data` in `pyproject.toml` ships these in the wheel.

**Module sizes / where the bulk is:** `models.py` (~104 methods) and `company_models.py` (~71) dominate —
these build econ-model assumptions. `wells.py` (~30), `production.py` (~24), `scenarios.py` (~22),
`forecasts.py` (~21) follow. `directional.py` and `typecurves.py` are small.

**Econ-model CSV mappers** live in the `econ_models/` subpackage (hand-written, NOT generated — distinct
from the generated CRUD methods below). Each econ-model type has a mapper subclassing the `EconModelMapper`
ABC (`econ_models/base.py`). Row level (one model): `to_row_dicts(model, context=None)` flattens an API model
dict into a list of CSV-column-keyed row dicts, `from_row_dicts(rows)` reconstructs the API payload. File
level (whole multi-model CSV): `to_csv(models, context=None)` / `from_csv(source)` convert to/from CSV text,
`read_csv(path)` / `write_csv(path, models)` to/from a file — all implemented once on the base over the row
methods. Plus a `columns` list (the exact CSV header) and an `econ_model_type`. Look one up with
`get_mapper(econ_model_type)`; `MAPPERS` registers all 11 types (StreamProperties, Differentials,
ProductionTaxes, Expenses, Capex, ReservesCategory, Pricing, Dates, OwnershipReversion, ActualOrForecast,
Risking). `to_row_dicts` keys every row by the full `columns` list, so a CSV round trip is lossless; value
formatting (numbers, dates, enums, escalations)
is centralized in `econ_models/formats.py` with matching `*_to_csv` / `*_from_csv` helpers, and the shared
header is `econ_models/csv_columns.py` `COLUMNS`. **The `get_mapper` / `MAPPERS` key is the PascalCase
`econModelType`** (see the name-forms section above), not the kebab route or camelCase form.

## Adding a new endpoint group

1. Create `src/combocurve_api_helper/<name>.py` with a class subclassing `APIBase` (and `Item`/`ItemList` from `.base`).
2. Import it and add it to the `ComboCurveAPI` base-class list in `__init__.py`.
3. Follow the url-builder + api-method pairing above. Each docstring links to its operation with
   `https://docs.api.combocurve.com/api/<operationId>`; `Example response:` / `Example data:` JSON is
   generated (see Generated content) -- write the description + link, leave example JSON to the generator.

`__version__` is set manually in `__init__.py` and is the source setuptools reads (`pyproject.toml`
`[tool.setuptools.dynamic]`); bump it there when releasing.

## Generated content (do not hand-edit)

Three build-time generators keep source in sync with external sources; each has a freshness test that
fails when the committed output is stale. Run all three at once with `scripts/codegen.sh` (or
`scripts/codegen.ps1`).

**The two generated modules are excluded from the ruff FORMATTER only, not the linter**
(`[tool.ruff.format] exclude`, with `force-exclude = true` so an explicit-path invocation such as a
pre-commit hook or format-on-save cannot reformat them and break the byte comparison). `ruff check`
still covers them, so the generators must emit lint-clean source. **If lint flags a generated file, fix
the template in `scripts/`, never the output** — editing the output makes the freshness test fail.

- **`scripts/generate_model_methods.py`** -> `_models_generated.py`: per-type econ-model CRUD +
  assignment methods expanded from `assets/econModels.json`. Edit the JSON, re-run, commit
  (`tests/test_generated_models.py`).
- **`scripts/generate_csv_functions.py`** -> `econ_models/_csv_generated.py`: the per-type CSV
  convenience functions (`<type>_to_row_dicts` / `<type>_from_row_dicts` row level,
  `<type>_to_csv` / `<type>_from_csv` whole-file, and `get_<type>_mapper`), expanded from
  `assets/econModels.json` + the mapper registry. Re-run after adding a mapper or changing the JSON,
  commit (`tests/econ_models/test_csv_generated.py`).
- **`scripts/generate_docstrings.py`** rewrites the `Example response:` / `Example data:` JSON blocks
  in docstrings -- and the shared module-level `*_response` / `*_data` constants appended via
  `__doc__ +=` -- from the **Postman collection** (a superset of the OpenAPI spec, which is an
  older/less-complete snapshot missing ~52 ops as of 2026-07). The collection's `<type>` placeholders
  are filled with realistic, deterministic spoof values (numbers as numbers, bools as bools, ISO dates,
  ObjectId-like ids) and duplicated array items are collapsed, so a docstring shows the response's
  key/value shape without a live call. Each method maps to its operation via the
  `docs.api.combocurve.com/api/<slug>` link (slug == the collection item name). Shared constants use
  their first (representative) method. Refresh with `python scripts/generate_docstrings.py`; `--check`
  exits 0 (fresh), 1 (stale), or 2 (collection unavailable) (`test_docstrings_current.py`, network-gated).
  (The OpenAPI spec has *real* example values; if it ever catches up on coverage, switching the source
  back would give real instead of spoofed values.)

  **Exit 1 vs 2 is load-bearing** — the freshness test reads 1 as "the docstrings are stale" (failure)
  and 2 as "skip". So *every* failure to obtain a usable collection must raise `CollectionUnavailable`
  and reach exit 2, not escape as a traceback: `OSError` (offline, DNS, TLS — a malformed cert in the
  Windows store breaks `ssl.load_default_certs`), `http.client.HTTPException` (which does **not** derive
  from `OSError` — a truncated `Content-Length` read raises `IncompleteRead`, and this endpoint serves
  `Content-Length`), a non-JSON body, valid JSON that is not an object, and an object with no top-level
  `item` list. That last one is the dangerous case: it yields zero examples, so every marker looks
  "unsourced" and `--check` would exit **0**, passing the test having verified nothing. A bad local
  `--collection PATH` deliberately still raises, so a typo is not mistaken for "offline".
