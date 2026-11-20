"""Rewrite tests/route_manifest.json: the status of every ComboCurve Postman collection operation.

Fetches the live collection, records what each public method sends on a fake transport, and writes one
entry per collection operation (see tests/route_manifest.py for the statuses). Hand-set `retired` and
`not-via-method` entries are carried over; a new unreached operation is written as `gap`.

Usage:
    python scripts/generate_route_coverage.py          # rewrite the manifest
    python scripts/generate_route_coverage.py --check  # exit 1 if the committed manifest is stale (no write)
    python scripts/generate_route_coverage.py --collection PATH  # a local collection JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tests.postman_collection import COLLECTION_URL  # noqa: E402
from tests.route_manifest import (  # noqa: E402
    ROUTE_MANIFEST_PATH,
    SENDS_NOTHING_BY_DESIGN,
    build_manifest,
    load_manifest,
    operations_from_collection,
    render_manifest,
    sent_by_method,
)


def _operation_items(items: list[Any]) -> list[tuple[str, dict[str, Any]]]:
    """(item name, request) for every operation under `items`, at any folder depth."""
    found: list[tuple[str, dict[str, Any]]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get('item'), list):
            found.extend(_operation_items(item['item']))
        elif isinstance(item.get('request'), dict):
            found.append((str(item.get('name') or ''), item['request']))
    return found


def _load_collection(local_path: str | None) -> dict[str, Any]:
    if local_path is not None:
        payload: dict[str, Any] = json.loads(Path(local_path).read_text(encoding='utf-8'))
        return payload
    response = requests.get(COLLECTION_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=120)
    response.raise_for_status()
    fetched: dict[str, Any] = response.json()
    return fetched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='exit 1 when the committed manifest is stale')
    parser.add_argument('--collection', metavar='PATH', help='read the collection from a local JSON file')
    arguments = parser.parse_args()

    payload = _load_collection(arguments.collection)
    items = payload.get('item')
    if not isinstance(items, list):
        print('the collection has no `item` tree', file=sys.stderr)
        return 2
    operations = operations_from_collection(_operation_items(items))
    if not operations:
        print('the collection has no operation', file=sys.stderr)
        return 2

    previous = load_manifest()
    sent, silent = sent_by_method()
    if sorted(silent) != sorted(SENDS_NOTHING_BY_DESIGN):
        print(f'public methods that sent no request (give them ARGUMENT_OVERRIDES): {sorted(silent)}', file=sys.stderr)
        return 1

    routes = build_manifest(operations, sent, previous)
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
