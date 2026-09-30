# Count methods and list methods do not pair everywhere

Severity: low
Opened: 2026-09-30

## What happens now

- Four list methods take no `filters`, but their `count_*` twins do, because the HEAD route lists
  query keys: `get_econ_model_assignments_by_type_by_id` (and every generated
  `get_<type>_assignments_by_id`: `wells`, `scenarios`), `scenarios.get_scenario_combos` (none
  listed), `econ_runs.get_econ_runs` (`runDate`, `tags`), `econ_runs.get_econ_run_onelines`
  (`comboName`, `well`). A filtered count has no list call to compare with. Passing `filters` to the
  list method raises `TypeError`, so nothing is silent.
- The 16 company per-type list methods (`get_company_capex_models`, ...) have no
  `count_company_<type>_models` twin; `count_company_econ_models_by_type` covers them.
- `ECON_MODELS` gives `Emission` and `FluidModel` company routes that do not exist. Verified live
  2026-09-30: `HEAD` and `GET /v1/econ-models/emissions` and `/fluid-models` return 400
  (`is not a valid ObjectId`); `/v1/econ-models/capex` returns 200. The get and the count both fail
  loudly.

## What would unblock it

A decision: add `filters` to the four list methods (additive), or document the asymmetry per method.
For the company routes: mark `Emission`/`FluidModel` as project-only in `econModels.json`, or raise
locally.

## Files

- `src/combocurve_api_helper/_econ_model_base.py`, `scenarios.py`, `econ_runs.py`, `company_models.py`
- `assets/econModels.json`, `scripts/generate_model_methods.py`
