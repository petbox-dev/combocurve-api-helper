"""Freshness check: docstring example blocks match the live Postman collection.

Network-dependent (fetches the collection). ``generate_docstrings.py --check`` exits
0 (in sync), 1 (stale -> re-run the generator and commit), or 2 (no verdict: the
collection is unreachable or no marker matched it -> skipped here so offline runs
don't fail).
"""

import pathlib
import subprocess
import sys

import pytest

GEN = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'generate_docstrings.py'


def test_docstring_examples_match_spec() -> None:
    try:
        result = subprocess.run([sys.executable, str(GEN), '--check'], capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, OSError) as exc:
        pytest.skip(f'could not run docstring freshness check: {exc}')
    if result.returncode == 2:
        pytest.skip('no verdict: Postman collection unreachable (offline) or no marker matched it')
    assert result.returncode == 0, (
        'Docstring examples are out of sync with the Postman collection. '
        'Re-run: python scripts/generate_docstrings.py\n' + result.stdout + result.stderr
    )


@pytest.mark.parametrize(
    'collection_text',
    [
        '{"item": []}',
        # Every operation renamed: the item still yields an (empty) example entry, but no marker matches.
        '{"item": [{"name": "renamed-op", "request": {"method": "GET"}, "response": []}]}',
    ],
    ids=['empty', 'every-operation-renamed'],
)
def test_a_collection_no_marker_matches_gives_no_verdict(tmp_path: pathlib.Path, collection_text: str) -> None:
    """Offline. Every marker would read as "unsourced", so exit 0 would pass having verified nothing."""
    collection = tmp_path / 'collection.json'
    collection.write_text(collection_text, encoding='utf-8')
    result = subprocess.run(
        [sys.executable, str(GEN), '--check', '--collection', str(collection)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 2, result.stdout + result.stderr
