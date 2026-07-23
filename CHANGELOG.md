# Changelog

All notable changes to `combocurve-api-helper` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-23

Type-precision release. Runtime behavior is unchanged throughout (same dicts flow
through); every change below is to the static types, but two of them remove/alter
public type names, so this is a major bump.

### Changed (breaking — types only)

- **`PrimativeValue` and `IterableValue` are removed; `JsonValue` replaces them.**
  The old aliases could not model real API payloads: `IterableValue` allowed only lists
  of scalars (no arrays of objects, no nested arrays) and nothing could be `null`, so a
  dict containing `None`, a `rows: [{…}]` array, or a nested list was not a valid `Item`.
  `Item` is now `Dict[str, JsonValue]` where `JsonValue` is the full recursive JSON union:
  `None | str | int | float | bool | Sequence[JsonValue] | Mapping[str, JsonValue]`. The
  container arms are the **covariant** `Sequence` / `Mapping` (not `List` / `Dict`) so that
  a concrete `list[str]` / `list[dict[…]]` payload — or a `list[str]` variable assigned into
  an item — type-checks despite `List` / `Dict` invariance. `JsonValue` is re-exported from
  the package root; `PrimativeValue` / `IterableValue` imports must be dropped (they had no
  valid replacement in the old model — use `JsonValue`, or `str | int | float | bool` for a
  scalar). `Item` / `ItemList` keep their names and their mutable `Dict` / `List` spelling.
