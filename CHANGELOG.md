# Changelog

All notable changes to `combocurve-api-helper` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.3.1] - 2026-11-22

### Fixed

- `post_scenario_wells` and `put_scenario_wells` declare `data` as `Union[Sequence[str], ItemList]`: the route takes
  a JSON array of well-id strings, so callers no longer need to cast their ids to `ItemList` (a cast still
  type-checks). A single string now raises `TypeError` before anything is sent, instead of being sent as one id
  per character.

## [3.3.0] - 2026-11-22

### Added

- Every operation in the ComboCurve Postman collection now has a method (484 of 502; the other 18 are the
  retired v1 type-curve routes and the OAuth token route). New methods:
  - Company econ settings and econ report settings: `get_`, `count_`, `post_`, `put_`, `patch_`
    `econ_settings` / `econ_report_settings`, `get_` and `delete_econ_setting_by_id` /
    `econ_report_setting_by_id`.
  - Scenarios: `put_scenario_econ_model_assignments`, `delete_scenario_econ_model_assignments`,
    `get_scenario_well_incrementals`.
  - Forecasts: `put_forecast_daily_volumes`, `put_forecast_monthly_volumes`; forecast configurations:
    `delete_forecast_configurations` (bulk, by id); wells: `patch_project_company_wells`.
  - Production comments (`ProductionComments`, company and project scope) and production comment types,
    verified live on dev. Writes go in batches of 200 records (the route's maximum per request); a delete
    by `well_id` needs both `start_date` and `end_date`, which must equal the comment's stored dates.
  - `post_directional_surveys_batch`.
  - Formations (`Formations`, company and project scope; the PUT is an asynchronous import, with
    `wait_for_company_formations_job` / `wait_for_project_formations_job`).
  - Shapefiles (`Shapefiles`, company and project scope), including the three-step zip upload
    (`upload_company_shapefile` / `upload_project_shapefile` run it end to end and wait for the job). The
    file goes to the signed storage URL with only the headers the upload ticket names, never the API key
    or the bearer token.
- `wait_for_export_forecast_parameters`, `wait_for_export_forecast_volumes`, `wait_for_export_econ_monthly` and
  `wait_for_export_econ_one_liners` poll a v2 export job until it leaves `pending`/`running` (default timeout
  900 s). A finished forecast export reads `successful`, an econ export `complete`, a failed one `failed`.
- `iter_pages(url, params=None)`: a public, lazy page iterator (one parsed page per step, in ComboCurve's
  order, unsorted). The private `_get_items_iterator` delegates to it and keeps working.
- `filters` on `get_econ_model_assignments_by_type_by_id` (and the 16 per-type `get_<type>_assignments_by_id`),
  `get_econ_runs` and `get_econ_run_onelines`, for the query keys their GET routes document.
- `QueryFilters` (and `WellFilters`, now an alias of it) exported from the package root: the filter mapping
  the url builders take, where a sequence value is sent as one repeated key per value.

### Changed

- A repeated `well` / `wellId` / `id` filter longer than 100 values is de-duplicated and sent in requests of
  100 (the routes refuse 101), for the production, forecast-output, forecast and root volume getters and
  counts, the scenario model-assignment and well-incremental getters, and `delete_forecast_configurations`. A `skip` or
  `cursor` filter combined with more than one batch raises `ValueError`, because it would apply once per batch.
- Refused locally with `ValueError` before any request: a blank or empty well id in an unassign or a
  scenario well removal, an assignment-delete record with neither `allWells` nor non-empty `wellIds`, more
  than 500 records on a scenario assignment write, more than 25,000 `wellIds` across one assignment PUT, and
  an empty `data` on the new write methods. The root volume counts refuse `well` without `forecast`; the
  getters accept `well` with `project` (read per forecast, see below).
  `delete_scenario_wells` and the econ-model unassign methods refuse more than 100 well ids (101 is a
  400 on both routes, live 2026-11-21) instead of splitting the delete. A production-comment bulk delete
  refuses `production_comment_id` together with `well_id`. Id lists given as a comma string are split and
  stripped (`'a, b'` is two ids); a blank or whitespace-only id is refused.
  A company-route shapefile create (`post_company_shapefiles`, `post_company_shapefile_upload_import`,
  `upload_company_shapefile`) without `scope` `company` or `project` is refused before any request (the API
  answers 400 `RequiredFieldError`, after the upload was reserved).
- `get_type_curves` reads 2,500 type curves per page (the route's maximum), not 200. The v1-compatibility
  type-curve wrappers read forecast outputs at 1,000 per page, like `get_forecast_outputs`, not 200.
- `get_project_custom_columns` and its url builder are typed with overloads: a type checker now refuses a
  call with neither `custom_column` nor the deprecated `collection`. Requires `typing-extensions>=4.5.0`.
- `delete_directional_survey_by_id`, `delete_forecast_by_id`, `delete_forecast_segment_parameters`,
  `delete_project_by_id` and `delete_forecast_configuration_by_id` return the response headers, like the other
  deletes by id (they were annotated `ItemList`, see Fixed).
- The transport policy (timeouts, retries, deadline, connection failures) moved from `base.py` to the
  private `_transport.py`; `base.py` re-exports the moved constants and functions (not `_whole_chunk_failure`,
  now in `_batch.py` with a new signature, nor `_LINK_HEADER_ENTRY`). Patching a re-exported name in `base`
  no longer intercepts the transport; patch `requests.request` or the `_transport` name.
- `get_root_forecast_daily_volumes` / `_monthly_volumes` with `project` and no `forecast` now read the
  project one forecast at a time (one forecast list, one forecast-scoped listing per forecast) and check the
  total against the project count, raising `RuntimeError` on a mismatch or on a repeated `(forecast, well)` pair. ComboCurve's own project-scoped
  listing returns wrong rows on every dev project above 200 rows (short pages end the read early;
  `(forecast, well)` pairs repeat and drop) while its count matches. Rows now come grouped by forecast, in
  forecast-name order. `well` is now accepted with `project` (per forecast; the count check is skipped for a
  narrowed read), and `skip` / `cursor` are refused with `project` alone. The counts are unchanged.
- Refused with `ValueError` before any request: an empty list for a batched repeated filter (`well: []`
  sent no `well` key and read or counted every row); a delete whose url ends in `/` (a by-id delete given a
  blank id would reach the collection url); a blank `scenario_id` or `qualifier_name` on the econ-model
  unassign (the route may read it as absent and unassign more); a batched write with `chunksize` or
  `max_workers` below 1 (`chunksize=0` sent nothing and reported a clean write).
- The single-object writes (`_send_for_item`: exports, shapefile and formation imports, run starts) return `{}`
  for a success with an empty body instead of raising after the write went through.

### Fixed

- `delete_econ_model_assignments_by_type_by_id` (and the 16 per-type unassign methods) sent two or more wells
  as one comma-joined `wells` value, which ComboCurve answers with 400; it now sends one `wells` key per id.
  `delete_scenario_wells` had the same defect and the same fix. A single well is sent as before.
- `delete_directional_survey_by_id`, `delete_forecast_by_id`, `delete_forecast_segment_parameters`,
  `delete_project_by_id` and `delete_forecast_configuration_by_id` raised `JSONDecodeError` after the delete
  had gone through, because each route answers success with an empty body.

## [3.2.0] - 2026-11-17

### Changed

- The OAuth token is kept on disk, in `~/.combocurve/token-cache/` (one file per credential, named by
  the first 32 hex digits of a SHA-256 of the token URI, client id and secret). The file holds the
  bearer token in plain text with its write and refresh times, not the secret; on POSIX it is mode
  0600. A new script run reuses the token until it is due for refresh (60 s before expiry) instead of
  requesting one at startup, which spent one of the 10 token requests per client per 15 minutes. A
  client reads the file again before it fetches, so it takes a token another process fetched. A file
  that cannot be read, or whose times are not plausible (written more than 5 s in the future, or a
  refresh time before the write or more than 24 hours after it), is ignored; one that cannot be written gives a
  `RuntimeWarning`. If ComboCurve refuses a token still on disk, delete the file. New keyword
  arguments on `OAuthClientAuth`: `cache_token_on_disk` (default `True`) and `token_cache_directory`.
  The service-account (v1) token is signed locally and is not written to disk.

### Fixed

- The `get_scenario_lookup_table_assignments` docstring said `column` takes a comma-separated
  list; a comma-joined value answers 400. It now lists the 15 columns the route takes and the
  `QualifierNotFound` answer for a qualifier the column does not have (verified live 2026-11-13).

## [3.1.0]

### Added

- Embedded lookup tables (`EmbeddedLookupTables`), project and company routes:
  `get_embedded_lookup_tables`, `count_embedded_lookup_tables`, `get_embedded_lookup_table_by_id`,
  `post_embedded_lookup_tables`, `put_embedded_lookup_tables`, `delete_embedded_lookup_table_by_id`,
  and the same six with a `company_` prefix (`get_company_embedded_lookup_tables`, ...). Types:
  `capex`, `expenses`, `stream_properties`, `differentials`, `production_taxes`, `risking`,
  `operations` (from the server's 400 message, 2026-11-12). Lists take 200 per page (the server
  maximum) and are sorted like the other lists. The POST and PUT refuse an empty list with
  `ValueError` before any request. The class docstring shows the `rows` / `rules` shape
  and the `"lookup_by"` cell. `tests/test_embedded_lookup_tables_live.py` writes and deletes a
  throwaway table at both scopes on the dev tenant (passed 2026-11-13).
- `get_scenario_combos` takes `filters` (`savedName`, `updatedAt`, `sort`). The saved combos come back
  in the order received, so `sort` (for example `-updatedAt`) decides the order.
- `delete_scenario_combo` takes `combo_ids` to delete only those combos from a saved combo. They are
  sent as a repeated `comboIds` key; a comma-joined value answers 400 (verified live 2026-11-12). It
  refuses an empty sequence, an empty id or a bare string before any request.
- `get_scenario_lookup_table_assignments` and `get_scenario_lookup_table_assignment_by_id` take
  `filters` (`column`, `qualifierName`, `incrementalIndex`). Without `qualifierName` the list read
  returns only the column's active qualifier (verified live 2026-11-13); the by-id read most likely
  does the same (not verified).
- `tests/test_published_routes_are_wrapped.py`: every route in the Postman collection is reached by a
  method or is in a reviewed list of 97 unwrapped routes. Network-gated.
- A test that fails with `requests.HTTPError` shows the response (status, method, url, first 2,000
  characters of the body) in an "HTTP error response" report section (`tests/conftest.py`).

### Changed

- **`delete_scenario_lookup_table_assignment_by_id` requires `well_ids`** (max 500) and takes an
  optional `incremental_index`. The route takes the well ids as the request body. Before 3.1.0 the
  method sent no body, and the route refused every call (400), so no working call breaks; a call
  without `well_ids` now raises `TypeError` instead of `HTTPError`. The route
  has no qualifier parameter and clears only the column's active qualifier; for a well assigned
  only in another qualifier it answers `X-Delete-Count: 0` and changes nothing (verified live
  2026-11-13).
- `get_scenario_combos_url` takes `filters` with sequence values (`Mapping[str, Union[str,
  Sequence[str]]]`); a sequence repeats its key. Existing `dict[str, str]` callers are unchanged.
- `put_scenario_lookup_table_assignments` refuses an empty `data` and more than 500 records with
  `ValueError` before any request. An empty list sent a PUT with no body; more than 500 went as one
  request, above the route's documented maximum of 500.
- `put_scenario_lookup_table_assignments` documents the forecast column: a Type Curve V2 lookup table
  is assigned there with `column: 'forecast'` (verified live 2026-11-12). The server refuses a
  lookup-table id on `put_scenario_model_assignments` (`ForecastNotFound`).
- The `post_forecasts` example response shows the `id` that ComboCurve now returns.
- The v2 type-curve docstrings link to the operation pages (`.../api/get-v2-type-curves`), not the
  `type-curves-v2-preview/` pages, and carry generated examples (the fits, normalization and wells
  examples are large; the docstring points to the docs page). The v2 operations are in the Postman
  collection since 2026-11-12, so the slug and route-path tests now check them.

## [3.0.0] - 2026-11-05

ComboCurve stopped the v1 type-curve and type-curve lookup-table routes on 2026-11-07 (one-way).
This release moves those methods to the v2 routes. 2.x keeps the v1 methods (bug fixes only, branch `2.x`).

### Changed

- **Type curves use `/v2/projects/{projectId}/type-curves`.** `get_type_curves`,
  `count_type_curves`, `get_type_curve_by_id`, `delete_type_curves` and the type-curve lookup-table
  methods keep their names. Reads return the v2 shape: no embedded `fits`, `forecastSeries`,
  `excludedWells`; fields with no value are left out, never `null`.
- `post_type_curves` sends to the batch route (100 per request).
- `delete_type_curves` with no match returns `X-Delete-Count: 0` (v2 answers 404).
- A migrated lookup table has a new id; the old id answers 404 (see Deprecated).
- The type-curve methods no longer emit the 2.7.0 `DeprecationWarning`. Only the methods in the
  Deprecated list below warn.

### Added

- `post_type_curve`, `patch_type_curve`, `patch_type_curves`, `delete_type_curve_by_id`,
  `get_type_curve_fits`, `put_type_curve_fits`, `get_type_curve_normalization`,
  `put_type_curve_normalization`, `get_type_curve_volumes`, `get_type_curve_wells`,
  `count_type_curve_wells`, `post_type_curve_lookup_table`, `put_type_curve_lookup_table_by_id`.
- `type_curve_conversions`, exported from the package: `fits_for_put`, `normalization_for_put`
  (make a v2 read body safe to write back: a `linear` segment read back verbatim is stored with a
  different `qEnd`), `fits_from_v1`, `fits_to_v1`, `type_curve_to_v1`, `volumes_to_v1`,
  `lookup_table_from_v1`, `lookup_table_to_v1`, `lookup_table_id_from_v1`,
  `representative_well_from_v2`.
- `_build_params_string` repeats a key for a sequence value (`?well=a&well=b`).
- `tests/test_type_curves_v2_live.py`: a live round trip that writes and deletes its own type curve.
  It needs `CC_LIVE_TEST=1`, `CC_TC2_PROJECT_ID` and `CC_TC2_TYPE_CURVE_ID`, and a tenant enrolled
  in Type Curve 2.0. It passed on 2026-11-05.
- Scenario run: `post_scenario_run` starts a run (ComboCurve answers 202 with a job id) and
  `get_scenario_run_by_job_id` returns the job status.
- Scenario model assignments: `get_scenario_model_assignments`, `put_scenario_model_assignments` and
  `delete_scenario_model_assignments`. `put_scenario_model_assignments(add_wells_to_forecast=True)`
  also adds the wells to the forecast.
- Forecast wells: `get_forecast_wells` and `count_forecast_wells`. `get_forecast_wells_url` takes
  `filters`.

### Deprecated (kept until at least 2027-01-31, then removed in a 3.x release)

- `get_type_curve_daily_fits`, `get_type_curve_monthly_fits` (wrap `get_type_curve_volumes`).
- `get_type_curve_representative_fits` (wells + forecast outputs; `valid`, `hasData` left out).
- `put_type_curves` (upsert by name: merge existing, create new) and `post_type_curves` with v1
  `fits`/`regressionType`/`normalizations` (create, then `put_type_curve_fits`; not atomic).
  v1 `normalizations` are dropped, not written. A record that the server returns no result for
  is reported as a failed result named `MissingResult`. A create, patch or fits-write request that
  fails as a whole becomes failed results (`mayHaveApplied: true` when the request may have reached
  the server), and the fits of the records that succeeded are still written. Any 2xx result code
  counts as success; a result without `id` uses the id of the request body.
- v1 lookup-table rule fields (`riskFactorOil/Gas/Water`, `applyNormalization`, `phase`,
  `resolution`), translated on write. v2 rules apply to every phase, so a v1 rule written for one
  phase now applies to all phases. Rules with the same filter that differ by more than `phase`
  raise `ValueError`. `fpdSource: 'schedule'` raises `ValueError` on write (no v2 equivalent).
- A v1 lookup-table id on the by-id methods: tried once more as the migrated id, when the server
  answers 404 `LookupTableNotFoundError` (for delete, also `X-Delete-Count: 0`).
- The credential paths deprecated in 2.5.0 keep working; their removal moved to a 3.x release,
  not before 2027-01-31 (as stated in 2.7.0).

### Removed

- `get_company_emission_models`, `get_company_emissions_model_by_id`,
  `get_company_emissions_models_url`, `get_company_emissions_model_by_id_url`,
  `get_company_fluid_models`, `get_company_fluid_model_by_id`, `get_company_fluid_models_url` and
  `get_company_fluid_models_by_id_url`. ComboCurve has no company route for the Emission and
  FluidModel econ models: the server answered 400 (verified live 2026-09-30). Use the project
  route (`get_econ_models_by_type`). `econModels.json` now has `hasCompanyRoute` for each type.

### Fixed

- **`get_directional_surveys` works again.** It asked for 1000 surveys per page. The API allows at
  most 100 and answered 400, so every call failed. The page size is now 100. Also in 2.7.1.
- **Company per-type methods refuse a type with no company route.** `get_company_econ_models_by_type`,
  `get_company_econ_models_by_type_url` and the other company per-type methods raise `ValueError` for
  Emission and FluidModel before any request. Before, they sent the request and got a 400. Also in
  2.7.1 (the methods stay on 2.x).
- **Single-object requests have a timeout and retries.** `post_directional_surveys`,
  `put_directional_survey_by_id`, the v2 export methods (`post_export_*`, `get_export_*_by_job_id`),
  `post_export`, `post_forecast_wells`, `patch_forecast_by_id` and `post_forecast_run` called
  `requests` directly, with no timeout and no retry. A stalled connection blocked the call forever.
  They now send through the shared transport: the request timeout, the 429 retry, the gateway retry
  for a GET, and a second send only when the request never reached the server. Also in 2.7.1.
- **One call has a time limit.** The retries of one call could hold a caller for about 91 minutes.
  A call now has 600 s in total, counted across every retry. A retry whose pause would pass that limit
  is not made: a status retry returns the last response, and a connection retry raises the last error.
  Each send's read timeout shrinks to the time that remains. A write is not retried when its full
  read timeout would not fit. A `Retry-After` is capped at 120 s (was 3600 s). A write is never sent
  again because of the limit. Also in 2.7.1.

## [2.7.1] - 2026-11-05

### Fixed

- **`get_directional_surveys` works again.** It asked for 1000 surveys per page. The API allows at
  most 100 and answered 400, so every call failed. The page size is now 100.
- **Single-object requests use the transport.** Eight calls sent through `requests` directly:
  directional survey POST and PUT, v2 export POST and GET, v1 export POST, forecast wells POST,
  forecast PATCH and forecast run POST. They had no timeout and no retry. A stalled connection
  blocked the call forever. They now send through the same transport as every other call.
- **One call has a 600 s deadline. `Retry-After` is capped at 120 s.** The deadline covers every
  connection retry and every status retry of one call. A retry whose pause would reach the deadline
  is not made. A write is sent again only when its full read timeout fits in the time left. The
  `Retry-After` cap was 3600 s. A failed token request is retried like the request it serves.
- **Company routes for Emission and FluidModel raise `ValueError`.** ComboCurve has no company route
  for these two types: it answers 400. `get_company_econ_models_by_type_url` now raises `ValueError`
  before any request. The eight company methods for these types stay on 2.x, and each raises
  `ValueError`. 3.0.0 removes them. `econModels.json` has a new `hasCompanyRoute` key.

## [2.7.0] - 2026-11-05

### Deprecated

- **v1 type curves.** Every public type-curve and type-curve lookup-table method
  (`get_type_curves`, `count_type_curves`, `get_type_curve_by_id`, the representative, daily and
  monthly fits, `post_`/`put_`/`delete_type_curves`, and the six `*_type_curve_lookup_table*`
  methods) emits a `DeprecationWarning`: v1 type curves stop responding on 2026-11-07; upgrade to
  combocurve-api-helper 3.0.0. The `*_url` builders send no request and do not warn.

### Changed

- **Removal dates moved.** The older credential layout (`combocurve.json` + `cc-api.config.json`),
  `from_alternate_config` and the import-time API-key read are removed, and a directory with both
  credential files raises, in a 3.x release, not before 2027-01-31; 2.5.0 announced 3.0.0 and
  3.1.0. The `pyjwt[crypto]` dependency moves to an optional `legacy` extra on the same terms. The
  `DeprecationWarning` texts say so.
- **Econ-model CSV float columns are written in float form and read as `float`.** Each mapper
  declares `float_columns` (rates, prices, percents, $ amounts, WI/NRI, multipliers); those write a
  whole number as `9.0`, not `9`, and `from_row_dicts` returns them as `float`. Offsets, periods and
  counts stay integers. ProductionTaxes `Value` did this from 2.6.0; this release adds Capex,
  Dates, Differentials, Expenses, OwnershipReversion, Pricing, Risking and StreamProperties. CC's
  own export writes the form CC stores, which the API's JSON does not expose, so CSV text may now
  differ from a CC export as `3.0` vs `3`; the values are equal.

## [2.6.0] - 2026-11-04

### Added

- **`econ_models.model_scope(rows)`** returns `'company'` when a model's CSV rows say
  `Model Type` `company` (CC's company export), else `'project'`. The API payload has no scope
  field, so pass it back as `Context(scope=...)` when writing the model out again, and use it to
  pick the company or project route.

- **`put_project_monthly_productions_batched(project_id, data, *, chunksize=PUT_LIMIT, max_workers=10, on_progress=None)`.**
  The monthly-production twin of `put_forecast_parameters_batched`: sends the records in parallel
  chunks of at most `chunksize` (default `PUT_LIMIT`, 20,000) with coordinated 429 backoff, and
  returns the stitched `BatchWriteResult` so per-record failures and whole-chunk failures are
  reported rather than flattened away. `put_project_monthly_productions` is unchanged and still
  sends one request for the whole payload.

### Fixed

- **ProductionTaxes CSV mapper handles every live model.** Over 8,149 live ProductionTaxes models,
  `to_row_dicts` raised on 1,532 and stopped any export loop that hit one. Fixed:
  - criteria `oil_rate`, `gas_rate`, `water_rate` (CSV `oil rate`, `gas rate`, `water rate`),
    `offset_to_as_of_date` (`as of`), `offset_to_discount_date` (`disc date`),
    `offset_to_first_segment` (`maj seg`) and `offset_to_end_history` (`end hist`), as a raw CC
    export spells them;
  - units `dollar_per_month` (`$/month`) and `dollar_per_boe` (`$/boe`);
  - a `null` value, written as `nan` as CC's export writes it, and read back as `null`.
- **ProductionTaxes inverse keeps numbers and rows.** `from_row_dicts` returned the periods of an
  offset or rate criteria as strings (`['36', '1164']`); it now returns numbers, as the API serves
  them. A model with two ad valorem rows (% of revenue plus $/month or $/boe) wrote both as
  `Ad Val Tax`, and the inverse merged them into one row; they are now numbered `Ad Val Tax 1` and
  `Ad Val Tax 2`, as two severance rows of one phase already are.
- **ProductionTaxes `dates` Period is `MM/YYYY`, as CC exports it.** The mapper wrote `'%b-%y'`
  (`Jul-23`), which is how Excel displays CC's `07/2023`. That form lost the century: reading it
  back turned `1976-01-01` into `2076-01-01` and `2000-01-01` into `1900-01-01` (223 live models).
  The mapper now writes `07/2023` and `01/1900`, and still reads the old `Jul-23` form.

### Changed

- **ProductionTaxes CSV `Value` is a float column.** It writes a whole number as `9.0`, not `9`,
  and `from_row_dicts` returns it as `float`. `EconModelMapper.float_columns` (default empty)
  declares such columns; ProductionTaxes is the only mapper that sets it in this release.
- **License metadata is an SPDX expression.** `pyproject.toml` declares `license = 'MIT'` and
  `license-files = ['LICENSE']` in place of the deprecated `license = {file = 'LICENSE'}` table, and
  drops the `License :: OSI Approved :: MIT License` classifier. The build needs `setuptools>=77`.
  The distributions now carry `Metadata-Version: 2.4` with `License-Expression: MIT`; uploading them
  needs `twine>=6.1.0`. The license itself does not change.

## [2.5.0] - 2026-10-27

### Added

- **OAuth client credentials (v2).** ComboCurve now issues OAuth credentials only: `api-credentials.json`
  (`client_id`, `client_secret`; the docs page spells them `clientId`, `clientSecret`, and both
  spellings are read) with `api-key.txt`. The client gets a bearer token from
  `https://api.combocurve.com/v1/oauth/token`, caches it for its one-hour lifetime, replaces it 60 s
  before it expires, and sends `x-backend-version: v2` on every request. A refused token request raises
  the new `ComboCurveAuthError`. It is not sent again: the token endpoint allows 10 requests per client
  per 15 minutes.
- **`ComboCurveAPI.from_credentials_directory(path)`** reads the unzipped credential download as
  ComboCurve ships it: `api-key.txt` with `api-credentials.json` (OAuth) or
  `api-service-account-key.json` (legacy), at the top of `path` or in the ZIP's `combocurve/` folder.
  `ComboCurveAPI()` reads the same files from `~/.combocurve`.
- `ComboCurveAPI(auth=...)` takes any object with a `get_auth_headers()` method.

### Fixed

- **Pagination stays on `api.combocurve.com`.** The OAuth (v2) backend writes its internal Cloud Run
  host into the `Link` header. Following that url answered 401 after the first page, and sent the
  bearer token and API key to a host taken from a response header. The client now takes only the path
  and query from `Link` and keeps the host of the request (verified live: every page of a project list
  paginates, and matches the legacy credential's result).

### Changed

- **`combocurve-api-v1` is no longer a dependency.** The legacy service-account JWT is signed in
  `auth.py`, with the same claims and header, without the deprecated `datetime.utcnow()`. It depends on
  `pyjwt[crypto]` directly (it was a transitive dependency before); that becomes an optional `legacy`
  extra in 3.0.0.
- Pagination reads the `Link` header with the package's own parser, which also accepts `; rel="next"`
  with a space, an unquoted `rel`, and several relation types. The replaced parser required `;rel=`
  with no space.
- The older `combocurve.json` may hold either credential type; its `type` field selects the auth.
- The API key that `config.cfg` loads at import comes from `~/.combocurve/api-key.txt` when present,
  else from `cc-api.config.json` as before.

### Deprecated

- The `combocurve.json` + `cc-api.config.json` layout, read by `ComboCurveAPI()` when `~/.combocurve`
  holds no `api-key.txt`, and `ComboCurveAPI.from_alternate_config`. Both warn and are removed in 3.0.0.
- A credential directory with both `api-credentials.json` and `api-service-account-key.json` uses the
  OAuth file and warns. From 3.1.0 it raises. Each download has its own API key, and a key works only
  with its own credential, so one directory cannot serve both.

## [2.4.0] - 2026-09-30

### Added

- **HEAD count methods for every list route (all 64 HEAD routes in the collection).** A
  `count_<rest>` sits beside most list methods `get_<rest>`, takes the same arguments plus `filters`,
  and returns the `X-Query-Count` header of a HEAD request as an `int`: the number of matching
  documents, with no documents fetched. The company per-type econ-model routes have no per-type
  twin; count them with `count_company_econ_models_by_type`. Where the list method takes no `filters`
  (assignments by id, scenario combos, econ runs, econ-run one-liners), the count accepts the filters
  the HEAD route lists, so a filtered count has no list call to compare with.
  `count_root_forecast_{daily,monthly}_volumes` refuse unscoped `filters` locally, as the list methods
  do (verified live 2026-09-30: an unscoped HEAD returns 400). The econ-run url builders
  `get_econ_runs_url`, `get_econ_run_onelines_url` and `get_econ_run_monthly_export_id_url` take an
  optional `filters`. For example `count_projects(filters)`,
  `count_project_wells(project_id, filters)`, `count_forecast_outputs(project_id, forecast_id,
  filters)`, `count_econ_run_onelines(project_id, scenario_id, econ_run_id, filters)`. Econ models:
  `count_econ_models`, `count_econ_models_by_type`, `count_econ_model_assignments_by_type_by_id`,
  `count_company_econ_models`, `count_company_econ_models_by_type`, and the generated per-type
  `count_<type>_models` / `count_<type>_assignments_by_id`. Verified live 2026-09-29: `take` does not
  change the count, a filter that matches nothing gives 0, and every count checked against its list
  call agreed. A response without the header raises `ValueError` rather than reading as 0.
- **Type-less econ-model by id**: `get_econ_model_by_id(project_id, model_id)` and
  `get_company_econ_model_by_id(model_id)`. They return the model's header only (`id`, `name`,
  `econModelType`, timestamps, ...), not its assumption body (verified live); use them to learn a
  model's type, then read it with the by-type method.

### Changed

- The ActualOrForecast CSV fixtures are refreshed from 2026-09-29 ComboCurve exports of two projects
  (anonymized), so the real-export round-trip test covers `Ignore Historical Production`.

### Fixed

- **A single connection interruption no longer ends a call.** Before, a `requests.ConnectionError` or
  timeout went straight to the caller, and a request had no timeout at all, so a connection that
  stalled without a reset blocked forever. Every request that goes through `APIBase` (the list, write,
  count and batched-write paths) now carries a timeout of 30 s to connect and 300 s to read, and is sent
  again, up to 2 more times with 2 s and 4 s pauses, when that cannot write twice:
  - a request that never reached the server (connect timeout, refused connection, DNS failure), any
    method;
  - a GET or HEAD that failed after it was sent (reset, read timeout, truncated body).

  A POST, PUT, PATCH or DELETE that failed after it was sent is NOT sent again: the server may have
  applied it and only the response was lost. That error still goes to the caller, which must check what
  the server holds. The direct `requests` calls in `directional.py`, `exports.py` and `forecasts.py` are
  not covered.
- **A write is no longer sent again after a 502, 503 or 504.** The gateway gives up waiting while the
  server behind it may still apply the request, so a POST sent again could create the records twice.
  The gateway retry now applies to GET and HEAD only; a POST, PUT, PATCH or DELETE gets the gateway
  status back (`raise_for_status` raises `HTTPError`). **Behavior change for batched writes**
  (`_request_batched`, used by the forecast-parameter PUT): a chunk that gets a gateway status is no
  longer sent again; it is recorded as a whole-chunk failure whose `error_message` starts
  `gateway status <code>: the server may have applied this chunk`. A 429 is still retried for every
  method, because the quota refuses the request before it runs.
- **Batched writes: a lost connection no longer discards the whole batch.** A chunk whose connection
  failed used to raise out of `_request_batched` while the other chunks were still sent, so the caller
  lost every chunk's result. It is now recorded as a whole-chunk failure (`http_status` 0) and the
  other results are returned. New `BatchChunk.may_have_applied` is `True` for a write chunk that got a
  gateway status or lost its connection after it was sent: check the server before sending it again.
  The batch workers also fetch auth headers per request (a throttled batch could outlive its token),
  and a 429 on a chunk now waits for the response's `Retry-After` instead of a fixed 60 s.
- **Batched writes: `results[i]` no longer shifts after a failed chunk.** A chunk that failed as a
  whole contributed no results, so every later result moved left and `results[i]` described a
  different record than `data[i]`. Each record of such a chunk now gets a placeholder result
  `{'status': 'ChunkFailed', 'code': <status or 0>, 'errors': [...], 'mayHaveApplied': <bool>}`.
- **The client could not be pickled or deep-copied** since the auth lock arrived in 2.3.0
  (`TypeError: cannot pickle '_thread.lock' object`). The lock is now left out of the pickled state
  and a new one is made on restore.
- **StreamProperties `btu` rows wrote `Value` as `1100`; ComboCurve writes `1100.0`.** Checked
  against a raw 2026-09-06 export; `btu` rows now use the same decimal form as every other
  StreamProperties `Value`, and the real-export fixture carries a `btu` model.
- **`get_project_custom_columns(..., collection=...)` works again.** 2.2.2 renamed the keyword to
  `custom_column`, so a keyword caller got `TypeError`. `collection=` is accepted again as a
  deprecated alias (it warns `DeprecationWarning`); passing both, or neither, raises `TypeError`. The
  same holds for `get_project_custom_columns_url`. The 2.2.2 return type (`ItemList`, not one
  `Item`) stands.
- **`get_project_wells` ignored its `filters`** and returned every well in the project; it now
  sends them, so its result agrees with `count_project_wells` for the same filters.
- **`Retry-After: 0` waited 60 s.** A zero is now honoured; a negative or non-finite value falls back
  to the 60 s default instead of raising in `time.sleep`, and a value above 3600 s is capped at 3600 s.
- **`scripts/generate_docstrings.py --check` passed having verified nothing** when the collection
  matched no docstring marker (an empty collection, or every operation renamed). It now exits 2 (no
  verdict). `production.py`'s daily-production example was marked `Example data:` on a GET with no
  body, so it was never refreshed and showed raw `<number>` placeholders; it is now
  `Example response:` and regenerated.
- **Econ-model drift check reported the `fromSchedule` Capex keys as drift.** The Capex baseline in
  `econ_models/drift.py` now lists `fromSchedule`, `spudStart` and `completionStart` (the
  `fromSchedule` row keys handled since 2.3.1).

### Dependencies

- `urllib3` is now a declared dependency (it was already installed through `requests`): the
  connection-failure classification imports `urllib3.exceptions`.
- Dev group: `python-dotenv`, so `tests/conftest.py` can load the live-test dev ids from a gitignored
  `.env` (names in `.env.example`). Not a runtime dependency.

## [2.3.2] - 2026-09-29

### Changed

- **Docstring examples regenerated** from the ComboCurve Postman collection republished 2026-09-28
  (`directional`, `exports`, `forecasts`, `typecurves`). Example JSON only; no code change.
- **`scripts/generate_docstrings.py` ignores random re-draws.** The collection re-draws its literal
  example strings on every publish: enum picks (`exportType` took three different values in three
  publishes) and faker values (ids, dates, sentences). So each republish made `test_docstrings_current`
  fail with no API change. Literal strings from the collection are now marked: a committed block that
  differs only at those positions is kept, and array elements that differ only at those positions
  collapse to one. A change of shape, keys, array length or placeholder type still reports stale.
  Costs: an enum member that ComboCurve removes stays in a docstring until something else in that
  block changes, and a placeholder that becomes a literal is not detected. One-time effect: the two
  `forecasts` volume examples collapse at three levels: the result list and `phases` from 2 elements
  to 1, and every `series` list to 1 element (one had 2).

### Fixed

- **`ActualOrForecast` converter read "Ignore Hist Prod" as "Never", the opposite meaning.** ComboCurve
  has four per-phase choices (Never, Ignore Hist Prod, As Of Date, Date) but the v1 API has explicit
  keys for only three. A phase set to "Ignore Hist Prod" arrives as an EMPTY per-phase node under a
  PRESENT `replaceActualWithForecast` key (`{'oil': {}, 'gas': {}, 'water': {}}`), which the converter
  resolved by model name to `Never` (keep actuals) instead of ignoring history (verified live
  2026-09-29 against the ComboCurve screen and against ComboCurve's own CSV export). An empty phase
  node under a present key now exports as `Ignore Historical Production`, the string ComboCurve's CSV
  export writes (its screen abbreviates it "Ignore Hist Prod"). `from_row_dicts` reconstructs
  `Ignore Historical Production` as an empty phase node. New CSV `Criteria` value
  `Ignore Historical Production`: consumers that switch on `Criteria` must handle it. Unchanged: the
  model-level `ignoreHistoryProd` flag is still ignored -- ComboCurve's export shows a
  `{"ignoreHistoryProd": true}` model as Never, and explicit per-phase nodes win whatever the flag
  says -- and the legacy whole-node `actualOrForecast == {}` (no `replaceActualWithForecast` key) still
  resolves by model name (`Forecast As Of` -> As of Date, otherwise Never). Checked against
  ComboCurve's CSV export of two projects (36 models, 108 rows): mapper output from the live API
  matches on every row.

## [2.3.1] - 2026-09-17

### Fixed

- **`fromSchedule` Capex rows used the wrong `OffsetTo` tokens.** A `fromSchedule` otherCapex row
  carries its OWN date tokens -- `offset_to_spud_start` / `offset_to_completion_start` (companion API
  keys `spudStart` / `completionStart`) -- distinct from the `fromHeaders` tokens
  `offset_to_spud_date` / `offset_to_completion_start_date`. `OFFSET_TO_SCHEDULE_CSV` previously
  pointed at the `fromHeaders` tokens, so a real model raised
  `NotImplementedError: Unsupported fromSchedule OffsetTo token: 'offset_to_spud_start'`. Added the
  two `OffsetTo` members, re-pointed `OFFSET_TO_SCHEDULE_CSV` and `OFFSET_TO_API_DATEKEY`, and added a
  live-verified round-trip regression test (verified live 2026-09-17).

## [2.3.0] - 2026-09-07

### Added

- **`Context.scope` stamps the CSV `Model Type` for company-scope econ models.** An econ-model API
  dict carries no scope field, so a model fetched from a company endpoint (`get_company_*`) was
  indistinguishable from a project one and every converter wrote `Model Type = 'project'`. `Context`
  gained `scope: Literal['project', 'company'] = 'project'`, threaded through `common_columns` into
  `formats.model_type(unique, scope)`; pass `scope='company'` to stamp company models correctly. A
  `unique` model still resolves to `'unique'` regardless of scope, and the default keeps the prior
  output for every existing caller.

### Fixed

- **Auth-header retrieval is now serialized against concurrent token refresh.** `ComboCurveAuth`
  refreshes an expired token in place, so several threads fetching headers at once (e.g. GETs driven
  from a thread pool) could refresh concurrently -- undefined behavior. All header fetches now route
  through `APIBase._auth_headers()`, which holds a lock across the fetch (never across the HTTP
  request). The batched-write path already fetched headers once up front, which was and remains safe.

### Documentation

- **Project production endpoints noted as returning no rows for company-scoped wells.**
  `get_project_monthly_productions` / `get_project_daily_productions` gained a note (verified live
  2026-09-07) that they return zero rows when a project's wells are all company-scoped -- read
  production from the company endpoints instead of looping per well.

## [2.2.2] - 2026-09-06

### Fixed

- **`get_project_custom_columns` dropped every header past the first, and crashed on projects
  with none.** Its `custom_column` argument is not a collection name like the sibling
  `get_custom_columns`'s (`'wells'`, `'daily-productions'`, ...) -- the live API accepts only the
  literal `'headers'` for this path segment, so any other value 404s with
  `CustomColumnHeaderNotFoundError`. The method also hard-coded `columns[0]`, silently discarding
  every custom header beyond the first and raising an unhandled `IndexError` for the common case
  of a project with zero custom headers. The argument is renamed `collection` -> `custom_column`
  (it was already required), and the method returns the full `ItemList` (`[]` when a project has
  none) instead of one `Item`. **Breaking** for a caller that passed `collection=` by keyword
  (`TypeError`) or indexed the returned dict. Verified live against three dev projects.

## [2.2.1] - 2026-09-06

### Fixed

- **The StreamProperties CSV converter dropped `btuContent`.** It assumed ComboCurve's export never
  carries `btu` rows. An export shows one `Key='btu'` row per off-default category (`unshrunk gas` /
  `shrunk gas`, Value in the ordinary Value column, Unit `mbtu/mcf`); `to_row_dicts` now writes them
  and `from_row_dicts` reads them back into `btuContent`. A category at the default (1000) gets no
  row, so it reads back as absent. The dedicated `BTU (MBTU/MCF)` column stays blank. (The `Value`
  cell was written `1100`, not ComboCurve's `1100.0`, until 2.4.0.)

## [2.2.0] - 2026-09-04

### Added

- **Forecast-parameters export -> CSV converter.** `forecast_parameters_to_row_dicts(export_rows, wells)`
  (with `forecast_parameters_to_csv` / `write_forecast_parameters_csv` and the
  `FORECAST_PARAMETERS_COLUMNS` header) turns the rows of a forecast-parameters async export into the
  Title-Case, unit-bearing CSV a ComboCurve "Forecast Parameters" UI export produces -- the 23-column
  segment-parameter subset downstream tooling reads. Well identity (`INPT ID` / `Chosen ID` / `API 10`)
  is joined from company-well headers; a forecast row whose `well_id` is absent from `wells` raises. The
  21 snake_case input keys were verified against a real export. A one-way `RowWriter` mixin, extracted
  from `EconModelMapper`, provides the shared CSV-write plumbing (no new runtime dependency).

### Fixed

- **Five routes were misspelled and returned `404 Method does not exist`.**
  `get_root_forecast_monthly_volumes` and `get_root_forecast_daily_volumes` built
  `/v1/forecasts/{monthly,daily}-volumes`; the root routes are flat and hyphenated
  (`/v1/forecast-monthly-volumes`). Only the *project-scoped* pair nests under
  `forecasts/`. `patch_well_identifiers` built `/v1/well-identifiers`; the route is
  `/v1/wells-identifiers`. `get_type_curve_daily_fits` and
  `get_type_curve_monthly_fits` built `.../type-curves/{id}/{daily,monthly}-fits`; the
  route nests the resolution under `fits` (`.../fits/daily`). All five were broken for
  every call through 2.1.0. Every spelling is confirmed by the OpenAPI spec and the
  Postman collection, and the type-curve pair was confirmed live (404 vs. 200).
- **`tests/test_route_paths.py` now checks every route mechanically.** It resolves each
  method's `docs.api.combocurve.com/api/<slug>` docstring link to its Postman
  collection item and asserts the paired `*_url` builder produces that item's path —
  110 builders, network-gated like the existing docstring tests. The three root routes
  were found by hand; the two type-curve routes only fell out of this check.
- **`_build_params_string` rendered `None` filter values as the literal text
  `None`.** `filters={'take': None}` produced `?take=None`, which the API rejects on
  any numeric field. `None` values are now dropped, matching how `requests` treats a
  `None` in `params`.
- **A `take` in `filters` collided with the method's own page size.** Query
  parameters reach a request through two channels — `filters` baked into the url by
  the `*_url(...)` builder, and the `params` the api method passes to `requests`,
  which *appends* rather than merges. A caller-supplied `take` arrived twice
  (`?take=50&take=200`) and the API rejected the pair outright
  (``TypeError: `50,200` is not a valid number``). They are now reconciled once, in
  `_request_with_retry`: the url wins, so an explicit filter overrides the default.
- **The four production `delete_*` methods could never succeed.** They sent
  `well` / `startDate` / `endDate` as a JSON request body, but the production
  delete endpoints take them as **query parameters**, so every call returned
  `400 Bad Request`. Verified live: the same filters in the query string return
  `204` with `X-Delete-Count`.

- **Five delete methods forwarded an empty filter instead of refusing it.**
  `delete_company_wells`, `delete_project_company_wells`, `delete_project_wells`,
  `delete_scenarios` and `delete_type_curves` each inlined their own
  at-least-one-filter guard, and all of them let `chosen_id=''` (the shape an
  unresolved lookup produces) through alongside a real filter, sending
  `?chosenID=&dataSource=...` — a delete filtered on a value the caller never set. The
  guard is now the single `APIBase._require_any_filter`, which drops empty values and
  raises when none survive.
- **A chunked write could post later chunks to an earlier chunk's next-page url.**
  `_request_items_pages_chunks` rebound the shared `url` while following pagination, so
  chunk N+1 inherited chunk N's `skip`/`take`. Page-following now uses a local copy.
  (Previously this surfaced as a duplicate `take` the API rejected; the new parameter
  reconciliation would have made it silent.)
- **Three scenario sub-deletes forwarded an empty filter.** `delete_scenario_wells`,
  `delete_scenario_combo` and `delete_scenario_qualifiers` built their filter inline without the
  at-least-one-filter guard the sibling deletes use, so an empty string (e.g. from an unresolved
  lookup) reached the API as an unscoped destructive DELETE. They now refuse an empty filter.
- **CAPEX `escalationStart` on an absolute date raised `NotImplementedError`.** `capex_to_row_dicts`
  handled only `applyToCriteria` / `asOfDate`; a model whose escalation started on a `{'date': ...}`
  shape was dropped from any export. The `date` shape is now written `MM/DD/YYYY` and read back
  (accepting both `MM/DD/YYYY` and ISO), and the day-offset shapes render with a decimal point (`0.0`)
  to match the CC export.

### Changed

- **`_build_params_string` now percent-encodes filter values.** A filter containing
  `&`, `=`, `#`, a space or a non-ASCII character no longer corrupts the query
  string. Callers that previously pre-encoded values to work around the raw
  interpolation must stop, or they will now double-encode (`a%20b` → `a%2520b`).
  `,` is deliberately left literal and a space encodes as `%20` rather than `+`: three
  callers join list filters on commas (`columns`, `wells`, `econNames`) and those wire
  formats were live-verified unencoded.
- **`delete_company_wells` no longer takes `project_id`, and its filters are now
  keyword-only.** The route is company-scoped and the parameter was accepted and then
  never used — the url is `get_company_wells_url(filters)`, with no project in it — so a
  caller passing one believed a destructive delete was confined to a project when it was
  not. This is a correction, not a break of working behavior: the project scoping never
  happened. A caller that passed `project_id` (or any filter) positionally now gets a
  `TypeError` at the call site rather than a silently company-wide delete, so drop the
  argument and pass filters by keyword; for a project-scoped delete use
  `delete_project_company_wells`.
- **`delete_scenarios` gives `scenario_name` and `scenario_id` defaults.** They were
  required positionals, so callers had to pass `None` explicitly to filter by the
  other. Backwards compatible.
- **`get_root_forecast_monthly_volumes` / `_daily_volumes` now require a scope filter.**
  The API rejects a request that does not carry at least one of `project`, `forecast`
  or `well`, so it is refused with `ValueError` instead of sent. This mirrors
  `get_econ_run_monthly_export`, which already enforced its own required filter.
- **The four production `delete_*` methods take explicit filter
  arguments and return response headers.** `delete_company_monthly_productions`,
  `delete_company_daily_productions`, `delete_project_monthly_productions` and
  `delete_project_daily_productions` replace their `data: ItemList` parameter
  with a required `well_id` plus optional `start_date` / `end_date`, and return the
  `CaseInsensitiveDict` of response headers — `X-Delete-Count` is the number of
  records deleted — instead of an `ItemList`. This is the pattern the package's
  other delete methods already use. No migration is required in practice: the
  previous signature could not complete a request, so no working caller can exist.
  An old positional call, `delete_company_daily_productions([{...}])`, raises
  `ValueError` — the guard type-checks `well_id` at runtime so a stale caller cannot
  stringify a list into the query and issue a real DELETE.
- **A production delete without a well is now refused** with `ValueError` rather
  than sent. `well` is marked `required: true` on all four delete routes in the
  OpenAPI spec and `(Required)` in the Postman collection, so a date-only delete was
  never a supported call. The guard is falsy, so `well_id=''` is refused too.

## [2.1.0] - 2026-08-05

### Changed

- **Minimum Python is now 3.9.13** (was 3.8). The floor is set by `combocurve-api-v1`,
  which has declared `requires-python = >=3.9.13` since its 0.2.5; declaring the real
  value makes `pip` fail at install of this package rather than part-way through
  dependency resolution. The 3.8 classifier is dropped. Annotations across the package
  move to PEP 585 builtin generics (`dict` / `list`) and `collections.abc` imports;
  modules that evaluate annotations at runtime (the pydantic econ-model rows) keep
  `Optional` / `Union`, which PEP 604 could not replace before 3.10.
- **Several list endpoints return a different order.** The `_keysort` comparison key was
  assembled by *reading* the item's own key sequence (`values[order[key]]`) rather than by
  *writing* each value to its assigned position. Those are inverse permutations, and they agree
  only when `order` composed with the payload's key order is self-inverse — a property of the
  data, not of `order`. The declared position is now honored. Verified endpoint-by-endpoint
  against the live API:

  | endpoint | live key order | before | now |
  |---|---|---|---|
  | econ models (company + per type) | `id, name, createdAt, updatedAt` | `updatedAt` | `name` |
  | type curves | `id, name, createdAt, updatedAt` | `updatedAt` | `name` |
  | wells (company, project-company, project) | `id, wellName, createdAt, updatedAt` | `updatedAt` | `wellName` |
  | econ runs (list + by id) | `id, runDate, status` | `status` | `runDate` |
  | projects, scenarios, forecasts | `createdAt, id, name, updatedAt` | `name` | `name` (unchanged) |
  | productions, forecast volumes | — | unchanged | unchanged |

  ComboCurve does **not** serialize keys uniformly: some resources lead with `createdAt`, others
  with `id`. Orderings of two or fewer keys are self-inverse for every arrival order and so were
  never affected. Consumers that relied on recency-first ordering for econ models, type curves or
  wells should sort explicitly.
- **Type-curve representative wells tie-break by `wellId`.** The ordering named `id`, which that
  payload does not have (its id key is `wellId`), so the tie-break never fired and every returned
  well was padded with a spurious `id: null`. Wells sharing a `wellName` now order by `wellId`
  instead of retaining arrival order, and the `id` key is no longer added.
- **`get_well_comments` returns newest first**, ordered by `commentedAt` then `well`. It was passing the well-list
  ordering, whose four keys (`wellName`/`id`/`createdAt`/`updatedAt`) appear in no well-comment
  payload. That raised `ValueError` on every non-empty response before this release; keeping it
  would instead have silently performed no sort while padding four `null` keys onto every returned
  comment.

### Fixed

- `_keysort` no longer raises `ValueError: not enough values to unpack` on an item that
  carries none of the ordering keys, and no longer leaks raw non-`str` values into the
  comparison key — which could raise
  `TypeError: '<' not supported between instances of 'NoneType' and 'int'` when a null and
  a number met in the same key position.
- `scripts/generate_docstrings.py` now reports every failure to obtain the collection as
  "unavailable" (exit 2) rather than "stale" (exit 1): TLS errors, `http.client`
  exceptions such as a truncated `Content-Length` read, non-JSON bodies, and valid JSON of
  the wrong shape. A well-formed JSON object with no `item` tree previously produced a
  silent exit 0, so the freshness test passed having verified nothing.
- `patch_company_monthly_productions`, `patch_project_monthly_productions` and
  `patch_project_daily_productions` issued **PUT** rather than PATCH, against routes documented
  as `patch-*`. Their sibling `patch_company_daily_productions` was already correct, so this was
  a copy-paste slip rather than a deliberate choice; PUT and PATCH differ server-side in how
  omitted fields are treated.
- `scripts/audit_econ_model_drift.py` emitted a `_BASELINE_KEYS: Dict[str, FrozenSet[str]]`
  literal for pasting into `drift.py`, which imports neither name and has no
  `from __future__ import annotations` — pasting it raised `NameError` at import.

### Internal

- `scripts/` is now covered by `scripts/test.{sh,ps1,bat}` (ruff, format, mypy). Its
  absence is why the `audit_econ_model_drift.py` defect above went unnoticed. `test.bat`
  also propagates failures instead of always reporting success.
- Ruff rule set widened to `E/W/F/I/UP/B/SIM/TC/RUF` (`SIM108` ignored) and mypy to
  `strict` plus `warn_unreachable` / `warn_no_return` / `disallow_any_unimported`.
- The shared ordering constants are `MappingProxyType`, so `copy.deepcopy` and `pickle.dumps`
  on them now raise `TypeError` where `company_models.SORT_ORDER` (a plain dict before) allowed
  it. `.copy()` still works and returns a mutable `dict`.
- The `_keysort` comparison orders are single-sourced as `base.LIST_SORT_ORDER` /
  `base.WELL_LIST_SORT_ORDER`, replacing a dozen inline copies across six modules that
  nothing kept in sync. `company_models.SORT_ORDER` remains bound as an alias.
  `_keysort` now rejects negative or duplicate `order` positions, which would
  respectively corrupt and silently discard a key.
- `tests/test_api.py` looked for `cc_api_config.json`; the file `config.py` defines and
  ships is `cc-api.config.json`, so its live tests were unconditionally skipped.
- The two generated modules are excluded from the ruff *formatter* only, not the linter,
  with `force-exclude` so an explicit-path invocation cannot reformat them and break their
  byte-comparison freshness tests.

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
