# Count methods and list methods do not pair everywhere

Closed: 2026-11-21 -- settled by: optional `filters` added to `get_econ_model_assignments_by_type_by_id` (and the 16 generated per-type wrappers), `get_econ_runs` and `get_econ_run_onelines`, with the keys each GET documents; `get_scenario_combos` already took them
If this was wrong, you will see: a filtered list whose length disagrees with its `count_*` twin

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
- Settled: `ECON_MODELS` gave `Emission` and `FluidModel` company routes that do not exist. Verified
  live 2026-09-30: `HEAD` and `GET /v1/econ-models/emissions` and `/fluid-models` return 400
  (`is not a valid ObjectId`); `/v1/econ-models/capex` returns 200. 3.0.0: `econModels.json` carries
  `hasCompanyRoute` (false for these two), the eight hand-written company methods for them are
  removed, and the company per-type url builder raises `ValueError` before any request. 2.7.1 gets
  only the `ValueError`.

## What would unblock it

A decision: add `filters` to the four list methods (additive), or document the asymmetry per method.
The company-route bullet needs no decision (settled above).

## Files

- `src/combocurve_api_helper/_econ_model_base.py`, `scenarios.py`, `econ_runs.py`, `company_models.py`
- `assets/econModels.json`, `scripts/generate_model_methods.py`

## Resolution (2026-11-21)

Decision taken: add `filters` (default `None`, last parameter). The GET operations document the same
keys as their HEAD twins: `get_econ_model_assignments_by_type_by_id` and every generated
`get_<type>_assignments_by_id` (`wells`, `scenarios`), `econ_runs.get_econ_runs` (`runDate`, `tags`),
`econ_runs.get_econ_run_onelines` (`comboName`, `well`); each also documents `sort`, `skip`, `take`.
`scenarios.get_scenario_combos` already took `filters` (`savedName`, `updatedAt`, `sort`); no change.