- **Write methods return `List[WriteResponse]`** instead of the generic `ItemList`.
  `WriteResponse` is a TypedDict for the 207 create/update envelope: `successCount` /
  `failedCount` (ints), `generalErrors` (`List[WriteError]`), and `results` — kept as the
  generic `ItemList` because the per-record shape varies by resource (id key is
  `id`/`forecastId`/`wellId`/…, productions add `date`/`well`, etc.), so a rigid per-record
  TypedDict would force casts to read a resource's own fields. Applied to all POST/PUT/PATCH
  methods (hand-written + the `generate_model_methods.py` template for the generated ones);
  `WriteResponse` / `WriteError` are re-exported from the package root. GET-list methods keep
  `ItemList`; the generic `_post_items` / `_put_items` / `_patch_items` dispatchers keep
  `ItemList` (POST isn't always a write envelope, e.g. `post_econ_run_monthly_export`), so
  each write method casts at its boundary.
- Package-root re-exports of `Item` / `ItemList` / `JsonValue` / `WriteResponse` / `WriteError`
  now use the explicit `from .base import X as X` form so downstream `mypy --strict`
  (`--no-implicit-reexport`) sees them as exported (previously only `_batch`'s exports did).

## [1.4.0] - 2026-07-23

### Added

- **Broader REST route coverage.** Wrappers for previously-unwrapped routes:
  - **v2 async exports** (`exports.py`): `post_export_*` / `get_export_*_by_job_id` for
    `forecast-parameters`, `forecast-volumes`, `econ-monthly`, `econ-one-liners` (submit +
    poll, mirroring `post_forecast_run` / `get_forecast_run_by_job_id`), plus the v1
    top-level `post_export`. These are the only `/v2` routes in the API.
  - **Forecast configurations** (`forecast_configurations.py`): list / get-by-id / create /
    upsert / patch / delete-by-id — the reusable presets referenced by `post_forecast_run`.
  - **Ownership qualifiers** (`ownership_qualifiers.py`): list / get-by-id / create / upsert
    (distinct from scenario qualifiers).
  - **Type-curve writes**: `post_type_curves`, `put_type_curves`, `delete_type_curves`
    (query-filter delete by `name` / `id`; delete mechanism verified against the dev API).
  - **Directional-survey writes**: `post_directional_surveys`, `put_directional_survey_by_id`,
    `delete_directional_survey_by_id` (top-level routes, verified against the dev API).
  - **Econ-run detail reads**: `get_econ_run_monthly_econ_result_by_id` (requires `columns`),
    `get_econ_run_oneline_by_id`.
  - **Singletons**: `delete_project_by_id`; `delete_forecast_by_id` / `patch_forecast_by_id`;
    `get_users_roles`; `get_project_custom_columns` (project-scoped custom columns).
  - `ComboCurveAPI` now also mixes in `ForecastConfigurations`, `OwnershipQualifiers`, `Exports`.
  - `DELETE .../scenarios/head` is intentionally NOT wrapped: it appears in the Postman
    collection but returns 404 on the live API (a phantom entry). Scenario deletion is the
    existing `delete_scenarios` (collection query-filter). **No route-coverage gaps remain.**

### Fixed

- **Directional-survey reads migrated to the top-level routes (breaking).**
  `get_directional_surveys` / `get_directional_survey_by_id` built project-scoped URLs
  (`/projects/{id}/directional-surveys`) that the live API now returns 404 for ("Method does
  not exist"); they now hit the top-level `/directional-surveys` routes and **dropped their
  `project_id` parameter** (the project is a body field on create). The old signatures never
  worked against the current API.

## [1.3.1] - 2026-07-22

Released as `v1.3.1`. This entry covers everything merged since `v1.2.0`
(2025-09-04) and supersedes the never-tagged `1.3.0` dev version. (The per-type CSV convenience
functions were briefly on `main` as `<type>_to_csv_rows` / `<type>_from_csv_rows`
before being renamed to `<type>_to_row_dicts` / `<type>_from_row_dicts` for 1.3.1.)

### Added

- **Econ-model CRUD.** CREATE / UPDATE / DELETE for econ-model types — project
  per-type methods and generics, plus company-level generics — generated from
  `econModels.json` via an econ-model method codegen (`_econ_model_base`,
  `_models_generated`, composed by `Models`).
- **Econ-model assignments.** Generic POST / PUT / DELETE assignment methods to
  wire models to wells per scenario qualifier, plus
  `get_scenario_econ_model_assignments()` to read the scenario assignment grid.
- **Econ-model CSV mapping.** Exact, invertible API <-> CSV column mapping for 11
  econ-model types (`csv_columns`).
- **Econ-model CSV file layer + per-type convenience functions.** `EconModelMapper` is a base
  class (ABC) exposing, for every mapped type, a **row level** — `to_row_dicts(model, context=None)`
  / `from_row_dicts(rows)` (one model <-> a list of CSV-column-keyed row dicts, for finer-grained
  per-model control) — and a **whole-file level** — `to_csv(models, context=None)` / `from_csv(source)`
  for multi-model CSV text, and `read_csv(path)` / `write_csv(path, models)` for files. Per-type free
  functions (`<type>_to_row_dicts` / `<type>_from_row_dicts` / `<type>_to_csv` / `<type>_from_csv` /
  `get_<type>_mapper`; e.g. `capex_to_row_dicts`, `expenses_to_csv`) are generated from
  `econModels.json` + the mapper registry (`scripts/generate_csv_functions.py` ->
  `econ_models/_csv_generated.py`), thin wrappers over `get_mapper(...)`. `MAPPERS` / `get_mapper`
  moved to `econ_models/registry.py` (still re-exported from `econ_models`).
- **Capex $/ft capture.** The Capex CSV mapper now captures the model-level
  `drillingCost` / `completionCost` per-foot objects — which CC's own export omits —
  losslessly as JSON in two extra columns (`Drilling Cost ($/ft)` /
  `Completion Cost ($/ft)`) instead of warning and dropping them. CC ignores unknown
  headers on import, so the CSV stays re-importable. Round-trips exactly, including
  completion's tiered `dollarPerFtOfHorizontal` list and the `rows[]` timing schedule.
  A model carrying $/ft objects but no `otherCapex` rows emits a single carrier row so
  nothing is dropped. (Consumers staging `CapexMapper.columns` into SQL must add the two
  new columns as `NVARCHAR`, not float.)
- **Lookup-table CRUD.** Scenario lookup tables, type-curve lookup tables, and
  scenario-assignment lookups.
- **Forecast runs and bulk writes.** Forecast run as an async job (submit +
  poll job status) and a bulk forecast-parameters PUT.
- **`put_forecast_parameters_batched()`** returning a `BatchWriteResult` —
  parallel, chunked (25 well x phase records per request), and 207-aware so
  per-record failures are preserved (`results[i]` maps to `data[i]`;
  `success_count` / `failed_count` / `ok`) instead of being silently dropped.
  `BatchChunk` and `BatchWriteResult` are re-exported from the package root.
- **Resilient transport.** Automatic retry with backoff on HTTP 429 (honoring
  `Retry-After`) and on transient gateway errors (502 / 503 / 504), applied to
  all requests.
- **Generated docstring examples.** `Example response:` / `Example data:` blocks
  are generated (`scripts/generate_docstrings.py`) — first from the OpenAPI
  spec, then from the ComboCurve Postman collection with deterministic spoofed
  placeholder values. A `SLUG_ALIASES` map bridges doc-slug vs. spec
  `operationId` mismatches, and docstring URLs were repointed from stale
  `#uuid` anchors to current `/api/<slug>` links.

### Changed

- `put_forecast_parameters()` now chunks at 25 well x phase records per PUT.
- Migrated lint/format tooling from flake8 to ruff.
- Econ-model CSV mapper registry key for the Dates model is now `'Dates'` (was
  `'DateSettings'`), matching its `econModelType` in `econModels.json` and the generated
  CRUD methods. `get_mapper('Dates')` now resolves and `get_mapper('DateSettings')` no
  longer does; the class name (`DateSettingsMapper`) and module are unchanged.
- Test suite moved out of the installed package to a top-level `tests/` tree; test modules and
  their CSV fixtures no longer ship in the wheel or appear under the `combocurve_api_helper`
  import namespace. Dev scripts consolidated under `scripts/` (check-runners `test.sh` /
  `test.ps1` / `test.bat`, plus `codegen.sh` / `codegen.ps1` to run every generator).

### Fixed

- Capex CSV mapper now handles the `{'asOfDate': <int>}` escalation-start shape
  (renders `'as of date'`), not only `{'applyToCriteria': …}`. Previously
  `to_row_dicts` raised `NotImplementedError` on ~22% of real capex rows (2,150 of
  9,729 across three production projects). Verified live and against a CC CSV
  export.
- ProductionTaxes CSV mapper now handles the `dates` criteria (date-based rate
  schedules), not only `entire_well_life`/`offset_to_fpd`. The `Period` renders as
  CC's `%b-%y` (`Jul-23`); the `1900-01-01` schedule-start sentinel is `Jan-00`
  and round-trips losslessly. Previously `to_row_dicts` raised `NotImplementedError`
  on 12 production models. Verified live and against a CC CSV export.
- Econ-model assignment `econName` is the kebab-case route segment, not
  `econModelType`.
- `delete_scenario_qualifiers()` uses the plural `econNames` query param
  (the singular `econName` returned 400).
- DELETE assignment `wells` accepts a sequence (a plain list previously caused a
  silent no-op).
- DELETE econ-model assignments filters via query params rather than a request
  body, with a corrected (truthful) return type.

## [1.2.0] - 2025-09-04

Interim release: full route coverage, company-models methods, and a
`get_custom_columns` method. See git history for details.

## [1.1.2] - 2024-08-14

Interim release: forecast `POST .../forecasts/:id/wells` method, contributing
docs, and `_keysort` fixes. See git history for details.

## [1.0.5] - 2023-12-05

Initial published release under the `combocurve-api-helper` name. See git history
for details.
