"""Every route in the ComboCurve Postman collection is in `tests/route_manifest.json`, and its status is true.

The manifest holds one entry per collection operation (see `tests/route_manifest.py`). This test fails when:

- the collection has an operation the manifest does not list, or the manifest lists one the collection
  no longer has (run `python scripts/generate_route_coverage.py`);
- a `wrapped` route is not sent by the public method the manifest names, or a method sends a route the
  manifest does not call `wrapped` (the manifest's `status` must match the code);
- a public method sends nothing (give it an `ARGUMENT_OVERRIDES` entry);
- a status or a `method` name is not one the manifest may hold.

A `gap` route passes: it is a published operation the helper does not send yet, and the manifest lists it.

Network-dependent, skipped when the collection can't be fetched -- same policy as `test_route_paths.py` /
`test_docstring_slugs.py`.
"""

from __future__ import annotations

import inspect

from combocurve_api_helper import ComboCurveAPI
from tests.postman_collection import collection_requests, normalized_segments
from tests.route_manifest import (
    SENDS_NOTHING_BY_DESIGN,
    STATUSES,
    load_manifest,
    sent_by_method,
    template_reached_by,
)


def _collection_keys() -> set[tuple[str, str]]:
    """(VERB, '/path') for every collection operation, in the manifest's form."""
    keys: set[tuple[str, str]] = set()
    for _, request in collection_requests():
        segments = (request.get('url') or {}).get('path')
        if segments:
            keys.add((str(request.get('method', '')).upper(), '/' + '/'.join(normalized_segments(segments))))
    return keys


def test_manifest_lists_every_collection_operation_and_no_other() -> None:
    manifest_keys = {route.key for route in load_manifest()}
    collection_keys = _collection_keys()
    missing = sorted(collection_keys - manifest_keys)
    stale = sorted(manifest_keys - collection_keys)
    assert not missing, (
        'collection operations missing from tests/route_manifest.json (run the generator):\n'
        + '\n'.join(f'{verb} {path}' for verb, path in missing)
    )
    assert not stale, 'manifest routes the collection no longer has (run the generator):\n' + '\n'.join(
        f'{verb} {path}' for verb, path in stale
    )


def test_manifest_statuses_match_what_the_methods_send() -> None:
    sent, silent = sent_by_method()
    assert sorted(silent) == sorted(SENDS_NOTHING_BY_DESIGN), (
        f'public methods that sent no request (give them ARGUMENT_OVERRIDES): {sorted(silent)}'
    )
    public_methods = {
        name for name, _ in inspect.getmembers(ComboCurveAPI, inspect.isfunction) if not name.startswith('_')
    }

    problems: list[str] = []
    for route in load_manifest():
        if route.status not in STATUSES:
            problems.append(f'{route.verb} {route.path}: unknown status {route.status!r}')
            continue
        reached_by_any = any(template_reached_by(route.template(), operations) for operations in sent.values())
        if route.status == 'wrapped':
            if route.method not in public_methods:
                problems.append(f'{route.verb} {route.path}: method {route.method!r} does not exist')
            elif not template_reached_by(route.template(), sent[route.method or '']):
                problems.append(f'{route.verb} {route.path}: {route.method} does not send it')
        elif reached_by_any:
            reaching = sorted(
                name for name, operations in sent.items() if template_reached_by(route.template(), operations)
            )
            problems.append(f'{route.verb} {route.path}: status {route.status!r} but sent by {reaching}; regenerate')
    assert not problems, 'tests/route_manifest.json disagrees with the methods:\n' + '\n'.join(problems)
