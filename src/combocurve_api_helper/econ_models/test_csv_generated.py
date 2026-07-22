"""Tests for the generated per-type CSV convenience functions (`_csv_generated.py`)
and the generator that produces them (`scripts/generate_csv_functions.py`).

The convenience functions are thin wrappers over `get_mapper(...)`, so these tests
check three things: the checked-in generated file is in sync with the generator
(freshness), every registered mapper has a matching function pair (coverage), and
each pair actually delegates to the correct mapper on real CC export rows.
"""

import pathlib
import subprocess
import sys
from typing import Dict

import pytest

from combocurve_api_helper import config
from combocurve_api_helper.econ_models import _csv_generated
from combocurve_api_helper.econ_models.registry import MAPPERS, get_mapper
from combocurve_api_helper.econ_models.test_fixtures import (
    _FIXTURE_FILES,
    _FIXTURES_DIR,
    _group_by_model_name,
    _read_csv_rows,
)

# Test file lives at <repo>/src/combocurve_api_helper/econ_models/test_csv_generated.py,
# so the repo root -- which holds scripts/ -- is parents[3].
REPO = pathlib.Path(__file__).resolve().parents[3]
GEN = REPO / 'scripts' / 'generate_csv_functions.py'
OUT = pathlib.Path(__file__).with_name('_csv_generated.py')

_BASE_BY_TYPE: Dict[str, str] = {
    m['econModelType']: m['methodBase'] for m in config.ECON_MODELS if m['methodBase'] is not None
}


def test_generated_file_is_current() -> None:
    fresh = subprocess.run([sys.executable, str(GEN), '--stdout'], capture_output=True, text=True, check=True).stdout
    assert fresh == OUT.read_text(encoding='utf-8'), 'Re-run scripts/generate_csv_functions.py and commit.'


def test_every_mapper_has_both_convenience_functions() -> None:
    for econ_model_type in MAPPERS:
        base = _BASE_BY_TYPE[econ_model_type]
        assert hasattr(_csv_generated, f'{base}_to_csv_rows'), econ_model_type
        assert hasattr(_csv_generated, f'{base}_from_csv_rows'), econ_model_type


def test_all_lists_exactly_two_callables_per_mapper() -> None:
    assert len(_csv_generated.__all__) == 2 * len(MAPPERS)
    for name in _csv_generated.__all__:
        assert name.endswith(('_to_csv_rows', '_from_csv_rows'))
        assert callable(getattr(_csv_generated, name))


@pytest.mark.parametrize('econ_model_type', sorted(_FIXTURE_FILES))
def test_convenience_functions_delegate_to_mapper(econ_model_type: str) -> None:
    base = _BASE_BY_TYPE[econ_model_type]
    to_csv = getattr(_csv_generated, f'{base}_to_csv_rows')
    from_csv = getattr(_csv_generated, f'{base}_from_csv_rows')
    mapper = get_mapper(econ_model_type)

    for filename in _FIXTURE_FILES[econ_model_type]:
        rows = _read_csv_rows(str(pathlib.Path(_FIXTURES_DIR) / filename))
        for model_name, model_rows in _group_by_model_name(rows).items():
            api = from_csv(model_rows)
            assert api == mapper.from_csv_rows(model_rows), f'{econ_model_type} / {filename} / {model_name!r}'
            assert to_csv(api) == mapper.to_csv_rows(api), f'{econ_model_type} / {filename} / {model_name!r}'
