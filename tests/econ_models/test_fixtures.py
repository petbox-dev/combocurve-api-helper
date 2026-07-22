"""Ground-truth validation of the forward/inverse direction against REAL ComboCurve
CSV exports (trimmed fixtures under fixtures/).

Unlike the hand-written API->CSV->API tests in the per-type test modules, this
module starts from actual CSV rows CC produced and checks that
`to_row_dicts(from_row_dicts(rows))` reproduces those rows exactly -- the CSV-level
round trip. This is the gate that catches per-type casing/default-value
mismatches that a synthetic API dict would never expose (e.g. CC's CSV renders a
display default such as 'None' or 'nri' for a column even when the underlying API
field is absent).
"""

import os

import pytest

from combocurve_api_helper.econ_models import MAPPERS
from tests.econ_models.csv_fixture_io import (
    FIXTURE_FILES,
    FIXTURES_DIR,
    group_by_model_name,
    project_columns,
    read_csv_rows,
)


def test_registry() -> None:
    assert set(MAPPERS) == {
        'StreamProperties',
        'Differentials',
        'ProductionTaxes',
        'Expenses',
        'Capex',
        'ReservesCategory',
        'Pricing',
        'Dates',
        'OwnershipReversion',
        'ActualOrForecast',
        'Risking',
    }
    for key, mapper in MAPPERS.items():
        assert mapper.econ_model_type == key


@pytest.mark.parametrize('econ_model_type', sorted(FIXTURE_FILES))
def test_csv_round_trip_matches_real_export(econ_model_type: str) -> None:
    mapper = MAPPERS[econ_model_type]
    # Compare only the model-parameter columns: from 'Model Type' through the last
    # type-specific column. Excludes the leading 'Model Id'/'Created At'/'Project Name'
    # (not reconstructable from CSV rows -- from_row_dicts never captures them) and the
    # trailing 'Last Update' (sourced from the API model's updatedAt/context, likewise
    # not reconstructed by from_row_dicts).
    compare_columns = mapper.columns[3:-1]

    for filename in FIXTURE_FILES[econ_model_type]:
        rows = read_csv_rows(os.path.join(FIXTURES_DIR, filename))
        for model_name, model_rows in group_by_model_name(rows).items():
            rebuilt_api = mapper.from_row_dicts(model_rows)
            rebuilt_rows = mapper.to_row_dicts(rebuilt_api)

            expected = [project_columns(row, compare_columns) for row in model_rows]
            actual = [project_columns(row, compare_columns) for row in rebuilt_rows]
            assert actual == expected, f'{econ_model_type} / {filename} / model {model_name!r}'
