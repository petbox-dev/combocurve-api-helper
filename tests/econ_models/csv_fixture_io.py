"""Shared IO helpers and the fixture registry for the econ-model CSV round-trip tests.

Extracted from ``test_fixtures`` so both ``test_fixtures`` (real-export round trip)
and ``test_csv_generated`` (convenience-function delegation) read the same fixtures
the same way, instead of one test module importing another.
"""

import contextlib
import csv
import os
from collections.abc import Sequence

from combocurve_api_helper.econ_models.base import group_rows_by_model_name

# Directory holding the trimmed real-CC-export fixtures (sits next to this module).
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

# econModelType -> trimmed fixture CSV filename(s) to validate against.
# ProductionTaxes has three: the plain/"custom"-state shape (main examples/ well-scenario
# export), the numbered-severance NM/TX state shape (examples/MoreExamples/), and a raw
# 2026-11-03 export of three models built to show the offset, rate and dates criteria,
# the $/month and $/boe units, and two ad valorem rows. A fourth is one unique model whose
# values are all null, from a 2026-11-03 scenario export (CC writes a null Value as nan).
FIXTURE_FILES: dict[str, list[str]] = {
    # The second is a 2026-11-03 export with CC's "include defaults" option: every yield, shrinkage
    # and loss & flare row is written, a btu row at its 1000 default is not. The mapper's API -> CSV
    # output matched that export on all 41 models of its project.
    # The third (dev project, include defaults) has one btu category at the 1000 default and the
    # other at 1200: only the off-default category gets a row. The fourth is a company-level model:
    # 'Model Type' is 'company' and 'Project Name' is blank.
    'StreamProperties': [
        'stream_properties.csv',
        'stream_properties_with_defaults.csv',
        'stream_properties_btu_one_default.csv',
        'stream_properties_company.csv',
    ],
    'Differentials': ['differentials.csv'],
    'ProductionTaxes': [
        'production_taxes.csv',
        'production_taxes_state.csv',
        'production_taxes_criteria.csv',
        'production_taxes_null_value.csv',
    ],
    'Expenses': ['expenses.csv'],
    'Capex': ['capex.csv'],
    'ReservesCategory': ['reserves_category.csv'],
    'Pricing': ['pricing.csv'],
    'Dates': ['date_settings.csv'],
    'OwnershipReversion': ['ownership_reversion.csv'],
    # Two projects: the first has a model-level `ignoreHistoryProd: true` model ('Ignore History',
    # exported as Never); the second has an empty-phase-node model exported as
    # 'Ignore Historical Production'.
    'ActualOrForecast': ['actual_or_forecast.csv', 'actual_or_forecast_ignore_hist_prod.csv'],
    'Risking': ['risking.csv'],
}


def read_csv_rows(path: str) -> list[dict[str, str]]:
    """Read a fixture CSV into a list of column-name -> value row dicts."""
    with open(path, encoding='utf-8', newline='') as csv_file:
        return list(csv.DictReader(csv_file))


def group_by_model_name(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Group rows by 'Model Name' as a name -> rows dict, preserving first-seen model order.

    A thin dict view over the library's `group_rows_by_model_name` (which returns the groups as
    a list), so the test suite and the shipped `from_csv` share one grouping implementation
    rather than two copies that could drift.
    """
    return {group[0].get('Model Name', ''): group for group in group_rows_by_model_name(rows)}


def project_columns(
    row: dict[str, str], columns: Sequence[str], float_columns: frozenset[str] = frozenset()
) -> dict[str, str]:
    """Restrict a row to `columns` (missing keys default to '') for column-subset comparison.

    A number in one of `float_columns` is normalised to its float form, so CC's '9' and the
    mapper's '9.0' compare equal: the mappers write float columns in float form on purpose, and
    CC's form follows a storage type the API does not expose (see test_float_columns.py).
    """
    projected = {column: row.get(column, '') for column in columns}
    for column in float_columns & set(columns):
        with contextlib.suppress(ValueError):
            projected[column] = repr(float(projected[column]))
    return projected
