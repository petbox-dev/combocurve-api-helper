# List getters hold the full result in memory; no public page iterator

Severity: low
Opened: 2026-11-06

## What happens now

The public list getters (for example `get_forecast_daily_volumes`, `get_forecast_monthly_volumes`,
`get_project_wells`, `get_scenario_econ_model_assignments`, `get_project_monthly_productions`) call
`APIBase._get_items` (`base.py:783`). It reads every page into one list before it returns. Many of
them then sort the list with `_keysort` (`base.py:987`), which makes a second, sorted copy.

A caller cannot stop early, so it cannot cap memory or bytes while it reads. The only method that
yields one page at a time is the private `_get_items_iterator` (`base.py:773`).

## Evidence

A downstream MCP server caps each result at 50 MB while it reads. It does this on the shared VM, which
has 15 GiB and no swap, and it can run 8 calls at the same time. To get page-by-page reads it calls
the private `_get_items_iterator` with the public URL builders (`get_*_url`) and the helper's own
`GET_LIMIT` constants, at 8 call sites (2026-11-06).

The server's final review estimated (not measured) that daily forecast volumes are about 0.5 MB of
JSON for each well. A project of a few hundred wells is then several GB as Python objects before the
sort.

## Blast radius

- Memory: any caller of a list getter on a large project.
- Stability: the server depends on a private method name, its `(url, params)` signature, and the
  module-level `GET_LIMIT` constants. A refactor of `base.py` (see
  `base-py-mixes-transport-policy-with-the-client-class`) can break it without a deprecation warning.

## Fix

Add a public page iterator, for example
`iter_pages(url: str, params: Mapping[...] | None = None) -> Iterator[ItemList]`, or an `iter_*`
twin for each list getter that applies the getter's own `take` and filters. Document that it
returns pages in ComboCurve order (no `_keysort`). Keep `_get_items_iterator` as an alias for one
deprecation window. Optionally expose the per-route page size as a public constant, or apply it
inside the iterator, so callers stop importing module `GET_LIMIT` values.

## What is still unverified

- The per-well size of daily forecast volumes. This is an estimate, not a measurement.
- Whether any existing caller depends on `_keysort` order from a getter that would get an `iter_*`
  twin. The twin can document "unsorted"; the getter keeps its sort.

## Files

- `src/combocurve_api_helper/base.py`: `_get_items_iterator`, `_get_items`, `_keysort`
- `src/combocurve_api_helper/forecasts.py`, `wells.py`, `scenarios.py`, `production.py`,
  `econ_runs.py`: list getters and their `GET_LIMIT` constants
