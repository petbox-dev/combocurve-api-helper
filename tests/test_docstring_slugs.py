"""Correctness check: every docstring `https://docs.api.combocurve.com/api/<slug>`
link resolves to a real ComboCurve Postman collection item (the slug source that
`scripts/generate_docstrings.py` maps examples by).

Network-dependent -- skipped when the collection can't be fetched, like
`test_docstrings_current`. Guards against hand-guessed / typo'd slugs, which link
to a 404 doc page and silently get no generated example.
"""

import pathlib
import re

from tests.postman_collection import collection_requests

_SRC = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'combocurve_api_helper'
_SLUG_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+(?:/[a-z0-9-]+)*)')


def _collection_item_names() -> set[str]:
    """The set of collection item names (== the valid docstring slugs)."""
    return {name for name, _ in collection_requests()}


def test_all_docstring_slugs_exist_in_collection() -> None:
    names = _collection_item_names()

    missing: list[str] = []
    for path in sorted(_SRC.glob('*.py')):
        for lineno, line in enumerate(path.read_text(encoding='utf-8').split('\n'), start=1):
            for slug in _SLUG_RE.findall(line):
                if slug not in names:
                    missing.append(f'{path.name}:{lineno} -> {slug}')

    assert not missing, 'docstring /api/<slug> links with no matching collection item:\n' + '\n'.join(missing)
