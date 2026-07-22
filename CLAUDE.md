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
mypy src tests                         # type check (primary gate; README also documents `mypy --package combocurve_api_helper`)
ruff check src tests                   # lint (rules in pyproject.toml [tool.ruff.lint])
ruff format --check src tests          # format check (line-length 120, single quotes; drop --check to apply)
pytest                                 # tests (testpaths = tests)
pytest tests/test_api.py::TestRoot::test_custom_columns   # single test
```

`scripts/test.sh` / `scripts/test.ps1` / `scripts/test.bat` are the canonical pre-commit checks --
all three run ruff (`check` + `format --check`), mypy, then pytest over `src` + `tests`. Per the
README contributing flow, type checking must pass before committing.

`mypy` is configured strict-ish in `pyproject.toml` (`disallow_untyped_defs`, `disallow_any_generics`,
`disallow_incomplete_defs`, etc.). Every method needs full parameter and return annotations.

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
run in CI or on machines without dev access.

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

**Type vocabulary** (defined in `base.py`, re-exported from `__init__.py`): `PrimativeValue` (str/int/float/bool),
`IterableValue`, `Item` (= `Dict[str, ...]`, one API object), `ItemList` (= `List[Item]`). Endpoint methods
take and return these, not custom model classes — responses stay as plain dicts.

**Per-endpoint pattern.** Within each module, every endpoint is expressed as a pair: a `*_url(...)` builder
that assembles the path (and appends query string via `_build_params_string`), and the public API method
that calls the builder, sets `params = {'take': GET_LIMIT}`, and dispatches through a `base.py` helper.
Methods that return a single object index `[0]` off the `ItemList`. Each public method's docstring carries
the matching `https://docs.api.combocurve.com/#<anchor>` link — keep this when adding methods.

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
  exits 1 (stale) or 2 (collection unreachable) (`test_docstrings_current.py`, network-gated). (The
  OpenAPI spec has *real* example values; if it ever catches up on coverage, switching the source back
  would give real instead of spoofed values.)
