Closed: 2026-11-12 -- settled by: the collection has the 24 v2 operations; docstring links use the collection names, the slug skip is gone, the route-path floor is 170, examples are generated
If this was wrong, you will see: `test_docstring_slugs.py` or `test_route_paths.py` fail on a `-v2-` slug, or a v2 docstring with no example where the collection has one.

# v2 type-curve routes have no Postman source

Severity: low
Opened: 2026-11-05

## What happens now

**2026-11-12: the collection now has the v2 type-curve operations** (24, named `get-v2-type-curves`,
`put-v2-type-curve-fits`, ...). `tests/test_published_routes_are_wrapped.py` reaches all of them. The
docstring links still use `type-curves-v2-preview/<name>`, so these checks still skip the v2 methods:

- `tests/test_route_paths.py`: no collection path to compare; the method is not counted.
- `tests/test_docstring_slugs.py`: skips links that start with `type-curves-v2-preview/`.
- `scripts/generate_docstrings.py`: the v2 docstrings carry no `Example response:` block.

The v2 builders are checked only by the offline tests in `tests/type_curves/` and by the live test
`tests/test_type_curves_v2_live.py`.

## Risk

The docs path contains `-preview`. It can move when the routes reach general availability. A moved
slug is not detected until a person follows a link.

## What would unblock it

Done on 2026-11-12: ComboCurve publishes the v2 operations in the collection. Next: change the v2
docstring links to `https://docs.api.combocurve.com/api/<collection name>` (check that the page
exists), drop the `type-curves-v2-preview/` skip, raise the `test_route_paths.py` floor, and add
`Example response:` markers so the generator fills them.

## Files

`tests/test_docstring_slugs.py`, `tests/test_route_paths.py`, `src/combocurve_api_helper/typecurves.py`
