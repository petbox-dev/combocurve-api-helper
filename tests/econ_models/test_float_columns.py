"""Float-valued CSV columns are written in float form ('9.0') and read back as `float`.

CC's export writes a number in the form CC stores it ('9' for an integer, '9.0' for a double),
and the API's JSON drops '.0', so the stored form cannot be recovered from API data. The mappers
therefore write every column known to hold a float in float form. Each mapper declares those
columns in `float_columns`; the real-export gate compares them by number.
"""

import os

import pytest

from combocurve_api_helper.econ_models import MAPPERS
from combocurve_api_helper.econ_models.base import Context, model_scope
from tests.econ_models.csv_fixture_io import FIXTURE_FILES, FIXTURES_DIR, group_by_model_name, read_csv_rows

EXPECTED_FLOAT_COLUMNS: dict[str, frozenset[str]] = {
    'ProductionTaxes': frozenset({'Value'}),
    'Differentials': frozenset({'Value'}),
    'Expenses': frozenset({'Value', 'Cap', 'Paying WI / Earning WI'}),
    'StreamProperties': frozenset({'Value'}),
    'Capex': frozenset({'Tangible (M$)', 'Intangible (M$)', 'Paying WI / Earning WI'}),
    'Pricing': frozenset({'Value', 'Cap', 'Price Ratio'}),
    'Risking': frozenset({'Value'}),
    'OwnershipReversion': frozenset(
        {
            'WI %',
            'NRI %',
            'Lease NRI %',
            'NPI %',
            'Oil NRI %',
            'Gas NRI %',
            'NGL NRI %',
            'Drip Cond. NRI %',
            'Reversion Value',
        }
    ),
    'Dates': frozenset({'Discount'}),
    'ReservesCategory': frozenset(),
    'ActualOrForecast': frozenset(),
}


def _is_number(cell: str) -> bool:
    try:
        float(cell)
    except ValueError:
        return False
    return cell != 'nan'


def test_every_mapper_declares_its_float_columns() -> None:
    assert {name: mapper.float_columns for name, mapper in MAPPERS.items()} == EXPECTED_FLOAT_COLUMNS
    for mapper in MAPPERS.values():
        assert mapper.float_columns <= set(mapper.columns), mapper.econ_model_type


@pytest.mark.parametrize('econ_model_type', sorted(FIXTURE_FILES))
def test_float_columns_are_written_in_float_form(econ_model_type: str) -> None:
    mapper = MAPPERS[econ_model_type]
    for filename in FIXTURE_FILES[econ_model_type]:
        rows = read_csv_rows(os.path.join(FIXTURES_DIR, filename))
        for model_name, model_rows in group_by_model_name(rows).items():
            rebuilt = mapper.to_row_dicts(mapper.from_row_dicts(model_rows), Context(scope=model_scope(model_rows)))
            for row in rebuilt:
                for column in mapper.float_columns:
                    cell = row[column]
                    if _is_number(cell):
                        assert '.' in cell, f'{econ_model_type} / {filename} / {model_name!r} / {column}: {cell!r}'


def test_production_taxes_value_reads_back_as_float() -> None:
    mapper = MAPPERS['ProductionTaxes']
    rows = read_csv_rows(os.path.join(FIXTURES_DIR, 'production_taxes_state.csv'))
    for model_rows in group_by_model_name(rows).values():
        for api_row in mapper.from_row_dicts(model_rows)['data']['rows']:
            assert all(isinstance(value, float) for value in api_row['value']), api_row
