"""The ComboCurve Postman collection, fetched once per test session, and the path normalization the
route tests compare by.

The collection is never vendored. Three tests read it (`test_docstring_slugs.py`,
`test_route_paths.py`, `test_published_routes_are_wrapped.py`); `collection_requests` skips the caller
when it cannot be fetched. The result of the first fetch, a failure included, is kept for the
session, so an offline run waits for one timeout, not one per test.
"""

import http.client
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

import pytest
import requests

# Mirrors scripts/generate_docstrings.py COLLECTION_URL.
COLLECTION_URL = 'https://docs.api.combocurve.com/downloads/combocurve-api.postman_collection.json'

# A 24-hex ObjectId stands in for every required id argument. Nothing is sent, so the value only has
# to be recognizable again in the built or sent url.
PLACEHOLDER = '0' * 24

# Path segments that are a caller-supplied id rather than a literal: the placeholder, and the
# collection's own `:param` spelling.
ID_SEGMENT = re.compile(rf'^(?:{PLACEHOLDER}|:.*)$')


# One collection operation: its item name and its `request` object.
Operation = tuple[str, dict[str, Any]]


@dataclass(frozen=True)
class _CollectionFetch:
    """The outcome of the one fetch: the collection's operations, or why there are none."""

    operations: Optional[list[Operation]]
    unavailable_reason: str


# The session's fetch outcome; None until the first caller asks.
_fetch_outcome: Optional[_CollectionFetch] = None


class MalformedCollection(ValueError):
    """A collection tree entry that is not what a Postman collection holds: an `item` that is not a list,
    an entry that is not an object, or a `request` that is not an object. The same rule as
    `scripts/generate_docstrings.py` `build_examples`, so the route tooling and the docstring generator
    give a malformed collection the same verdict (unavailable), not a usable subset of it."""


def _operations_in(items: object) -> list[Operation]:
    """(item name, request) for every leaf item (an item with a `request`) under `items`; raises
    `MalformedCollection` for a malformed entry."""
    if not isinstance(items, list):
        raise MalformedCollection(f'collection `item` is {type(items).__name__}, expected a list')
    operations: list[Operation] = []
    for item in items:
        if not isinstance(item, dict):
            raise MalformedCollection(f'collection `item` entry is {type(item).__name__}, expected an object')
        if 'item' in item:
            operations.extend(_operations_in(item['item']))
        elif 'request' in item:
            if not isinstance(item['request'], dict):
                raise MalformedCollection(f'operation {item.get("name")!r}: `request` is not an object')
            operations.append((str(item.get('name') or ''), item['request']))
    return operations


def collection_operations(payload: Mapping[str, Any]) -> list[Operation]:
    """(item name, request) for every operation of a collection document; empty when it has no `item` list.
    Raises `MalformedCollection` for a malformed tree."""
    items = payload.get('item')
    return _operations_in(items) if isinstance(items, list) else []


def fetch_collection() -> _CollectionFetch:
    """Fetch the collection and take its operations. A collection with no operation is unavailable,
    not empty: an empty one would fail every route test for a reason that is not theirs. The same
    rule as `scripts/generate_docstrings.py` `CollectionUnavailable`, which also counts `OSError`
    (a broken CA bundle or certificate store raises it, not a `requests` exception). Also the fetch of
    `scripts/generate_route_coverage.py`, which exits 2 when `operations` is None."""
    try:
        response = requests.get(COLLECTION_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, http.client.HTTPException, OSError, ValueError) as error:
        return _CollectionFetch(None, str(error))
    try:
        operations = collection_operations(payload) if isinstance(payload, dict) else []
    except MalformedCollection as error:
        return _CollectionFetch(None, str(error))
    if not operations:
        return _CollectionFetch(None, 'the payload has no `item` tree with an operation in it')
    return _CollectionFetch(operations, '')


def collection_requests() -> list[Operation]:
    """(item name, request) for every operation in the collection. Skips the calling test when the
    collection is unavailable; the first outcome, a failure included, is kept for the session."""
    global _fetch_outcome
    if _fetch_outcome is None:
        _fetch_outcome = fetch_collection()
    if _fetch_outcome.operations is None:
        pytest.skip(f'ComboCurve Postman collection unavailable: {_fetch_outcome.unavailable_reason}')
    return list(_fetch_outcome.operations)  # a copy: a caller cannot change the session cache


def normalized_segments(path_segments: list[str]) -> tuple[str, ...]:
    """Collapse id segments (the placeholder, or the collection's `:name`) to `:p`, so a built url and
    a collection template compare equal."""
    return tuple(':p' if ID_SEGMENT.match(str(segment)) else str(segment) for segment in path_segments)
