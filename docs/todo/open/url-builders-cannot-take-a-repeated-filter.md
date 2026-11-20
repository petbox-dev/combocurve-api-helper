# URL builders cannot take a repeated filter

Severity: low
Opened: 2026-11-13

## What happens now

`_build_params_string` repeats a key for a sequence value (`{'well': ['a', 'b']}` gives
`?well=a&well=b`). About 50 `*_url` builders type `filters` as `Optional[dict[str, str]]`, so a typed
caller cannot pass a sequence. 3.1.0 widened one builder (`get_scenario_combos_url`, for
`comboIds`) to `Mapping[str, Union[str, Sequence[str]]]`.

Routes that take a repeated filter through a `dict[str, str]` builder:

- `get_forecast_outputs_url` and the forecast volume builders: `well` must be repeated (a comma-joined
  value is a 400, verified live 2026-11-05). `type_curves_v1_compatibility.py` therefore rebuilds the
  outputs path by hand and appends `_build_params_string({'well': chunk})`.
- `get_scenario_model_assignments_url`: `wellId` "up to 100 values" (form not verified live).
- Monthly and daily productions, company and project scope (`get_*`, `count_*` and the URL builders):
  **done 2026-11-20.** `well` takes repeated keys; a comma-joined value is a 400. The limit is 100 `well`
  values per request (100 accepted, 101 refused with `400 OperatorError: "0" is not an allowed operator`),
  verified live on dev for company monthly, company daily (HEAD), and project monthly (HEAD). The `get_*`
  and `count_*` methods split a `well` list longer than 100 into batches (after de-duplicating), then
  combine the rows or sum the counts. `WellFilters` is `Mapping[str, Union[str, Sequence[str]]]`.
  Still unverified: a live multi-batch call needs more than 100 distinct wells, and dev has 7 company wells.
  The batching is covered offline by `tests/test_production_well_batches.py`.
- Forecast outputs (`get_forecast_outputs`, `count_forecast_outputs`, key `well`) and scenario model
  assignments (`get_scenario_model_assignments`, key `wellId`): **done 2026-11-20.** The 100-value cap was
  verified live on both (100 accepted, 101 refused with a 400) through the raw URL builders. The public
  methods split longer lists through `APIBase._filter_value_batches` in `base.py`. The
  scenario-assignment rows are concatenated in request order, not re-sorted.
- Forecast volumes (`get/count_forecast_daily_volumes`, `get/count_forecast_monthly_volumes`) and root
  volumes (`get/count_root_forecast_daily_volumes`, `get/count_root_forecast_monthly_volumes`): **done
  2026-11-20.** The forecast-scoped routes take 100 `well` values (101 refused with a 400). The root routes
  also refuse 101, but they accept a `well` list only together with `forecast`: `well` alone, and
  `project` with `well`, return 400 even at 100 values. `_require_volume_scope` now refuses a `well` filter
  without `forecast` with a local ValueError (2026-11-20), so those requests never reach the API.
- Scenario econ-model assignments have no well filter, so they are not affected.

Two other methods bypass their builders the same way: `scenarios.delete_scenario_qualifiers`
(`f'{base_url}/qualifiers' + ...`) and the compatibility outputs call above.

## Fix

A `QueryFilters` alias in `base.py` (`Mapping[str, Union[str, Sequence[str], None]]`, spelled with
`Union` because a `TypeAlias` right-hand side is evaluated at runtime on 3.9), used by
`_build_params_string` and by each builder whose route takes a repeated key. Then call the builders
from the two bypass sites. Live-verify `wellId` and the lookup-table assignments `column` filter
(documented as comma-separated) before stating their form.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phases 1-2.
