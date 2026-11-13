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

Two other methods bypass their builders the same way: `scenarios.delete_scenario_qualifiers`
(`f'{base_url}/qualifiers' + ...`) and the compatibility outputs call above.

## Fix

A `QueryFilters` alias in `base.py` (`Mapping[str, Union[str, Sequence[str], None]]`, spelled with
`Union` because a `TypeAlias` right-hand side is evaluated at runtime on 3.9), used by
`_build_params_string` and by each builder whose route takes a repeated key. Then call the builders
from the two bypass sites. Live-verify `wellId` and the lookup-table assignments `column` filter
(documented as comma-separated) before stating their form.

Found by the `/code-fix` run over 3.1.0 (2026-11-13), Phases 1-2.
