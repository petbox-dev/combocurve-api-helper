"""Shared IO helpers and the fixture registry for the econ-model CSV round-trip tests.

Extracted from ``test_fixtures`` so both ``test_fixtures`` (real-export round trip)
and ``test_csv_generated`` (convenience-function delegation) read the same fixtures
the same way, instead of one test module importing another.
"""

import csv
import os
from typing import Dict, List

from combocurve_api_helper.econ_models.base import group_rows_by_model_name

# Directory holding the trimmed real-CC-export fixtures (sits next to this module).
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# econModelType -> trimmed fixture CSV filename(s) to validate against.
# ProductionTaxes has two: the plain/"custom"-state shape (main examples/ well-scenario
# export) and the numbered-severance NM/TX state shape (examples/MoreExamples/).
FIXTURE_FILES: Dict[str, List[str]] = {
    'StreamProperties': ['stream_properties.csv'],
    'Differentials': ['differentials.csv'],
    'ProductionTaxes': ['production_taxes.csv', 'production_taxes_state.csv'],
    'Expenses': ['expenses.csv'],
    'Capex': ['capex.csv'],
    'ReservesCategory': ['reserves_category.csv'],
    'Pricing': ['pricing.csv'],
    'Dates': ['date_settings.csv'],
    'OwnershipReversion': ['ownership_reversion.csv'],
    'ActualOrForecast': ['actual_or_forecast.csv'],
    'Risking': ['risking.csv'],
}


def read_csv_rows(path: str) -> List[Dict[str, str]]:
    """Read a fixture CSV into a list of column-name -> value row dicts."""
    with open(path, 'r', encoding='utf-8', newline='') as csv_file:
        return list(csv.DictReader(csv_file))


def group_by_model_name(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Group rows by 'Model Name' as a name -> rows dict, preserving first-seen model order.

    A thin dict view over the library's `group_rows_by_model_name` (which returns the groups as
    a list), so the test suite and the shipped `from_csv` share one grouping implementation
    rather than two copies that could drift.
    """
    return {group[0].get('Model Name', ''): group for group in group_rows_by_model_name(rows)}


def project_columns(row: Dict[str, str], columns: List[str]) -> Dict[str, str]:
    """Restrict a row to `columns` (missing keys default to '') for column-subset comparison."""
    return {column: row.get(column, '') for column in columns}
