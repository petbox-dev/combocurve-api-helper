# v2 type-curve routes have no Postman source

Severity: low
Opened: 2026-11-05

## What happens now

The ComboCurve Postman collection has no v2 type-curve operations (checked 2026-11-05). Three checks
therefore skip the v2 type-curve methods:

- `tests/test_route_paths.py`: no collection path to compare; the method is not counted.
- `tests/test_docstring_slugs.py`: skips links that start with `type-curves-v2-preview/`.
- `scripts/generate_docstrings.py`: the v2 docstrings carry no `Example response:` block.

The v2 builders are checked only by the offline tests in `tests/type_curves/` and by the live test
`tests/test_type_curves_v2_live.py`.

## Risk

The docs path contains `-preview`. It can move when the routes reach general availability. A moved
slug is not detected until a person follows a link.

## What would unblock it

ComboCurve publishes the v2 type-curve operations in the collection. Then: drop the
`type-curves-v2-preview/` skip, raise the `test_route_paths.py` floor, and add docstring examples.

## Files

`tests/test_docstring_slugs.py`, `tests/test_route_paths.py`, `src/combocurve_api_helper/typecurves.py`
