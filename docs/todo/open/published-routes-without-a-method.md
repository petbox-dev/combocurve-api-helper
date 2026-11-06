# Published routes without a method

Severity: low
Opened: 2026-11-05

## What happens now

The audit of 2026-11-05 compared the published v1 operations with the public methods. 79 published
operations have no method (86 on 2026-11-05; 7 wrapped since, see Wrapped). 6 more operations are in the docs only (embedded lookup tables).

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
(see CLAUDE.md "Adding a new endpoint group"). The audit method is in
`no-test-checks-that-published-routes-are-wrapped.md`.
