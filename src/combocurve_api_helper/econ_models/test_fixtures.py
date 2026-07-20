"""Ground-truth validation of the forward/inverse direction against REAL ComboCurve
CSV exports (trimmed fixtures under fixtures/, sourced from cc-api-scripts/examples).

Unlike the hand-written API->CSV->API tests in the per-type test modules, this
module starts from actual CSV rows CC produced and checks that
`to_csv_rows(from_csv_rows(rows))` reproduces those rows exactly -- the CSV-level
round trip. This is the gate that catches per-type casing/default-value
mismatches that a synthetic API dict would never expose (e.g. CC's CSV renders a
display default such as 'None' or 'nri' for a column even when the underlying API
field is absent).
"""

import csv
import os
from typing import Dict, List

import pytest

from combocurve_api_helper.econ_models import MAPPERS

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# econModelType -> trimmed fixture CSV filename(s) to validate against.
# ProductionTaxes has two: the plain/"custom"-state shape (main examples/ well-scenario
# export) and the numbered-severance NM/TX state shape (examples/MoreExamples/).
_FIXTURE_FILES: Dict[str, List[str]] = {
    'StreamProperties': ['stream_properties.csv'],
    'Differentials': ['differentials.csv'],
    'ProductionTaxes': ['production_taxes.csv', 'production_taxes_state.csv'],
    'Expenses': ['expenses.csv'],
    'Capex': ['capex.csv'],
    'ReservesCategory': ['reserves_category.csv'],
    'Pricing': ['pricing.csv'],
    'DateSettings': ['date_settings.csv'],
    'OwnershipReversion': ['ownership_reversion.csv'],
    'ActualOrForecast': ['actual_or_forecast.csv'],
    'Risking': ['risking.csv'],
}


def _read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, 'r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def _group_by_model_name(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    groups: Dict[str, List[Dict[str, str]]] = {}
    order: List[str] = []
    for row in rows:
        name = row['Model Name']
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(row)
    return {name: groups[name] for name in order}


def _project(row: Dict[str, str], cols: List[str]) -> Dict[str, str]:
    return {c: row.get(c, '') for c in cols}


def test_registry() -> None:
    assert set(MAPPERS) == {
        'StreamProperties',
        'Differentials',
        'ProductionTaxes',
        'Expenses',
        'Capex',
        'ReservesCategory',
        'Pricing',
        'DateSettings',
        'OwnershipReversion',
        'ActualOrForecast',
        'Risking',
    }
    for key, mapper in MAPPERS.items():
        assert mapper.econ_model_type == key


@pytest.mark.parametrize('econ_model_type', sorted(_FIXTURE_FILES))
def test_csv_round_trip_matches_real_export(econ_model_type: str) -> None:
    mapper = MAPPERS[econ_model_type]
    # Compare only the model-parameter columns: from 'Model Type' through the last
    # type-specific column. Excludes the leading 'Model Id'/'Created At'/'Project Name'
    # (not reconstructable from CSV rows -- from_csv_rows never captures them) and the
    # trailing 'Last Update' (sourced from the API model's updatedAt/context, likewise
    # not reconstructed by from_csv_rows).
    compare_cols = mapper.columns[3:-1]

    for filename in _FIXTURE_FILES[econ_model_type]:
        rows = _read_csv_rows(os.path.join(_FIXTURES_DIR, filename))
        for model_name, model_rows in _group_by_model_name(rows).items():
            rebuilt_api = mapper.from_csv_rows(model_rows)
            rebuilt_rows = mapper.to_csv_rows(rebuilt_api)

            expected = [_project(r, compare_cols) for r in model_rows]
            actual = [_project(r, compare_cols) for r in rebuilt_rows]
            assert actual == expected, f'{econ_model_type} / {filename} / model {model_name!r}'
