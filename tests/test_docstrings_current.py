"""Freshness check: docstring example blocks match the live OpenAPI spec.

Network-dependent (fetches the spec). ``generate_docstrings.py --check`` exits
0 (in sync), 1 (stale -> re-run the generator and commit), or 2 (spec
unreachable -> skipped here so offline runs don't fail).
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
        pytest.skip('OpenAPI spec unreachable (offline)')
    assert result.returncode == 0, (
        'Docstring examples are out of sync with the OpenAPI spec. '
        'Re-run: python scripts/generate_docstrings.py\n' + result.stdout + result.stderr
    )
