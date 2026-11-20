# Published routes without a method

Severity: low
Opened: 2026-11-05

## What happens now

58 published operations have no public method. `tests/route_manifest.json` lists each one with
`"status": "gap"`; `python scripts/generate_route_coverage.py --check` keeps the file current.
Gaps are not accepted decisions: a route stays `gap` until a method sends it.

| Area | Gaps |
|---|---|
| Shapefiles | 21 |
| Formations | 18 |
| Production comments | 16 |
| Production comment types | 2 |
| Directional-survey batch (`POST /v1/directional-surveys/batch`) | 1 |

Not counted here: the 17 v1 type-curve routes ComboCurve retired on 2026-11-07 (`status: retired`) and
`POST /v1/oauth/token` (`status: not-via-method`, sent by `auth.py`).

## Wrapped since the audit

- 2026-11-12: scenario run, scenario model assignments, forecast wells, embedded lookup tables (3.1.0).
- 2026-11-20: scenario econ-model assignment `PUT` and `DELETE`, scenario well incrementals (`GET`),
  forecast daily and monthly volumes `PUT`, econ report settings (7 routes) and econ settings (7 routes).
  Both have a live round trip on dev that passed. Forecast-configurations bulk `DELETE` and project
  company-wells `PATCH` are wrapped too, with offline tests only. The econ settings test needs `CC_DEV_ECON_CATEGORY`
  (`Cash Flow`) and `CC_DEV_ECON_COLUMN_KEY` (`net_income`) set, which the test skips without.

## Blast radius

Each gap is a published operation a caller cannot reach through the helper. None is known to be
broken: the helper does not send these routes at all.

## What would unblock it

Per area: a method with its `*_url` builder and docs link (CLAUDE.md "Adding a new endpoint group"),
then regenerate the manifest. Each area is its own change. The econ settings and econ report settings
need a decision on the public shape first; their collection descriptions are in the manifest `area`
entries and the Postman collection.

## Files

- `tests/route_manifest.json`: status of every collection operation.
- `scripts/generate_route_coverage.py`: regenerates the manifest.
- `tests/test_published_routes_are_wrapped.py`: fails when the manifest is stale or a status is wrong.
