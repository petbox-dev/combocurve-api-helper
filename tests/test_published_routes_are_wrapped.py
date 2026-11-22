"""Every route in the ComboCurve Postman collection is in `tests/route_manifest.json`, and its status is true.

The manifest holds one entry per collection operation (see `tests/route_manifest.py`). This test fails when:

- the committed file differs from what the generator would write now: an operation added, removed or
  renamed in the collection, a status or `method` that changed (run `python scripts/generate_route_coverage.py`);
- a `wrapped` route is not sent by the public method the manifest names, or a method sends a route the
  manifest does not call `wrapped` (the manifest's `status` must match the code);
- a public method sends nothing (give it an `ARGUMENT_OVERRIDES` entry);
- a status or a `method` name is not one the manifest may hold.

A `gap` route passes: it is a published operation the helper does not send yet, and the manifest lists it.

Network-dependent, skipped when the collection can't be fetched -- same policy as `test_route_paths.py` /
`test_docstring_slugs.py`. The offline checks of the tooling itself are in `test_route_manifest_tooling.py`.
"""

from __future__ import annotations

import difflib

from tests.postman_collection import COLLECTION_URL, collection_requests
from tests.route_manifest import (
    ROUTE_MANIFEST_PATH,
    SENDS_NOTHING_BY_DESIGN,
    STATUSES,
    build_manifest,
    load_manifest,
    operations_from_collection,
    public_method_names,
    render_manifest,
    routes_reached,
    sent_by_method,
)

# Diff lines shown on failure; the full diff of a large change helps no one.
_MAX_DIFF_LINES = 60


def test_manifest_is_what_the_generator_would_write() -> None:
    operations = operations_from_collection(collection_requests())
    expected = render_manifest(build_manifest(operations, sent_by_method().sent, load_manifest()), COLLECTION_URL)
    committed = ROUTE_MANIFEST_PATH.read_text(encoding='utf-8') if ROUTE_MANIFEST_PATH.exists() else ''
    if committed != expected:
        diff = list(
            difflib.unified_diff(
                committed.splitlines(),
                expected.splitlines(),
                'tests/route_manifest.json (committed)',
                'tests/route_manifest.json (generated)',
                lineterm='',
                n=2,
            )
        )
        shown = diff[:_MAX_DIFF_LINES] + (
            [f'... {len(diff) - _MAX_DIFF_LINES} more lines'] if len(diff) > _MAX_DIFF_LINES else []
        )
        raise AssertionError(
            'tests/route_manifest.json is stale: run python scripts/generate_route_coverage.py\n' + '\n'.join(shown)
        )


def test_manifest_statuses_match_what_the_methods_send() -> None:
    calls = sent_by_method()
    assert sorted(calls.silent) == sorted(SENDS_NOTHING_BY_DESIGN), (
        f'public methods that sent no request (give them ARGUMENT_OVERRIDES): {sorted(calls.silent)}'
    )
    public_methods = set(public_method_names())
    routes = load_manifest()
    reached = routes_reached((route.template() for route in routes), calls.sent)

    problems: list[str] = []
    for route in routes:
        if route.status not in STATUSES:
            problems.append(f'{route.verb} {route.path}: unknown status {route.status!r}')
            continue
        reaching = reached.get(route.template(), [])
        if route.status == 'wrapped':
            if route.method not in public_methods:
                problems.append(f'{route.verb} {route.path}: method {route.method!r} does not exist')
            elif route.method not in reaching:
                problems.append(f'{route.verb} {route.path}: {route.method} does not send it')
        elif reaching:
            problems.append(f'{route.verb} {route.path}: status {route.status!r} but sent by {reaching}; regenerate')
    assert not problems, 'tests/route_manifest.json disagrees with the methods:\n' + '\n'.join(problems)
