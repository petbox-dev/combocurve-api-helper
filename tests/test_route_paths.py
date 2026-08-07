"""Correctness check: every `*_url` builder produces the path its operation declares.

Route literals are hand-written, and through 2.1.0 **five** of them were wrong --
`forecast-monthly-volumes`, `forecast-daily-volumes` and `wells-identifiers` were
misspelled in `root.py`, and `type-curves/{id}/fits/{daily,monthly}` were spelled
`{daily,monthly}-fits` in `typecurves.py`. Every one 404'd with the Google-ESP body
`{"code": 5, "message": "Method does not exist."}`, i.e. the method could never
succeed for any caller. Three were caught by hand; the last two only fell out of
this check.

Nothing else validates a path. `test_docstring_slugs.py` already fetches the same
Postman collection and walks the same item tree, but reads only `item['name']` --
the item also carries `item['request']['url']['path']`, which is what this uses.

Method -> operation is the `https://docs.api.combocurve.com/api/<slug>` link in the
public method's docstring (slug == collection item name, the same mapping
`scripts/generate_docstrings.py` uses). Method -> builder is the repo's naming
convention: `<method>_url`, or for a write verb the `get_`-prefixed builder it shares
with the read method (`delete_company_wells` -> `get_company_wells_url`). A method is
only checked when BOTH resolve, so this is a floor on coverage, not a guarantee of it
-- the `checked` assertion keeps that floor from silently collapsing if a convention
drifts.

Network-dependent, skipped when the collection can't be fetched -- same policy as
`test_docstring_slugs.py` / `test_docstrings_current.py`.
"""

import inspect
import re
import warnings
from typing import Any, Callable

import pytest
import requests

from combocurve_api_helper import ComboCurveAPI

# Mirrors scripts/generate_docstrings.py COLLECTION_URL (the collection is never vendored).
_COLLECTION_URL = 'https://docs.api.combocurve.com/downloads/combocurve-api.postman_collection.json'
_SLUG_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+)')

# A 24-hex ObjectId stands in for every required path argument. Nothing is sent, so the
# value only has to be recognizable again in the built url.
_PLACEHOLDER = '0' * 24

# Path segments that are a caller-supplied id rather than a literal: the placeholder, and
# the collection's own `:param` spelling.
_ID_SEGMENT = re.compile(rf'^(?:{_PLACEHOLDER}|:.*)$')

# Builders whose path legitimately has no collection counterpart.
_EXEMPT = {
    # v2 async export routes live under a different base url and item tree.
    'get_v2_export_url',
    'get_v2_export_by_job_id_url',
}


def _normalize(path_segments: list[str]) -> str:
    """Collapse id segments to `:p` so a built url and a collection template compare equal."""
    return '/' + '/'.join(':p' if _ID_SEGMENT.match(str(s)) else str(s) for s in path_segments)


def _collection_paths() -> dict[str, str]:
    """slug (collection item name) -> normalized path template."""
    response = requests.get(_COLLECTION_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
    response.raise_for_status()
    paths: dict[str, str] = {}

    def walk(items: list[dict[str, Any]]) -> None:
        for item in items:
            if 'item' in item:
                walk(item['item'])
                continue
            segments = ((item.get('request') or {}).get('url') or {}).get('path')
            if segments:
                paths[item.get('name') or ''] = _normalize(segments)

    walk(response.json().get('item', []))
    return paths


def _builder_for(method_name: str) -> tuple[str, Callable[..., str]] | tuple[None, None]:
    """Resolve a public method to the `*_url` builder that assembles its path.

    Read methods pair as `<method>_url`. Write verbs have no builder of their own --
    they reuse the read builder (`delete_company_wells` -> `get_company_wells_url`), so
    the verb prefix is swapped for `get_` on the second attempt.
    """
    candidates = [f'{method_name}_url']
    verb, _, rest = method_name.partition('_')
    if verb in {'post', 'put', 'patch', 'delete'} and rest:
        candidates.append(f'get_{rest}_url')

    for candidate in candidates:
        builder = getattr(ComboCurveAPI, candidate, None)
        if builder is not None and candidate not in _EXEMPT:
            return candidate, builder

    return None, None


def _built_path(builder: Callable[..., str]) -> str:
    """Call `builder` with placeholders for its required args and normalize the result."""
    required = [
        name
        for name, parameter in list(inspect.signature(builder).parameters.items())[1:]
        if parameter.default is inspect.Parameter.empty and name != 'self'
    ]
    # A couple of builders validate an enum argument (`phase`, `series`) and warn when
    # the placeholder is not one of its names. The path is still assembled, and the path
    # is all this checks, so the warning is noise here.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        url = builder(ComboCurveAPI.__new__(ComboCurveAPI), *([_PLACEHOLDER] * len(required)))

    base = ComboCurveAPI.API_BASE_URL.rsplit('/v1', 1)[0]

    return _normalize(url.split('?')[0][len(base) :].strip('/').split('/'))


def test_url_builders_match_the_collection_route_paths() -> None:
    try:
        collection = _collection_paths()
    except (requests.RequestException, ValueError) as exc:
        pytest.skip(f'ComboCurve Postman collection unreachable: {exc}')

    mismatches: list[str] = []
    checked = 0

    for name, method in inspect.getmembers(ComboCurveAPI, inspect.isfunction):
        if name.endswith('_url'):
            continue

        slug_match = _SLUG_RE.search(method.__doc__ or '')
        if slug_match is None:
            continue

        builder_name, builder = _builder_for(name)
        expected = collection.get(slug_match.group(1))
        if builder is None or expected is None:
            continue

        try:
            built = _built_path(builder)
        except (TypeError, ValueError):
            # Builder needs an argument shape the placeholder cannot satisfy; the slug
            # test still covers its docs link.
            continue

        checked += 1
        if built != expected:
            mismatches.append(
                f'{name} (via {builder_name}): builds {built}, collection says {expected} (slug: {slug_match.group(1)})'
            )

    assert not mismatches, 'url builders whose path disagrees with the collection:\n' + '\n'.join(sorted(mismatches))
    # Floor set just under the count at the time of writing (110 of 116 slug-carrying
    # methods resolve to a builder). A convention drift that silently stops checking
    # most of the surface should fail loudly rather than pass vacuously.
    assert checked >= 100, f'only {checked} builders were checked -- the slug/builder naming convention drifted'


def test_the_five_previously_broken_routes_stay_fixed() -> None:
    """Offline pin for the specific 404s, so a revert fails without needing the network."""
    api = ComboCurveAPI.__new__(ComboCurveAPI)
    base = ComboCurveAPI.API_BASE_URL

    assert api.get_root_forecast_monthly_volumes_url() == f'{base}/forecast-monthly-volumes'
    assert api.get_root_forecast_daily_volumes_url() == f'{base}/forecast-daily-volumes'
    assert api.get_well_identifiers_url() == f'{base}/wells-identifiers'
    assert api.get_type_curve_daily_fits_url('P', 'T') == f'{base}/projects/P/type-curves/T/fits/daily'
    assert api.get_type_curve_monthly_fits_url('P', 'T') == f'{base}/projects/P/type-curves/T/fits/monthly'
