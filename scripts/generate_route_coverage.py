"""Rewrite tests/route_manifest.json: the status of every ComboCurve Postman collection operation.

Fetches the live collection, records what each public method sends on a fake transport, and writes one
entry per collection operation (see tests/route_manifest.py for the statuses). Hand-set `retired` and
`not-via-method` entries are carried over; a new unreached operation is written as `gap`.

Usage:
    python scripts/generate_route_coverage.py          # rewrite the manifest
    python scripts/generate_route_coverage.py --check  # exit 1 if the committed manifest is stale (no write)
    python scripts/generate_route_coverage.py --collection PATH  # a local collection JSON

Exit codes, as scripts/generate_docstrings.py: 0 the manifest is current (or was written), 1 it is stale
or a method check failed, 2 the live collection could not be obtained in usable form. A bad local
`--collection PATH` raises instead (exit 1), so a typo is not mistaken for "offline".
"""

from __future__ import annotations

import argparse
import http.client
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tests.postman_collection import COLLECTION_URL, Operation  # noqa: E402
from tests.route_manifest import (  # noqa: E402
    ROUTE_MANIFEST_PATH,
    SENDS_NOTHING_BY_DESIGN,
    build_manifest,
    collection_operations,
    load_manifest,
    operations_from_collection,
    render_manifest,
    sent_by_method,
)

# Seconds for the collection fetch (connect and each read). A timeout is a failure to fetch: exit 2.
FETCH_TIMEOUT_SECONDS = 60


class CollectionUnavailable(Exception):
    """The live collection could not be obtained in usable form: a transport failure, or a fetched body
    that is not a collection with operations. Exit 2, "no verdict", never 1 ("stale")."""


def _fetch_collection_operations() -> list[Operation]:
    """The live collection's operations. Every failure to obtain them raises `CollectionUnavailable`."""
    try:
        response = requests.get(COLLECTION_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=FETCH_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, http.client.HTTPException, OSError) as error:
        # RequestException covers connection errors, timeouts and HTTP status errors. OSError covers a
        # broken CA bundle or certificate store; http.client.HTTPException (a truncated read) does not
        # derive from OSError.
        raise CollectionUnavailable(str(error)) from error
    except ValueError as error:
        # A captive-portal or error HTML page.
        raise CollectionUnavailable(f'malformed collection JSON: {error}') from error
    if not isinstance(payload, dict):
        raise CollectionUnavailable(f'collection JSON is {type(payload).__name__}, expected an object')
    operations = collection_operations(payload)
    if not operations:
        # A well-formed object with no operation would make every route look removed.
        raise CollectionUnavailable('the collection has no `item` tree with an operation in it')
    return operations


def _read_local_collection_operations(path: str) -> list[Operation]:
    """A local collection's operations. A missing, malformed or empty file raises (`OSError`,
    `ValueError`): exit 1, not the exit-2 "offline"."""
    payload: Any = json.loads(Path(path).read_text(encoding='utf-8'))
    operations = collection_operations(payload) if isinstance(payload, dict) else []
    if not operations:
        raise ValueError(f'{path} is not a Postman collection with operations')
    return operations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='exit 1 when the committed manifest is stale')
    parser.add_argument('--collection', metavar='PATH', help='read the collection from a local JSON file')
    arguments = parser.parse_args()

    if arguments.collection is not None:
        items = _read_local_collection_operations(arguments.collection)
    else:
        try:
            items = _fetch_collection_operations()
        except CollectionUnavailable as error:
            print(f'could not use the collection ({COLLECTION_URL}): {error}', file=sys.stderr)
            return 2
    operations = operations_from_collection(items)

    previous = load_manifest()
    calls = sent_by_method()
    if sorted(calls.silent) != sorted(SENDS_NOTHING_BY_DESIGN):
        print(
            f'public methods that sent no request (give them ARGUMENT_OVERRIDES): {sorted(calls.silent)}',
            file=sys.stderr,
        )
        return 1

    routes = build_manifest(operations, calls.sent, previous)
    text = render_manifest(routes, COLLECTION_URL)
    counts = Counter(route.status for route in routes)
    print(
        f'{len(routes)} collection operations: ' + ', '.join(f'{status} {counts[status]}' for status in sorted(counts))
    )
    gap_areas = Counter(route.area for route in routes if route.status == 'gap')
    for area, count in gap_areas.most_common():
        print(f'  gap  {count:3d}  {area}')

    current = ROUTE_MANIFEST_PATH.read_text(encoding='utf-8') if ROUTE_MANIFEST_PATH.exists() else ''
    if arguments.check:
        if current != text:
            print(f'{ROUTE_MANIFEST_PATH.relative_to(REPO_ROOT)} is stale: run scripts/generate_route_coverage.py')
            return 1
        print('manifest is current')
        return 0
    if current != text:
        ROUTE_MANIFEST_PATH.write_text(text, encoding='utf-8', newline='\n')
        print(f'wrote {ROUTE_MANIFEST_PATH.relative_to(REPO_ROOT)}')
    else:
        print('manifest unchanged')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
