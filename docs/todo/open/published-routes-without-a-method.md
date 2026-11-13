# Published routes without a method

Severity: low
Opened: 2026-11-05

## What happens now

The audit of 2026-11-05 compared the published v1 operations with the public methods. 79 published
operations have no method (86 on 2026-11-05; 7 wrapped since, see Wrapped).

2026-11-12: `tests/test_published_routes_are_wrapped.py` now holds the reviewed list (`_UNWRAPPED`, 97
entries: these 79, the 17 retired v1 type-curve routes and the OAuth token route). A new route fails
that test. The embedded lookup tables are now in the Postman collection (12 operations: 6 project,
6 company) and are wrapped in 3.1.0. The test run of 2026-11-12 gives the same 79, area by area.

## New between 2026-08 and 2026-10 (50)

| Area | Operations |
|---|---|
| Econ report settings | 7 |
| Formations | 18 |
| Shapefiles | 21 |
| Scenario econ-model assignment PUT and DELETE | 2 |
| Well incrementals | 1 |
| Directional-survey batch | 1 |

## Wrapped (7)

| Area | Operations | Methods |
|---|---|---|
| Scenario run | 2 | `post_scenario_run`, `get_scenario_run_by_job_id` |
| Scenario model assignments | 3 | `get_`, `put_`, `delete_scenario_model_assignments` |
| Forecast wells | 2 | `get_forecast_wells`, `count_forecast_wells` |
| Embedded lookup tables (3.1.0) | 12 | `get_`, `count_`, `post_`, `put_` `embedded_lookup_tables`, `get_`, `delete_embedded_lookup_table_by_id`, and the `company_` six |

## Older (29)

| Area | Operations |
|---|---|
| Econ settings | 7 |
| Production comments | 16 |
| Production comment types | 2 |
| Project company-wells PATCH | 1 |
| Forecast volumes PUT | 2 |
| Forecast-configurations DELETE | 1 |

## What to do

Decide per area whether to wrap it. Each new method needs its `*_url` builder and its docs link
(see CLAUDE.md "Adding a new endpoint group"). Remove the route from `_UNWRAPPED` in
`tests/test_published_routes_are_wrapped.py` when it is wrapped; the test fails until then.
