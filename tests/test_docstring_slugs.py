"""Correctness check: every docstring `https://docs.api.combocurve.com/api/<slug>`
link resolves to a real ComboCurve Postman collection item (the slug source that
`scripts/generate_docstrings.py` maps examples by).

Network-dependent -- skipped when the collection can't be fetched, like
`test_docstrings_current`. Guards against hand-guessed / typo'd slugs, which link
to a 404 doc page and silently get no generated example.
"""

import pathlib
import re
from typing import Any

import pytest
import requests

# Mirrors scripts/generate_docstrings.py COLLECTION_URL (the collection is never vendored).
_COLLECTION_URL = 'https://docs.api.combocurve.com/downloads/combocurve-api.postman_collection.json'
_SRC = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'combocurve_api_helper'
_SLUG_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+)')


def _collection_item_names() -> set[str]:
    """The set of collection item names (== the valid docstring slugs)."""
    response = requests.get(_COLLECTION_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
    response.raise_for_status()
    names: set[str] = set()

    def walk(items: list[dict[str, Any]]) -> None:
        for item in items:
            if 'item' in item:
                walk(item['item'])
            elif 'request' in item:
                names.add(item.get('name') or '')

    walk(response.json().get('item', []))
    return names


def test_all_docstring_slugs_exist_in_collection() -> None:
    try:
        names = _collection_item_names()
    except (requests.RequestException, ValueError) as exc:
        pytest.skip(f'ComboCurve Postman collection unreachable: {exc}')

    missing: list[str] = []
    for path in sorted(_SRC.glob('*.py')):
        for lineno, line in enumerate(path.read_text(encoding='utf-8').split('\n'), start=1):
            for slug in _SLUG_RE.findall(line):
                if slug not in names:
                    missing.append(f'{path.name}:{lineno} -> {slug}')

    assert not missing, 'docstring /api/<slug> links with no matching collection item:\n' + '\n'.join(missing)
