# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`combocurve-api-helper` is a typed Python client library that maps ComboCurve's v1 REST API
(`https://api.combocurve.com/v1`) to Python methods. It is published to PyPI; consumers `pip install`
it and drive it through the single `ComboCurveAPI` class. There is no application or service here —
just the library and its type/lint/test tooling.

## Commands

Run from the repo root:

```bash
mypy src                               # type check (primary gate; README also documents `mypy --package combocurve_api_helper`)
flake8 src                             # lint (max-line-length 120, rules in pyproject.toml [tool.flake8])
pytest                                 # tests (testpaths = src)
pytest src/combocurve_api_helper/test_api.py::TestRoot::test_custom_columns   # single test
```

`test/test.sh` / `test/test.bat` are the canonical pre-commit checks: both run flake8 then mypy
(`test.bat` also runs pytest). Per the README contributing flow, type checking must pass before committing.

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
`test_api.py` uses this against `~/.combocurve/dev/`, so the test suite requires live credentials.

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

## Adding a new endpoint group

1. Create `src/combocurve_api_helper/<name>.py` with a class subclassing `APIBase` (and `Item`/`ItemList` from `.base`).
2. Import it and add it to the `ComboCurveAPI` base-class list in `__init__.py`.
3. Follow the url-builder + api-method pairing and the docstring-anchor convention above.

`__version__` is set manually in `__init__.py` and is the source setuptools reads (`pyproject.toml`
`[tool.setuptools.dynamic]`); bump it there when releasing.
