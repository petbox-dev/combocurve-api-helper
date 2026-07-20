# Changelog

All notable changes to `combocurve-api-helper` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-07-20

Version `__version__` is set to `1.3.0`; a matching `v1.3.0` git tag has not been
cut yet. This entry covers everything merged since `v1.2.0` (2025-09-04).

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

### Fixed

- Capex CSV mapper now handles the `{'asOfDate': <int>}` escalation-start shape
  (renders `'as of date'`), not only `{'applyToCriteria': …}`. Previously
  `to_csv_rows` raised `NotImplementedError` on ~22% of real capex rows (2,150 of
  9,729 across three production projects). Verified live and against a CC CSV
  export.
- ProductionTaxes CSV mapper now handles the `dates` criteria (date-based rate
  schedules), not only `entire_well_life`/`offset_to_fpd`. The `Period` renders as
  CC's `%b-%y` (`Jul-23`); the `1900-01-01` schedule-start sentinel is `Jan-00`
  and round-trips losslessly. Previously `to_csv_rows` raised `NotImplementedError`
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
