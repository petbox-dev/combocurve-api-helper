"""Correctness check: every docstring `https://docs.api.combocurve.com/api/<slug>`
link resolves to a real ComboCurve Postman collection item (the slug source that
`scripts/generate_docstrings.py` maps examples by).

Network-dependent -- skipped when the collection can't be fetched, like
`test_docstrings_current`. Guards against hand-guessed / typo'd slugs, which link
to a 404 doc page and silently get no generated example.
"""

import ast
import pathlib
import re

from tests.postman_collection import collection_requests

_SRC = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'combocurve_api_helper'
_SLUG_RE = re.compile(r'https://docs\.api\.combocurve\.com/api/([a-z0-9-]+(?:/[a-z0-9-]+)*)')
_NEW_ROUTE_EXAMPLE_MARKERS = {
    'delete-forecast-configurations': {'Example response:'},
    'delete-scenario-econ-model-assignments': {'Example data:'},
    'get-econ-report-settings': {'Example response:'},
    'get-econ-report-settings-by-id': {'Example response:'},
    'get-econ-settings': {'Example response:'},
    'get-econ-settings-by-id': {'Example response:'},
    'get-root-forecast-daily-volumes': {'Example response:'},
    'get-root-forecast-monthly-volumes': {'Example response:'},
    'get-scenario-well-incrementals': {'Example response:'},
    'patch-econ-report-settings': {'Example data:', 'Example response:'},
    'patch-econ-settings': {'Example data:', 'Example response:'},
    'patch-project-company-wells': {'Example data:', 'Example response:'},
    'post-econ-report-settings': {'Example data:', 'Example response:'},
    'post-econ-settings': {'Example data:', 'Example response:'},
    'put-econ-report-settings': {'Example data:', 'Example response:'},
    'put-econ-settings': {'Example data:', 'Example response:'},
    'put-forecast-daily-volumes': {'Example data:', 'Example response:'},
    'put-forecast-monthly-volumes': {'Example data:', 'Example response:'},
    'put-scenario-econ-model-assignments': {'Example data:', 'Example response:'},
}


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


def test_new_route_docstrings_keep_every_collection_example() -> None:
    """A generated freshness check cannot detect a removed marker, because there is then nothing to rewrite."""
    source_docs: dict[str, tuple[str, str]] = {}
    for path in sorted(_SRC.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            docstring = ast.get_docstring(node, clean=False) or ''
            slug_match = _SLUG_RE.search(docstring)
            if slug_match and slug_match.group(1) in _NEW_ROUTE_EXAMPLE_MARKERS:
                source_docs[slug_match.group(1)] = (path.name, docstring)

    missing: list[str] = []
    for slug, markers in _NEW_ROUTE_EXAMPLE_MARKERS.items():
        if slug not in source_docs:
            missing.append(f'{slug}: public method docstring not found')
            continue

        filename, docstring = source_docs[slug]
        for marker in markers:
            if marker not in docstring:
                missing.append(f'{filename}: {slug} is missing {marker}')

    assert not missing, 'new route docstrings without their saved collection examples:\n' + '\n'.join(missing)
